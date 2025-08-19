from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from accounts.enums import UserRole
from accounts.managers import CustomUserManager, AuthorUserManager, ReviewerUserManager


class User(AbstractUser):
    """
    Custom User model that extends Django's AbstractUser.
    """
    base_role = UserRole.OTHER

    role = models.PositiveSmallIntegerField(
        choices=UserRole.choices, verbose_name=_("Role")
    )

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ("date_joined",)

    def save(self, *args, **kwargs) -> None:
        """
        Override save method to set the base role if not already set.

        Args:
            - args: Positional arguments.
            - kwargs: Keyword arguments.
        """
        if not self.pk:
            self.role = self.base_role
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        """
        Returns the string representation of the User.
        """
        ful_name = self.get_full_name()
        return ful_name if ful_name else self.username


class AuthorUser(User):
    """
    Proxy model for Author users, extending the base User model.
    """
    base_role = UserRole.AUTHOR

    objects = AuthorUserManager()

    class Meta:
        proxy = True


class ReviewerUser(User):
    """
    Proxy model for Reviewer users, extending the base User model.
    """
    base_role = UserRole.REVIEWER

    objects = ReviewerUserManager()

    class Meta:
        proxy = True
