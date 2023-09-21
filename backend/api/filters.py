from app.models import Recipe, Tag

import django_filters

from rest_framework.filters import SearchFilter


class IngredientSearchFilter(SearchFilter):
    """
    Фильтр для поиска ингредиентов по названию.
    """
    search_param = "name"


class RecipeFilter(django_filters.FilterSet):
    """
    Фильтр для рецептов, позволяющий фильтровать
    по избранным, корзине, тегам и автору.
    """

    is_favorited = django_filters.NumberFilter(
        method='favorite_filter',
        label='Избранные',
        help_text='Показать только избранные рецепты (1) или все (0).'
    )

    is_in_shopping_cart = django_filters.NumberFilter(
        method='shopping_cart_filter',
        label='В корзине',
        help_text='Показать только рецепты в корзине (1) или все (0).'
    )

    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
        label='Теги',
        help_text='Фильтр по тегам. Выберите один или несколько тегов.'
    )

    def favorite_filter(self, queryset, name, value):
        """
        Фильтр для избранных рецептов.
        """
        if value == 1:
            user = self.request.user
            return queryset.filter(favourites__user=user.id)
        return queryset

    def shopping_cart_filter(self, queryset, name, value):
        """
        Фильтр для рецептов в корзине.
        """
        if value == 1:
            user = self.request.user
            return queryset.filter(shopping_carts__user=user.id)
        return queryset

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')
