from django.db import models
from django.db.models import QuerySet
from django_filters import rest_framework as filters

from books.models import Book, Review, Favorites


class BookFilterSet(filters.FilterSet):
    """
    FilterSet for Book model to allow filtering by various fields.
    """
    search = filters.CharFilter(
        method="custom_search", label="Search by name, description"
    )

    def custom_search(self, queryset: QuerySet[Book], name: str, value: str) -> QuerySet[Book]:
        """
        Custom search method to filter books by title, description, or content.

        Args:
            - queryset (QuerySet[Book]): The initial queryset of books.
            - name (str): The name of the filter field.
            - value (str): The search term to filter by.

        Returns:
            - QuerySet[Book]: Filtered queryset containing books that match the search term.
        """
        return queryset.filter(
            models.Q(title__icontains=value)
            | models.Q(description__icontains=value)
            | models.Q(content__icontains=value)
        )

    class Meta:
        model = Book
        fields = (
            "search",
            "title",
            "author",
            "description",
            "content",
            "language",
            "pages",
            "publication_date",
            "publisher",
            "is_available",
        )


class ReviewFilterSet(filters.FilterSet):
    """
    FilterSet for Review model to allow filtering by various fields.
    """

    class Meta:
        model = Review
        fields = ("book", "reviewer", "title", "content", "rating", "is_trusted")


class FavoritesFilterSet(filters.FilterSet):
    """
    FilterSet for Favorites model to allow filtering by user and book.
    """

    class Meta:
        model = Favorites
        fields = ("user", "book", "reason", "notes")
