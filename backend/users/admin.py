from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from users.models import User


@register(User)
class UserAdminConfig(UserAdmin):
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    list_display = (
        'pk', 'username', 'email', 'first_name', 'last_name', 'is_staff'
    )
    ordering = ('username',)
