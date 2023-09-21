from api.views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
)

from django.urls import include, path

from djoser.views import UserViewSet

from rest_framework import routers


# Создаем роутер для автоматической генерации URL-адресов
router = routers.DefaultRouter()

# Регистрируем представления в роутере
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'users', CustomUserViewSet)
router.register(r'recipes', RecipeViewSet)

# URL-пути для djoser (библиотека аутентификации и управления пользователями)
djoser_urlpatterns = [
    path(
        'users/me/',
        UserViewSet.as_view({'get': 'me'})
    ),  # Получение текущего пользователя
    path(
        'users/set_password/',
        UserViewSet.as_view({'post': 'set_password'})
    ),  # Установка пароля
]

# Общие URL-пути, включая URL-пути djoser и сгенерированные роутером
urlpatterns = [
    path(
        '',
        include(djoser_urlpatterns)
    ),  # Подключение URL-путей из djoser
    path(
        '',
        include(router.urls)
    ),  # Подключение сгенерированных URL-адресов из роутера
    path(
        'auth/',
        include('djoser.urls.authtoken')
    ),  # URL-пути для аутентификации с помощью токена
]
