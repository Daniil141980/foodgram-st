from recipes.serializers import RecipeMinifiedSerializer
from rest_framework import serializers
from users.models import User


class UserWithRecipesSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return request.user.subscriptions.filter(id=obj.id).exists()

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = None

        if request and request.query_params.get("recipes_limit"):
            limit_param = request.query_params.get("recipes_limit")
            if limit_param.isdigit():
                limit = int(limit_param)

        queryset = obj.recipes.all()
        if limit:
            queryset = queryset[:limit]

        return RecipeMinifiedSerializer(
            queryset,
            many=True,
            context={"request": request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
            "recipes",
            "recipes_count"
        )
