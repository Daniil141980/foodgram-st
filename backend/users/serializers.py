import base64
import uuid

from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import User


class Base64Format(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format_data, base64_data = data.split(';base64,')
            extension = format_data.split('/')[-1]
            filename = f"{uuid.uuid4()}.{extension}"
            decoded_file = base64.b64decode(base64_data)
            data = ContentFile(decoded_file, name=filename)

        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64Format(use_url=True, allow_null=True)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user.subscriptions.filter(id=obj.id).exists()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )


class CreateUserSerializer(UserSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {"password": {"write_only": True}}


class SetAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64Format(use_url=True)

    def validate(self, attrs):
        avatar = self.initial_data.get("avatar")
        if not avatar:
            raise serializers.ValidationError("Нельзя загрузить пустой аватар")

        return attrs

    class Meta:
        model = User
        fields = ('avatar',)


class UserCreateResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name')


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
