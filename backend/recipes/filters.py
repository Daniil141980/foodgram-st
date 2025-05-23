from django_filters import rest_framework as filters

from .models import Recipe, Ingredient


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name="name",
        lookup_expr="istartswith"
    )

    class Meta:
        model = Ingredient
        fields = ("name",)


class RecipeFilter(filters.FilterSet):
    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(method='filter_is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user

        if value not in (0, 1):
            return queryset

        if not user.is_authenticated:
            return queryset.none() if value == 1 else queryset

        if value == 1:
            return queryset.filter(favorites__user=user)

        return queryset.exclude(favorites__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user

        if value not in (0, 1):
            return queryset

        if not user.is_authenticated:
            return queryset.none() if value == 1 else queryset

        if value == 1:
            return queryset.filter(shopping_cart__user=user)

        return queryset.exclude(shopping_cart__user=user)

    class Meta:
        model = Recipe
        fields = (
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )
