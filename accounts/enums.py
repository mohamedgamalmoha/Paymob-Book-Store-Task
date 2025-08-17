from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.IntegerChoices):
    ADMIN = 1, _("Admin")
    AUTHER = 2, _("Author")
    REVIEWER = 3, _("Reviewer")
    OTHER = 0, _("Other")
