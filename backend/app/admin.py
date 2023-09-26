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

from django.contrib import admin


class IngredientInRecipeInline(admin.TabularInline):
    """
    Позволяет редактировать модель ингредиентов в рецепте
    на той же странице, что и модель-родитель.
    """
    model = IngredientInRecipe
    extra = 1


class TagForRecipeInline(admin.TabularInline):
    """
    Позволяет редактировать модель тегов в рецепте
    на той же странице, что и модель-родитель.
    """
    model = TagForRecipe
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Панель администратора для модели тегов."""

    list_display = ('id', 'name', 'color', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Панель администратора для модели ингредиентов."""

    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Панель администратора для модели рецептов."""

    list_display = ('author', 'name', 'get_is_favorited')
    list_filter = ('author', 'name', 'tags')
    inlines = (IngredientInRecipeInline, TagForRecipeInline)

    def get_is_favorited(self, obj):
        """Метод подсчитывает количество добавлений рецепта в избранное."""
        return obj.favourites.count()

    get_is_favorited.short_description = 'количество добавлений в избранное'


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    """Панель администратора для модели ингредиентов в рецептах."""

    list_display = ('id', 'recipe', 'ingredient', 'amount')


@admin.register(TagForRecipe)
class TagForRecipeAdmin(admin.ModelAdmin):
    """Панель администратора для модели тегов в рецептах."""

    list_display = ('id', 'recipe', 'tag')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Панель администратора для модели подписок."""

    list_display = ('id', 'user', 'following')


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    """Панель администратора для модели избранного."""

    list_display = ('id', 'user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Панель администратора для модели корзины покупок."""

    list_display = ('id', 'user', 'recipe')
