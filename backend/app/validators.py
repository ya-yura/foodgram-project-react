from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import webcolors


def validate_HEX_format(value):
    """
    Проверяет, может ли значение быть
    интерпретировано как шестнадцатеричное значение цвета.
    """
    try:
        # Попробуйте нормализовать значение как шестнадцатеричное
        webcolors.normalize_hex(value)
    except ValueError:
        # Если не удалось нормализовать, вызовите ValidationError
        raise ValidationError(
            _('Цвет должен быть записан в шестнадцатиричном формате HEX!'),
        )
