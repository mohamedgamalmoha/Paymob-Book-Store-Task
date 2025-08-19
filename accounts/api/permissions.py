from django.db.models import Model
from django.contrib.auth import get_user_model

from rest_framework.views import View
from rest_framework.request import Request
from rest_framework.permissions import BasePermission, SAFE_METHODS

from books.models import Book, Review, Favorites
from accounts.utils import is_author, is_reviewer


User = get_user_model()


class IsAuthor(BasePermission):
    """
    Custom permission to only allow authors to edit their own books.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """
        Check if the user is authenticated and is an author.

        Args:
            - request (Request): The request object.
            - view (View): The view being accessed.

        Returns:
            - bool: True if the user is authenticated and is an author, False otherwise.
        """
        return bool(
            request.user and request.user.is_authenticated and is_author(request.user)
        )


class IsReviewer(BasePermission):
    """
    Custom permission to only allow reviewers to access certain views.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """
        Check if the user is authenticated and is a reviewer.

        Args:
            - request (Request): The request object.
            - view (View): The view being accessed.

        Returns:
            - bool: True if the user is authenticated and is a reviewer, False otherwise.
        """
        return bool(
            request.user and request.user.is_authenticated and is_reviewer(request.user)
        )


class IsOwner(BasePermission):
    """
    Custom permission to only allow users to edit their own objects.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """
        Check if the user is authenticated.

        Args:
            - request (Request): The request object.
            - view (View): The view being accessed.

        Returns:
            - bool: True if the user is authenticated, False otherwise.
        """
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: View, obj: Model) -> bool:
        """
        Check if the user is the owner of the object.

        Args:
            - request (Request): The request object.
            - view (View): The view being accessed.
            - obj (Model): The object being accessed.

        Returns:
            - bool: True if the user is the owner of the object, False otherwise.
        """
        if isinstance(obj, User):
            return request.user == obj
        if isinstance(obj, Book):
            return request.user == obj.author
        if isinstance(obj, Review):
            return request.user == obj.reviewer
        if isinstance(obj, Favorites):
            return request.user == obj.user
        return False


class ReadOnly(BasePermission):
    """
    Custom permission to allow read-only access to authenticated users.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """
        Check if the request method is safe (GET, HEAD, OPTIONS) and the user is authenticated.

        Args:
            - request (Request): The request object.
            - view (View): The view being accessed.

        Returns:
            - bool: True if the request method is safe and the user is authenticated, False otherwise
        """
        return bool(
            request.method in SAFE_METHODS
            and request.user
            and request.user.is_authenticated
        )
