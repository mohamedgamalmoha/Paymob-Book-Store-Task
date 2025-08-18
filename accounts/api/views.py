from rest_framework.decorators import action
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_flex_fields.utils import is_expanded
from rest_flex_fields.views import FlexFieldsMixin
from rest_flex_fields.filter_backends import FlexFieldsFilterBackend

from accounts.models import User
from accounts.enums import UserRole
from accounts.api.permissions import IsOwner
from accounts.api.serializers import UserSerializer


class UserViewSet(FlexFieldsMixin, ModelViewSet):
    queryset = User.objects.all()
    authentication_classes = [
        BasicAuthentication,
        SessionAuthentication,
        JWTAuthentication,
    ]
    permission_classes = [IsOwner]
    serializer_class = UserSerializer
    filter_backends = [FlexFieldsFilterBackend] + api_settings.DEFAULT_FILTER_BACKENDS
    permitted_expands = ['books', 'reviews', 'favorites']
    permit_list_expands = permitted_expands

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_expanded(self.request, 'books'):
            queryset = queryset.prefetch_related('books')
        if is_expanded(self.request, 'reviews'):
            queryset = queryset.prefetch_related('reviews')
        if is_expanded(self.request, 'favorites'):
            queryset = queryset.prefetch_related('favorites')
        return queryset

    def get_current_user(self):
        return self.request.user

    def perform_create(self, serializer):
        serializer.save(role=UserRole.REVIEWER)

    @action(["GET"], detail=False, url_name='me', url_path='me')
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_current_user
        return self.retrieve(request,*args, **kwargs)
