from django.contrib.auth import get_user_model

from rest_framework.permissions import BasePermission

from books.models import Book, Review, Favorites
from accounts.utils import is_author, is_reviewer


User = get_user_model()


class IsAuthor(BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            is_author(request.user)
        )


class IsReviewer(BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            is_reviewer(request.user)
        )


class IsOwner(BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, User):
            return request.user == obj
        if isinstance(obj, Book):
            return request.user == obj.author
        if isinstance(obj, Review):
            return request.user == obj.reviewer
        if isinstance(obj, Favorites):
            return request.user == obj.user
        return False
