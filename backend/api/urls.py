from django.urls import include, path
from recipes.views import RecipeViewSet, IngredientViewSet
from rest_framework import routers

from .views import UserViewSet, AvatarUpdateView

router = routers.DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("recipes", RecipeViewSet, basename="recipes")
router.register("ingredients", IngredientViewSet, basename="ingredients")
app_name = "api"

urlpatterns = [
    path('users/me/avatar/', AvatarUpdateView.as_view(), name='avatar-update'),

    path("", include(router.urls)),

    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
