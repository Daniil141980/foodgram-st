from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from foodmanager.models import (Ingredient, User, Recipe,
                                Favorite, RecipeIngredient,
                                Subscription, ShoppingCart)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    class RecipeIngredientInline(admin.TabularInline):
        model = RecipeIngredient
        min_num = 1
        extra = 1

    list_display = ('id', 'name', 'author', 'cooking_time',
                    'favorites_count')
    list_filter = ('author', 'name')
    search_fields = ('name', 'author__username', 'author__email')
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('favorites_count',)

    def favorites_count(self, obj):
        return obj.favorited_by.count()

    favorites_count.short_description = _('Количество добавлений в избранное')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('recipe', 'ingredient')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user__username', 'author__username')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')
