from io import BytesIO

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from foodmanager.models import (Ingredient, Recipe, Favorite,
                                RecipeIngredient, Subscription, ShoppingCart)
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .serializers import (IngredientSerializer, UserCreateSerializer,
                          UserSerializer, PasswordSerializer,
                          RecipeCreateUpdateSerializer, RecipeSerializer,
                          RecipeMinSerializer, UserWithRecipesSerializer,
                          SetAvatarSerializer, RecipeShortLinkSerializer,
                          SubscriptionSerializer)

User = get_user_model()

PDF_FONT = 'Arial'
PDF_FONT_PATH = 'Arial.ttf'
PDF_TITLE = 'Список покупок'
PDF_FILENAME = 'shopping_list.pdf'
PDF_TITLE_FONT_SIZE = 14
PDF_TEXT_FONT_SIZE = 12
PDF_START_Y = 750
PDF_BOTTOM_MARGIN = 50
PDF_LINE_HEIGHT = 25
PDF_FIRST_PAGE_Y = 800
PDF_PAGE_WIDTH, PDF_PAGE_HEIGHT = A4


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name']
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')

        if name:
            queryset = queryset.filter(name__istartswith=name)

        return queryset.order_by('name')


class LimitPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
                request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        return (
                obj.author == request.user
                or request.user.is_staff
        )


def generate_shopping_cart_pdf(ingredients):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    pdfmetrics.registerFont(TTFont(PDF_FONT, PDF_FONT_PATH))
    pdf.setFont(PDF_FONT, PDF_TITLE_FONT_SIZE)
    pdf.drawString(30, PDF_FIRST_PAGE_Y, PDF_TITLE)

    pdf.setFont(PDF_FONT, PDF_TEXT_FONT_SIZE)
    y_position = PDF_START_Y

    for i, item in enumerate(ingredients, 1):
        line = (
            f"{i}. {item['ingredient__name']} - "
            f"{item['total']} {item['ingredient__measurement_unit']}"
        )
        pdf.drawString(30, y_position, line)
        y_position -= PDF_LINE_HEIGHT

        if y_position <= PDF_BOTTOM_MARGIN:
            pdf.showPage()
            pdf.setFont(PDF_FONT, PDF_TEXT_FONT_SIZE)
            y_position = PDF_FIRST_PAGE_Y

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitPageNumberPagination
    permission_classes = [IsAuthorOrAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update', 'update'):
            return RecipeCreateUpdateSerializer
        if self.action == 'get_link':
            return RecipeShortLinkSerializer
        return RecipeSerializer

    def get_queryset(self):
        queryset = Recipe.objects.all()

        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author__id=author)

        if self.request.user.is_authenticated:
            is_favorited = self.request.query_params.get('is_favorited')
            if is_favorited == '1':
                queryset = queryset.filter(
                    favorited_by__user=self.request.user
                )

            is_in_shopping_cart = self.request.query_params.get(
                'is_in_shopping_cart'
            )
            if is_in_shopping_cart == '1':
                queryset = queryset.filter(
                    in_shopping_cart__user=self.request.user
                )

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[permissions.AllowAny],
        url_path='get-link',
        url_name='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        serializer = RecipeShortLinkSerializer(
            recipe, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()

        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(
                user=request.user, recipe=recipe
            )

            if not created:
                return Response(
                    {'errors': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = RecipeMinSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            deleted, _ = request.user.favorites.filter(recipe=recipe).delete()

            if not deleted:
                return Response(
                    {'errors': 'Рецепта нет в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()

        if request.method == 'POST':
            cart_item, created = ShoppingCart.objects.get_or_create(
                user=request.user, recipe=recipe
            )

            if not created:
                return Response(
                    {'errors': 'Рецепт уже в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = RecipeMinSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            deleted, _ = request.user.shopping_cart.filter(recipe=recipe).delete()

            if not deleted:
                return Response(
                    {'errors': 'Рецепта нет в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(
                {'errors': 'Ваш список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        recipes = Recipe.objects.filter(in_shopping_cart__user=user)

        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__in=recipes)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total=Sum('amount'))
        )

        buffer = generate_shopping_cart_pdf(ingredients)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=PDF_FILENAME,
            content_type='application/pdf'
        )


def recipe_short_link(request, slug_short):
    recipe = get_object_or_404(Recipe, slug__startswith=slug_short)
    return redirect('api:recipes-detail', pk=recipe.id)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitPageNumberPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create' or self.action == 'retrieve' or self.action == 'list':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        serializer = UserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def set_password(self, request):
        serializer = PasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['current_password']):
            return Response(
                {'current_password': ['Неверный пароль.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar'
    )
    def me_avatar(self, request):
        if request.method == 'DELETE':
            request.user.avatar = None
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = SetAvatarSerializer(
            instance=request.user,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'avatar': request.user.avatar.url},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        authors = User.objects.filter(subscribers__user=request.user)
        paginated_queryset = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            paginated_queryset,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={'user': request.user.id, 'author': author.id}
            )
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=request.user, author=author)

            response_serializer = UserWithRecipesSerializer(
                author,
                context={'request': request}
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            deleted, _ = request.user.subscriptions.filter(author=author).delete()

            if not deleted:
                return Response(
                    {'errors': 'Вы не были подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
