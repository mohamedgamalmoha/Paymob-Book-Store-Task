from django.db import models

from django_filters import rest_framework as filters

from books.models import Book, Review, Favorites


class BookFilterSet(filters.FilterSet):
    search = filters.CharFilter(method='custom_search', label="Search by name, description")

    def custom_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(description__icontains=value) |
            models.Q(content__icontains=value)
        )

    class Meta:
        model = Book
        fields = ('search', 'title', 'author', 'description', 'content', 'language',
                  'pages', 'publication_date', 'publisher', 'is_available')


class ReviewFilterSet(filters.FilterSet):

    class Meta:
        model = Review
        fields = ('book', 'reviewer', 'title', 'content', 'rating', 'is_trusted')


class FavoritesFilterSet(filters.FilterSet):

    class Meta:
        model = Favorites
        fields = ('user', 'book', 'reason', 'notes')
