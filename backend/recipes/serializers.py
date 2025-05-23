from rest_framework import serializers
from users.serializers import UserSerializer, Base64Format

from .models import (
    Recipe,
    RecipeIngredient,
    Ingredient
)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class IngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    measurement_unit = serializers.CharField()

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source="recipe_ingredients",
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.shopping_cart.filter(user=request.user).exists()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )


class IngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f"Ингредиента с id {value} не существует."
            )
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Количество ингредиента должно быть больше 0"
            )
        return value

    class Meta:
        model = Ingredient
        fields = ("id", "amount")


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientCreateSerializer(many=True)
    image = Base64Format(required=True, allow_null=False)

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Время приготовления должно быть положительным числом"
            )
        return value

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance, context={"request": self.context.get("request")}
        )
        return serializer.data

    def validate(self, attrs):
        ingredients = attrs.get("ingredients")
        cooking_time = attrs.get("cooking_time")

        if not ingredients:
            raise serializers.ValidationError(
                "Список ингредиентов не может быть пустым"
            )

        ingredient_ids = [item["id"] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингредиенты должны быть уникальными"
            )

        if cooking_time and cooking_time < 1:
            raise serializers.ValidationError(
                "Время приготовления должно быть не меньше 1 минуты"
            )

        return attrs

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        author = self.context.get("request").user

        recipe = Recipe.objects.create(author=author, **validated_data)
        self._create_recipe_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        if "ingredients" in validated_data:
            ingredients_data = validated_data.pop("ingredients")
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self._create_recipe_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    @staticmethod
    def _create_recipe_ingredients(recipe, ingredients_data):
        recipe_ingredients = []

        for item in ingredients_data:
            ingredient = Ingredient.objects.get(id=item["id"])
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=item["amount"]
                )
            )

        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
