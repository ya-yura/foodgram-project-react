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
        request = self.context.get('request')
        user = request.user

        if user.is_anonymous:
            return False

        user_favorites = Favourite.objects.filter(
            user=user
        ).prefetch_related(
            'recipe'
        )

        return obj in [favorite.recipe for favorite in user_favorites]

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = request.user

        if user.is_anonymous:
            return False

        user_cart = ShoppingCart.objects.filter(
            user=user
        ).prefetch_related(
            'recipe'
        )

        return obj in [cart.recipe for cart in user_cart]

    def get_image(self, obj):
        """Метод для представления изображения."""

        image_path = obj.image.path
        new_path = image_path.replace('/app', '')
        return new_path


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientKeyedRelatedField(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
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

    def create_ingredient(self, ingredients, recipe):
        ingredient_list = []
        for obj in ingredients:
            ingredient, amount = obj
            ingredient_list.append(
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=amount,
                )
            )
        IngredientInRecipe.objects.bulk_create(ingredient_list)

    def create_tag(self, tags, recipe):
        tag_objects = [TagForRecipe(recipe=recipe, tag=tag) for tag in tags]
        TagForRecipe.objects.bulk_create(tag_objects)

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(author=user, **validated_data)
        self.create_ingredient(ingredients, recipe)
        self.create_tag(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.clear()
            self.create_tag(tags, instance)
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredient(ingredients, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(instance, context=self.context)
        return serializer.data


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

    def validate_following(self, following):
        user = self.context['request'].user

        if user == following:
            raise serializers.ValidationError(
                "Вы не можете подписаться на самого себя."
            )

        return following

    def create(self, validated_data):
        following = validated_data['following']
        user = self.context['request'].user

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
