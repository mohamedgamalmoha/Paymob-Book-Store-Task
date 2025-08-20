from django.db.models import QuerySet

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import BasePermission, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_flex_fields.utils import is_expanded
from rest_flex_fields.views import FlexFieldsMixin
from rest_flex_fields.filter_backends import FlexFieldsFilterBackend

from accounts.models import User
from accounts.api.permissions import IsOwner
from accounts.api.serializers import UserSerializer


class UserViewSet(FlexFieldsMixin, ModelViewSet):
    """
    UserViewSet is a viewset for managing User objects.
    """
    queryset = User.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsOwner]
    serializer_class = UserSerializer
    filter_backends = [FlexFieldsFilterBackend] + api_settings.DEFAULT_FILTER_BACKENDS
    permitted_expands = ["books", "reviews", "favorites"]
    permit_list_expands = permitted_expands

    def get_permissions(self) -> list[BasePermission]:
        """
        Returns the list of permissions that this view requires.

        If the action is 'create', it allows any user to create a new user.
        Otherwise, it uses the default permissions defined in the class.

        Returns:
            - list[BasePermission]: A list of permission classes that apply to this view.
        """
        if self.action == "create":
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self) -> QuerySet[User]:
        """
        Returns the queryset for the viewset, applying prefetching based on request parameters.

        This method checks if certain fields are expanded in the request and prefetches
        the related fields accordingly. The fields that can be expanded are 'books', 'reviews',
        and 'favorites'.

        Returns:
            - QuerySet: The queryset of User objects, potentially prefetching related fields.
        """
        queryset = super().get_queryset()
        if is_expanded(self.request, "books"):
            queryset = queryset.prefetch_related("books")
        if is_expanded(self.request, "reviews"):
            queryset = queryset.prefetch_related("reviews")
        if is_expanded(self.request, "favorites"):
            queryset = queryset.prefetch_related("favorites")
        return queryset

    def get_current_user(self) -> User:
        """
        Returns the current user from the request.
        """
        return self.request.user

    @action(["GET"], detail=False, url_name="me", url_path="me")
    def me(self, request: Request, *args, **kwargs) -> Response:
        """
        Returns the current user.
        This action is used to retrieve the details of the currently authenticated user.

        Args:
            - request: The HTTP request object.
            - args: Additional positional arguments.
            - kwargs: Additional keyword arguments.

        Returns:
            - Response: A response containing the serialized data of the current user.
        """
        self.get_object = self.get_current_user
        return self.retrieve(request, *args, **kwargs)
