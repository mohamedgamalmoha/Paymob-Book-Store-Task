from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from accounts.models import AuthorUser, ReviewerUser
from books.enums import LanguageChoices, ReasonChoices


User = get_user_model()


class Book(models.Model):
    """
    Represents a book in the library system.
    """
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    slug = models.SlugField(max_length=250, unique=True, verbose_name=_("Slug"))
    author = models.ForeignKey(
        AuthorUser,
        on_delete=models.CASCADE,
        related_name="books",
        verbose_name=_("Author"),
    )
    description = models.TextField(verbose_name=_("Description"))
    content = models.TextField(verbose_name=_("Content"))
    language = models.PositiveSmallIntegerField(
        choices=LanguageChoices.choices,
        verbose_name=_("Language"),
    )
    pages = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_("Number of Pages")
    )
    publication_date = models.DateField(verbose_name=_("Publication Date"))
    publisher = models.CharField(
        max_length=200, blank=True, null=True, verbose_name=_("Publisher")
    )
    cover_image = models.ImageField(
        upload_to="books/covers/",
        blank=True,
        null=True,
        verbose_name=_("Cover Image"),
    )
    file = models.FileField(
        upload_to="books/files/",
        blank=True,
        null=True,
        verbose_name=_("Book File"),
    )
    is_available = models.BooleanField(default=True, verbose_name=_("Is Available"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Book")
        verbose_name_plural = _("Books")
        ordering = ("-created_at", "-updated_at")
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["author"]),
            models.Index(fields=["publication_date"]),
            models.Index(fields=["is_available"]),
        ]

    def __str__(self) -> str:
        """
        Returns a string representation of the book.
        """
        return str(self.title)

    def get_absolute_url(self) -> str:
        """
        Returns the URL for the book detail view.
        """
        return reverse("book:detail", kwargs={"slug": self.slug})


class Review(models.Model):
    """
    Represents a review for a book written by a reviewer.
    """
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="reviews", verbose_name=_("Book")
    )
    reviewer = models.ForeignKey(
        ReviewerUser,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("Reviewer"),
    )
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    content = models.TextField(verbose_name=_("Content"))
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Rating"),
    )
    is_trusted = models.BooleanField(default=False, verbose_name=_("Is Trusted"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")
        ordering = ("-created_at", "-updated_at")
        unique_together = ("book", "reviewer")
        indexes = [
            models.Index(fields=["book"]),
            models.Index(fields=["reviewer"]),
            models.Index(fields=["rating"]),
        ]

    def __str__(self) -> str:
        """
        Returns a string representation of the review.
        """
        return f"{self.book} - {self.reviewer}"


class Favorites(models.Model):
    """
    Represents a user's favorite book with a reason and optional notes.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name=_("User"),
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="favorites", verbose_name=_("Book")
    )
    reason = models.PositiveSmallIntegerField(
        choices=ReasonChoices.choices,
        default=ReasonChoices.OTHER,
        verbose_name=_("Reason for Favoriting"),
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Favorite")
        verbose_name_plural = _("Favorites")
        unique_together = ("user", "book")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["book"]),
        ]

    def __str__(self) -> str:
        """
        Returns a string representation of the favorite.
        """
        return f"{self.book} - {self.user} - {self.reason}"
