from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.IntegerChoices):
    """
    Enum for user roles in the application.
    """
    ADMIN = 1, _("Admin")
    AUTHOR = 2, _("Author")
    REVIEWER = 3, _("Reviewer")
    OTHER = 0, _("Other")
