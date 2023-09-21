from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()  # Получаем модель пользователя


@admin.register(User)
class CustomUser(UserAdmin):
    """Регистрируем модель пользователя с собственным классом администратора"""

    list_display = (
        'pk',  # ID пользователя
        'username',  # Имя пользователя
        'email',  # Электронная почта пользователя (добавленное поле)
        'first_name',  # Имя пользователя
        'last_name',  # Фамилия пользователя
    )
    list_filter = ('email', 'username')  # Фильтры списка пользователей
