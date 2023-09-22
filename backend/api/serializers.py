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

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from drf_extra_fields.fields import Base64ImageField

from rest_framework import serializers

User = get_user_model()


# Сериализатор для связи с ингредиентом и его количеством в рецепте
class IngredientKeyedRelatedField(serializers.PrimaryKeyRelatedField):
    """
    Поле, обрабатывающее идентификатор ингредиента и его количество в рецепте.
    """
    def get_queryset(self):
        return Ingredient.objects.all()

    def to_internal_value(self, data):
        try:
            ingredient = self.get_queryset().get(id=data['id'])
            amount = data['amount']
            return (ingredient, amount)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data['id'])
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data['id']).__name__)

    def to_representation(self, value):
        ingredient, amount = value
        return {'id': ingredient.id, 'amount': amount}


# Сериализатор для тега
class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тега."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


# Сериализатор для ингредиента
class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиента."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


# Сериализатор для создания пользователя
# class CreateUserSerializer(serializers.ModelSerializer):
#     """Сериализатор для создания пользователя."""

#     class Meta:
#         model = User
#         fields = (
#             'email',
#             'id',
#             'username',
#             'first_name',
#             'last_name',
#             'password',
#         )
#         read_only_fields = ('id',)
#         extra_kwargs = {'password': {'write_only': True}}

#     def create(self, validated_data):
#         user = User(**validated_data)
#         user.set_password(validated_data['password'])
#         user.save()
#         return user


# Сериализатор для пользователя
class UserSerializer(serializers.ModelSerializer):
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
        request = self.context.get('request')
        user = request.user
        return Follow.objects.filter(
            user=user.id, following=obj
        ).exists()


class UserCreateSerializer(serializers.ModelSerializer):
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


# Сериализатор для ингредиента в рецепте
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


# Сериализатор для рецепта
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


# Сериализатор для создания рецепта
class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""

    ingredients = IngredientKeyedRelatedField(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
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
        """Метод для создания ингредиента."""

        for obj in ingredients:
            ingredient, amount = obj
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount,
            )

    def create_tag(self, tags, recipe):
        """Метод для создания тега."""

        for pk in tags:
            TagForRecipe.objects.create(recipe=recipe, tag=pk)

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
        request = self.context.get('request')
        serializer = RecipeSerializer(instance, context={'request': request})
        return serializer.data


# Сериализатор для избранного и корзины
class FavouriteAndShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного и корзины."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


# Сериализатор для управления подписками
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
        """
        Метод для сериализации рецептов пользователя
        с возможностью указания ограничения на количество объектов.
        """

        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if recipes_limit:
            recipes = Recipe.objects.filter(author=obj)[:int(recipes_limit)]
        serializer = FavouriteAndShoppingCartSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        """Метод для подсчета количества рецептов пользователя."""

        return Recipe.objects.filter(author=obj).count()
