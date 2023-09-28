# Молю о пощаде! :)
# У меня дедлайн был в прошлую пятницу.
# Я очень благодарен тебе за конструктивные улучшения и методы оптимизации.
# Это правда очень круто и мне очень нравится твой наставнический подход
# и отношение за всё время учёбы и сейчас особенно!
# Но я могу не успеть сдать, если мы будем пилить так поэтапно до идеала. :)
# Прошу, давай до пнд попробуем закрыть проект?
# У меня, если честно, уже жим-жим немношк от приближения критической даты.

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.http import Http404

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientSearchFilter, RecipeFilter
from api.mixins import ListRetrieveCreateViewSet
from api.pagination import LimitPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    CreateRecipeSerializer,
    CreateUserSerializer,
    FollowSerializer,
    IngredientSerializer,
    RecipeSerializer,
    TagSerializer,
    UserSerializer,
    FavouriteSerializer,
    ShoppingCartSerializer,
)

from app.models import (
    Favourite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
    Follow,
)

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    """ViewSet для тега."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)


class IngredientViewSet(ReadOnlyModelViewSet):
    """ViewSet для ингредиента."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class CustomUserViewSet(ListRetrieveCreateViewSet):
    """ViewSet для пользователя."""

    queryset = User.objects.all()
    pagination_class = LimitPageNumberPagination
    permission_classes = (permissions.AllowAny,)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        return UserSerializer

    @action(
        detail=False,
        url_path='subscriptions',
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = User.objects.filter(following__user=user)
        page = self.paginate_queryset(subscriptions)
        serializer = FollowSerializer(
            page,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(data=serializer.data)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscribe(self, request, pk):
        following = get_object_or_404(User, pk=pk)

        if request.user == following:
            return Response(
                data={"error": "На себя подписываться нет смысла."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        subscription, created = Follow.objects.get_or_create(
            user=user,
            following=following
        )

        if not created:
            return Response(
                data={"error": "Вы уже подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            data={"message": "Вы успешно подписались!"},
            status=status.HTTP_201_CREATED,
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk):
        following = get_object_or_404(User, pk=pk)

        if request.user == following:
            return Response(
                data={"error": "От себя не отписаться!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        Follow.objects.filter(user=user, following=following).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(ModelViewSet):
    """ViewSet для рецепта."""

    queryset = Recipe.objects.all()
    pagination_class = LimitPageNumberPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return CreateRecipeSerializer
        return RecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            context['subscriptions'] = set(
                Follow.objects.filter(user=self.request.user).values_list(
                    'following_id',
                    flat=True
                )
            )
        return context

    @action(
        methods=('post', 'delete'),
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def add_to_favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if Favourite.objects.filter(user=user, recipe=recipe).exists():
            favourite = Favourite.objects.get(user=user, recipe=recipe)
            favourite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = FavouriteSerializer(
            data={
                'user': user.id,
                'recipe': recipe.id
            }
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            data=serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @add_to_favorite.mapping.delete
    def remove_from_favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if not Favourite.objects.filter(user=user, recipe=recipe).exists():
            raise Http404

        favourite = get_object_or_404(Favourite, user=user, recipe=recipe)
        favourite.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def add_to_shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                data={'errors': 'Рецепт уже добавлен в корзину.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        shopping_cart = ShoppingCart(user=user, recipe=recipe)
        shopping_cart.save()

        serializer = ShoppingCartSerializer(shopping_cart)
        return Response(
            data=serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        shopping_cart = get_object_or_404(
            ShoppingCart,
            user=user,
            recipe=recipe
        )
        shopping_cart.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        url_path='download_shopping_cart',
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        user = request.user

        if not user.shopping_carts.exists():
            return Response(
                data={'errors': 'Корзина пуста.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        ingredients = Ingredient.objects.filter(
            ingredient_in_recipes__recipe__shopping_carts__user=user,
        ).values(
            'name',
            'measurement_unit',
        ).annotate(
            amount=Sum('ingredient_in_recipes__amount'),
        )

        shopping_cart = [''.join(
            f'{ingredient["name"]} '
            f'({ingredient["measurement_unit"]}) - '
            f'{ingredient["amount"]}\n'
        ) for ingredient in ingredients]

        return HttpResponse(shopping_cart, content_type='text/plain')
