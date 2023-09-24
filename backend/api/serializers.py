from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction

from drf_extra_fields.fields import Base64ImageField

from app.models import (
    Favourite,
    Follow,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
    TagForRecipe,
)

User = get_user_model()


class IngredientKeyedRelatedField(serializers.DictField):
    def to_representation(self, value):
        return {'id': value['id'], 'amount': value['amount']}


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тега."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиента."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """
        Метод, определяющий, подписан ли текущий пользователь
        на другого пользователя.
        """
        return obj.id in self.context['subscriptions']


class CreateUserSerializer(serializers.ModelSerializer):
    """Сериализатор создания пользователя."""
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'password'
        ]
        extra_kwargs = {'password': {'write_only': True}}


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиента в рецепте."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецепта."""

    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_in_recipes',
        many=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        """
        Метод, указывающий, добавлен ли рецепт в избранное.
        """

        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favourite.objects.filter(
            user=request.user,
            recipe=obj,
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Метод, указывающий, добавлен ли рецепт в корзину.
        """

        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user,
            recipe=obj,
        ).exists()

    def get_image(self, obj):
        """Метод для представления изображения."""

        image_path = obj.image.path
        new_path = image_path.replace('/app', '')
        return new_path


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(),
            allow_empty=False
        ),
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        source='tag_set'
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user  # Получаем текущего пользователя из запроса
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tag_set')  # Теперь мы получаем список объектов Tag

        # Создаем рецепт с указанием автора (пользователя)
        recipe = Recipe.objects.create(author=user, **validated_data)

        # Создаем связи с ингредиентами
        for ingredient_data in ingredients_data:
            try:
                ingredient = Ingredient.objects.get(id=ingredient_data['id'])
                amount = ingredient_data['amount']
                IngredientInRecipe.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=amount,
                )
            except Ingredient.DoesNotExist:
                continue

        # Создаем связи с тегами
        for tag in tags:
            recipe.tags.add(tag)  # Добавляем теги к рецепту

        return recipe



class FavouriteAndShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного и корзины."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для управления подписками."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if recipes_limit:
            recipes = Recipe.objects.filter(author=obj)[:int(recipes_limit)]
        serializer = FavouriteAndShoppingCartSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def create(self, validated_data):
        user = self.context['request'].user
        following = validated_data['following']

        if user == following:
            raise serializers.ValidationError(
                "На самого себя подписаться не получится."
            )

        subscription, created = Follow.objects.get_or_create(
            user=user,
            following=following
        )

        if not created:
            raise serializers.ValidationError("Вы уже подписаны.")

        return subscription


class FavouriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favourite
        fields = ('user', 'recipe')


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
