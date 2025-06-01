import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from foodmanager.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR.parent, 'data', 'ingredients.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            ingredients_data = json.load(f)
        ingredients_to_create = []
        for item in ingredients_data:
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')
            ingredients_to_create.append(
                Ingredient(name=name, measurement_unit=measurement_unit)
            )
        Ingredient.objects.bulk_create(ingredients_to_create)
