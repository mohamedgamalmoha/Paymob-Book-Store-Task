from django.db.models import IntegerChoices
from django.utils.translation import gettext_lazy as _


class LanguageChoices(IntegerChoices):
    ENGLISH = 1, _("English")
    SPANISH = 2, _("Spanish")
    FRENCH = 3, _("French")
    GERMAN = 4, _("German")
    ITALIAN = 5, _("Italian")
    PORTUGUESE = 6, _("Portuguese")
    RUSSIAN = 7, _("Russian")
    CHINESE = 8, _("Chinese")
    JAPANESE = 9, _("Japanese")
    ARABIC = 10, _("Arabic")


class ReasonChoices(IntegerChoices):
    RECOMMENDED = 1, _("Recommended")
    READING = 2, _("Reading")
    LISTING = 3, _("Listing")
    INTERESTING = 4, _("Personal Interest")
    PURCHASING = 5, _("Purchasing")
    GIFT = 6, _("Gift")
    COLLECTION = 7, _("Collection")
    OTHER = 0, _("Other")
