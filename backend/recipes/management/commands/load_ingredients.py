import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из JSON-файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            help='Путь к JSON-файлу с данными ингредиентов',
            default=None
        )

    def handle(self, *args, **options):
        custom_path = options.get('path')

        if custom_path:
            json_path = Path(custom_path)
        else:
            json_path = Path(__file__).parent.parent.parent.parent.parent / 'data' / 'ingredients.json'
            json_path = json_path.resolve()

        if not json_path.exists():
            self.stderr.write(self.style.ERROR(
                f'Файл не найден: {json_path}'
            ))
            return

        try:
            with open(json_path, encoding='utf-8') as f:
                ingredients_data = json.load(f)

            if not isinstance(ingredients_data, list):
                self.stderr.write(self.style.ERROR(
                    'Некорректный формат данных: ожидается список ингредиентов'
                ))
                return

            with transaction.atomic():
                created_count = 0
                updated_count = 0

                for item in ingredients_data:
                    if not isinstance(item, dict) or 'name' not in item or 'measurement_unit' not in item:
                        self.stderr.write(self.style.WARNING(
                            f'Пропуск некорректных данных ингредиента: {item}'
                        ))
                        continue

                    obj, created = Ingredient.objects.update_or_create(
                        name=item['name'],
                        measurement_unit=item['measurement_unit']
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

            self.stdout.write(self.style.SUCCESS(
                f'Успешно обработано {len(ingredients_data)} ингредиентов: '
                f'{created_count} создано, {updated_count} обновлено.'
            ))

        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR(
                'Некорректный формат JSON в файле ингредиентов'
            ))
        except Exception as e:
            self.stderr.write(self.style.ERROR(
                f'Ошибка при загрузке ингредиентов: {e}'
            ))
