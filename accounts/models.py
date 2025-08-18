from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from accounts.enums import UserRole
from accounts.managers import CustomUserManager, AuthorUserManager, ReviewerUserManager


class User(AbstractUser):
    base_role = UserRole.OTHER

    role = models.PositiveSmallIntegerField(
        choices=UserRole.choices, verbose_name=_("Role")
    )

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ("date_joined",)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.role = self.base_role
        return super().save(*args, **kwargs)


class AuthorUser(User):
    base_role = UserRole.AUTHOR

    objects = AuthorUserManager()

    class Meta:
        proxy = True


class ReviewerUser(User):
    base_role = UserRole.REVIEWER

    objects = ReviewerUserManager()

    class Meta:
        proxy = True
