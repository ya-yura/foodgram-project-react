import csv

from app.models import Ingredient

from django.core.management import BaseCommand

from foodgram.settings import LOAD_DATA_DIR


class Command(BaseCommand):
    """Команда для загрузки ингредиентов в базу данных из файла CSV."""

    def handle(self, *args, **options):
        """
        Обработчик команды.

        Использование команды:
        python manage.py load_ingredients

        Эта команда загружает ингредиенты
        из файла ingredients.csv в базу данных.
        Файл ingredients.csv должен находиться в директории,
        указанной в настройках (LOAD_DATA_DIR).

        Пример содержимого файла ingredients.csv:
        "Молоко","мл"
        "Сахар","г"
        "Мука","г"
        ...

        Каждая строка файла содержит имя ингредиента и его единицу измерения,
        разделенные запятой. Первая колонка - имя ингредиента,
        вторая колонка - единица измерения.

        После успешного выполнения команды, все ингредиенты
        будут добавлены в базу данных.
        """
        # Открываем CSV-файл для чтения
        with open(
            f'{LOAD_DATA_DIR}/ingredients.csv',
            encoding='utf-8',
        ) as csvfile:
            reader = csv.reader(csvfile)
            # Создаем временный список с объектами Ingredient
            temp_data = [Ingredient(
                name=row[0],  # Имя ингредиента из первой колонки CSV
                measurement_unit=row[1],  # Единица измерения
            ) for row in reader]
            # Массово добавляем ингредиенты в базу данных
            Ingredient.objects.bulk_create(temp_data)
            # Выводим сообщение об успешной загрузке
            self.stdout.write(self.style.SUCCESS(
                'Ингредиенты были загружены в базу данных!')
            )
