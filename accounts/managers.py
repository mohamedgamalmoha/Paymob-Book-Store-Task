from django.contrib.auth.models import UserManager
from django.utils.translation import gettext_lazy as _

from accounts.enums import UserRole


class CustomUserManager(UserManager):

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("role") is not UserRole.ADMIN:
            raise ValueError(_("Superuser must has admin role"))

        return super().create_superuser(username, email, password, **extra_fields)


class AuthorUserManager(CustomUserManager):

    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=UserRole.AUTHOR)


class ReviewerUserManager(CustomUserManager):

    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=UserRole.REVIEWER)
