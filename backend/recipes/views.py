from api.pagination import DefaultPagination
from api.permissions import IsAuthorOrReadOnly
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    SAFE_METHODS,
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .models import Recipe, Ingredient
from .serializers import (
    RecipeCreateSerializer,
    RecipeSerializer,
    RecipeMinifiedSerializer,
    IngredientSerializer,
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ("^name",)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').all()
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=("get",),
        permission_classes=(IsAuthenticatedOrReadOnly,),
        url_path="get-link",
        url_name="get-link",
    )
    def generate_share_url(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = f"{request.get_host()}/recipes/{recipe.id}"
        return Response(
            {"short-link": short_link},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart'
    )
    def get_shopping_cart(self, request):
        recipes_in_cart = Recipe.objects.filter(shopping_cart__user=request.user)
        page = self.paginate_queryset(recipes_in_cart)

        serializer = RecipeMinifiedSerializer(
            page or recipes_in_cart,
            many=True,
            context={'request': request}
        )

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        ingredient_totals = {}

        recipes = Recipe.objects.filter(shopping_cart__user=request.user)

        for recipe in recipes:
            for recipe_ingredient in recipe.recipe_ingredients.all():
                ingredient = recipe_ingredient.ingredient
                key = (ingredient.name, ingredient.measurement_unit)

                current_amount = ingredient_totals.get(key, 0)
                ingredient_totals[key] = current_amount + recipe_ingredient.amount

        shopping_list = []
        for (name, unit), amount in sorted(ingredient_totals.items()):
            shopping_list.append(f"{name} ({unit}) — {amount}\n")

        content = "".join(shopping_list)
        return Response(content, content_type='text/plain')

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
    )
    def modify_shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self._add_to_shopping_cart(request, pk)
        return self._remove_from_shopping_cart(request, pk)

    def _add_to_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if recipe.shopping_cart.filter(user=user).exists():
            return Response(
                {'errors': 'Рецепт уже в корзине'},
                status=status.HTTP_400_BAD_REQUEST
            )

        recipe.shopping_cart.create(user=user)

        serializer = RecipeMinifiedSerializer(
            recipe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        cart_item = recipe.shopping_cart.filter(user=user)
        if not cart_item.exists():
            return Response(
                {'errors': 'Рецепта нет в корзине'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='favorite'
    )
    def get_favorites(self, request):
        favorite_recipes = Recipe.objects.filter(favorites__user=request.user)
        page = self.paginate_queryset(favorite_recipes)

        serializer = RecipeMinifiedSerializer(
            page or favorite_recipes,
            many=True,
            context={'request': request}
        )

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', "delete"],
        permission_classes=[IsAuthenticated],
        url_path='favorite'
    )
    def modify_favorite(self, request, pk=None):
        if request.method == 'POST':
            return self._add_to_favorites(request, pk)
        return self._remove_from_favorites(request, pk)

    def _add_to_favorites(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        if recipe.favorites.filter(user=request.user).exists():
            return Response(
                {'errors': 'Рецепт уже в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )

        recipe.favorites.create(user=request.user)

        serializer = RecipeMinifiedSerializer(
            recipe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_favorites(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        favorite = recipe.favorites.filter(user=request.user)
        if not favorite.exists():
            return Response(
                {'errors': 'Рецепта нет в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
