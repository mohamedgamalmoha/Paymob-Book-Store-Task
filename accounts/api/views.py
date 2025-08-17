from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BasicAuthentication

from accounts.models import User
from accounts.enums import UserRole
from accounts.api.permissions import IsOwner
from accounts.api.serializers import UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsOwner]
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    def get_current_user(self):
        return self.request.user

    def perform_create(self, serializer):
        serializer.save(role=UserRole.REVIEWER)

    @action(["GET"], detail=False, url_name='me', url_path='me')
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_current_user
        return self.retrieve(request,*args, **kwargs)
