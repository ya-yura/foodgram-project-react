from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Модель пользователя"""

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    first_name = models.CharField(_('first name'), max_length=50)
    last_name = models.CharField(_('last name'), max_length=50)
    email = models.EmailField(_('email address'), max_length=100, unique=True)
    password = models.CharField(_('password'), max_length=128)

    groups = models.ManyToManyField(
        to='auth.Group',
        related_name='custom_users',
        blank=True,
        verbose_name=_('groups'),
    )
    user_permissions = models.ManyToManyField(
        to='auth.Permission',
        related_name='custom_users',
        blank=True,
        verbose_name=_('user permissions'),
    )

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ('id',)

    def __str__(self):
        return self.username
