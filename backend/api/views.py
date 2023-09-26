from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

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
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscribe(self, request, pk):
        following = get_object_or_404(User, pk=pk)
        self.check_object_permissions(request, following)

        try:
            subscription = Follow.objects.get(
                user=request.user,
                following=following
            )
            if request.method == 'POST':
                # Уже подписан, отписываемся
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                # Уже подписан, ничего не делаем
                return Response(status=status.HTTP_200_OK)
        except Follow.DoesNotExist:
            if request.method == 'POST':
                # Не подписан, подписываемся
                serializer = FollowSerializer(
                    data={'following': following.id},
                    context={'request': request}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(
                    data=serializer.data,
                    status=status.HTTP_201_CREATED
                )
            else:
                # Не подписан, ничего не делаем
                return Response(status=status.HTTP_200_OK)


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
        methods=['post'],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def add_to_favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        # Проверяем, существует ли объект в избранном
        if Favourite.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                data={'errors': 'Рецепт уже добавлен в избранное.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        favourite = Favourite(user=user, recipe=recipe)
        favourite.save()

        serializer = FavouriteSerializer(favourite)
        return Response(
            data=serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @add_to_favorite.mapping.delete
    def remove_from_favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        # Проверяем, существует ли объект в избранном
        if not Favourite.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                data={'errors': 'Рецепт не находится в избранном.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        favourite = Favourite.objects.get(user=user, recipe=recipe)
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

        # Проверяем, существует ли объект в корзине
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

        # Проверяем, существует ли объект в корзине
        if not ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                data={'errors': 'Рецепт не находится в корзине.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        shopping_cart = ShoppingCart.objects.get(user=user, recipe=recipe)
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
