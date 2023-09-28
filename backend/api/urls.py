from rest_framework import routers
from django.urls import include, path

from djoser.views import UserViewSet

from api.views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
)


router = routers.DefaultRouter()

router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'users', CustomUserViewSet, basename='user')
router.register(r'recipes', RecipeViewSet, basename='recipe')

djoser_urlpatterns = [
    path(
        'users/me/',
        UserViewSet.as_view({'get': 'me'})
    ),
    path(
        'users/set_password/',
        UserViewSet.as_view({'post': 'set_password'})
    ),
]

urlpatterns = [
    path(
        '',
        include(djoser_urlpatterns)
    ),
    path(
        '',
        include(router.urls)
    ),
    path(
        'auth/',
        include('djoser.urls.authtoken')
    ),
]
