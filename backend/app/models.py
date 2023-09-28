from app.validators import validate_HEX_format

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('название тега'),
    )
    color = models.CharField(
        max_length=7,
        verbose_name=_('цвет'),
        validators=(validate_HEX_format,),
    )
    slug = models.SlugField(
        max_length=200,
        verbose_name=_('уникальный идентификатор'),
        validators=(
            RegexValidator(
                regex='^[-a-zA-Z0-9_]+$',
                message=_('slug может содержать только буквы латинского '
                          'алфавита, цифры и символы подчеркивания'),
            ),
        ),
    )

    class Meta:
        verbose_name = _('тег')
        verbose_name_plural = _('теги')
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'color', 'slug'),
                name='unique_tag',
            ),
        )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        max_length=200,
        verbose_name=_('название ингредиента'),
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name=_('единица измерения'),
    )

    class Meta:
        verbose_name = _('ингредиент')
        verbose_name_plural = _('ингредиенты')
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient',
            ),
        )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name=_('автор рецепта'),
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_('название рецепта'),
    )
    image = models.ImageField(
        upload_to='images/',
        verbose_name=_('изображение'),
    )
    text = models.TextField(verbose_name=_('описание рецепта'))
    ingredients = models.ManyToManyField(
        to=Ingredient,
        related_name='recipes',
        through='IngredientInRecipe',
        verbose_name=_('ингредиенты'),
    )
    tags = models.ManyToManyField(
        to=Tag,
        related_name='recipes',
        through='TagForRecipe',
        verbose_name=_('теги'),
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name=_('время приготовления'),
        validators=(
            MinValueValidator(
                limit_value=1,
                message=_('минимальное время приготовления - 1 минута'),
            ),
        ),
    )

    class Meta:
        verbose_name = _('рецепт')
        verbose_name_plural = _('рецепты')
        ordering = ('name',)

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Модель ингредиента в рецепте."""

    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipes',
        verbose_name=_('рецепт'),
    )
    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipes',
        verbose_name=_('ингредиент'),
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name=_('количество ингредиента в рецепте'),
        validators=(
            MinValueValidator(
                limit_value=1,
                message=_('минимальное количество - 1'),
            ),
        ),
    )

    class Meta:
        verbose_name = _('ингредиент в рецепте')
        verbose_name_plural = _('ингредиенты в рецепте')
        ordering = ('recipe',)
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredient_in_recipe',
            ),
        )

    def __str__(self):
        return f'{self.recipe} содержит {self.ingredient}'


class TagForRecipe(models.Model):
    """Модель тега в рецепте."""

    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='tag_in_recipes',
        verbose_name=_('рецепт'),
    )
    tag = models.ForeignKey(
        to=Tag,
        on_delete=models.CASCADE,
        related_name='tag_in_recipes',
        verbose_name=_('тег'),
    )

    class Meta:
        verbose_name = _('тег в рецепте')
        verbose_name_plural = _('теги в рецепте')
        ordering = ('recipe',)
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'tag'),
                name='unique_tag_in_recipe',
            ),
        )

    def __str__(self):
        return f'{self.recipe} - {self.tag}'


class Follow(models.Model):
    """Модель подписки."""

    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name=_('пользователь'),
    )
    following = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name=_('подписка на пользователя'),
    )

    class Meta:
        verbose_name = _('подписка')
        verbose_name_plural = _('подписки')
        ordering = ('user',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'following'),
                name='unique_follow',
            ),
        )

    def __str__(self):
        return f'{self.user} подписан на {self.following}'


class Favourite(models.Model):
    """Модель избранного."""

    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='favourites',
        verbose_name=_('пользователь'),
    )
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='favourites',
        verbose_name=_('рецепт'),
    )

    class Meta:
        verbose_name = _('избранное')
        verbose_name_plural = _('избранные')
        ordering = ('user',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favourite',
            ),
        )

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное'


class ShoppingCart(models.Model):
    """Модель корзины покупок."""

    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name=_('пользователь'),
    )
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name=_('рецепт'),
    )

    class Meta:
        verbose_name = _('корзина покупок')
        verbose_name_plural = _('корзины покупок')
        ordering = ('user',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart',
            ),
        )

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в корзину'
