from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField(
        verbose_name="Электронная почта",
        max_length=255,
        unique=True,
    )
    username = models.CharField(
        verbose_name="Имя пользователя",
        max_length=50,
        unique=True,
        db_index=True,
        validators=[RegexValidator(regex=r'^[\w.@+-]+\Z')],
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=50,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=50,
    )
    avatar = models.ImageField(
        verbose_name="Аватар пользователя",
        upload_to='users/avatars/',
        blank=True,
    )

    subscriptions = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='subscribers',
        blank=True,
        verbose_name='Подписки'
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self):
        return self.username
