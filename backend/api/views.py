from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated, AllowAny)
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User
from users.serializers import (
    UserSerializer,
    CreateUserSerializer,
    SetAvatarSerializer,
    SetPasswordSerializer,
)

from .pagination import DefaultPagination
from .serializers import UserWithRecipesSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CreateUserSerializer
    permission_classes = (AllowAny,)
    pagination_class = DefaultPagination

    def get_serializer_class(self):
        actions_map = {
            'list': UserSerializer,
            'retrieve': UserSerializer,
            'me': UserSerializer,
        }
        return actions_map.get(self.action, super().get_serializer_class())

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def me(self, request):
        serializer = self.get_serializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password'
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        if not user.check_password(serializer.validated_data['current_password']):
            return Response(
                {'current_password': ['Неверный текущий пароль']},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        user_subscriptions = request.user.subscriptions.all()
        paginated_queryset = self.paginate_queryset(user_subscriptions)

        serializer = UserWithRecipesSerializer(
            paginated_queryset,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        url_path="subscribe",
        url_name='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        if request.method == "POST":
            return self._add_subscription(request, pk)
        return self._remove_subscription(request, pk)

    def _add_subscription(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)

        if user == author:
            return Response(
                {"errors": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.subscriptions.filter(pk=author.pk).exists():
            return Response(
                {"errors": "Вы уже подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.subscriptions.add(author)

        serializer = UserWithRecipesSerializer(
            author,
            context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_subscription(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)

        if not request.user.subscriptions.filter(pk=author.pk).exists():
            return Response(
                {'detail': 'Вы не подписаны на данного пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.subscriptions.remove(author)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AvatarUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = SetAvatarSerializer(
            instance=request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        return self.put(request)

    def delete(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save(update_fields=['avatar'])
        return Response(status=status.HTTP_204_NO_CONTENT)
