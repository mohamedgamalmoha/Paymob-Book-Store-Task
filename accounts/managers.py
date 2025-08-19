from django.db.models import QuerySet
from django.contrib.auth.models import UserManager
from django.utils.translation import gettext_lazy as _

from accounts.enums import UserRole


class CustomUserManager(UserManager):
    """
    Custom user manager for handling user creation and management.
    """

    def create_superuser(self, username: str, email: str = None, password: str = None, **extra_fields) -> "User":
        """
        Create and return a superuser with the given username, email, and password.

        Args:
            - username (str): The username for the superuser.
            - email (str, optional): The email for the superuser.
            - password (str, optional): The password for the superuser.
            - extra_fields (dict): Additional fields for the superuser.

        Returns:
            - User: The created superuser instance.

        Raises:
            - ValueError: If the role is not set to admin.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("role") is not UserRole.ADMIN:
            raise ValueError(_("Superuser must has admin role"))

        return super().create_superuser(username, email, password, **extra_fields)


class AuthorUserManager(CustomUserManager):
    """
    Custom user manager for handling Author users.
    """

    def get_queryset(self, *args, **kwargs) -> QuerySet["User"]:
        """
        Get the queryset of Author users.

        Args:
            - args: Positional arguments.
            - kwargs: Keyword arguments.

        Returns:
            - QuerySet: Filtered queryset containing only Author users.
        """
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=UserRole.AUTHOR)


class ReviewerUserManager(CustomUserManager):
    """
    Custom user manager for handling Reviewer users.
    """

    def get_queryset(self, *args, **kwargs) -> QuerySet["User"]:
        """
        Get the queryset of Reviewer users.

        Args:
            - args: Positional arguments.
            - kwargs: Keyword arguments.

        Returns:
            - QuerySet: Filtered queryset containing only Reviewer users.
        """
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=UserRole.REVIEWER)
