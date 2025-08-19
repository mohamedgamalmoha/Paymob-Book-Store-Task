from django.db.models import QuerySet

from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet
from rest_framework.serializers import BaseSerializer
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_flex_fields.utils import is_expanded
from rest_flex_fields.views import FlexFieldsMixin
from rest_flex_fields.filter_backends import FlexFieldsFilterBackend
from rest_framework_simplejwt.authentication import JWTAuthentication

from accounts.api.permissions import IsAuthor, IsReviewer, IsOwner, ReadOnly
from books.models import Book, Review, Favorites
from books.api.filters import BookFilterSet, ReviewFilterSet, FavoritesFilterSet
from books.api.serializers import BookSerializer, ReviewSerializer, FavoritesSerializer


class BookViewSet(FlexFieldsMixin, ModelViewSet):
    """
    A viewset for viewing and editing book instances.
    """
    queryset = Book.objects.all()
    authentication_classes = [
        BasicAuthentication,
        SessionAuthentication,
        JWTAuthentication,
    ]
    permission_classes = [ReadOnly | IsAuthor]
    serializer_class = BookSerializer
    filter_backends = [FlexFieldsFilterBackend] + api_settings.DEFAULT_FILTER_BACKENDS
    filterset_class = BookFilterSet
    lookup_field = "slug"
    permitted_expands = ["author", "reviews"]
    permit_list_expands = permitted_expands

    def get_queryset(self) -> QuerySet[Book]:
        """
        Returns a queryset of Book objects, optionally expanded based on request parameters.

        If the request has the 'author' parameter expanded, it will use select_related to fetch
        the related author objects in a single query.

        Returns:
            - QuerySet[Book]: A queryset of Book objects, potentially with related author and reviews pre-fetched.
        """
        queryset = super().get_queryset()
        if is_expanded(self.request, "author"):
            queryset = queryset.select_related("author")
        if is_expanded(self.request, "reviews"):
            queryset = queryset.prefetch_related("reviews")
        return queryset

    def perform_create(self, serializer: BaseSerializer) -> None:
        """
        Saves the book instance with the current user as the author.

        Args:
            - serializer (BaseSerializer): The serializer instance containing the book data.
        """
        serializer.save(author=self.request.user)


class ReviewViewSet(FlexFieldsMixin, ModelViewSet):
    """
    A viewset for viewing and editing review instances.
    """
    queryset = Review.objects.all()
    authentication_classes = [
        BasicAuthentication,
        SessionAuthentication,
        JWTAuthentication,
    ]
    permission_classes = [ReadOnly | IsReviewer]
    serializer_class = ReviewSerializer
    filter_backends = [FlexFieldsFilterBackend] + api_settings.DEFAULT_FILTER_BACKENDS
    filterset_class = ReviewFilterSet
    permitted_expands = ["book", "reviewer"]
    permit_list_expands = permitted_expands

    def get_queryset(self) -> QuerySet[Review]:
        """
        Returns a queryset of Review objects, optionally expanded based on request parameters.

        If the request has the 'book' parameter expanded, it will use select_related to fetch
        the related book objects in a single query. If the 'reviewer' parameter is expanded,
        it will also fetch the related reviewer objects.

        Returns:
            - QuerySet[Review]: A queryset of Review objects, potentially with related book and reviewer pre-fetched.
        """
        queryset = super().get_queryset()
        if is_expanded(self.request, "book"):
            queryset = queryset.select_related("book")
        if is_expanded(self.request, "reviewer"):
            queryset = queryset.select_related("reviewer")
        return queryset

    def perform_create(self, serializer: BaseSerializer) -> None:
        """
        Saves the review instance with the current user as the reviewer.

        Args:
            - serializer (BaseSerializer): The serializer instance containing the review data.
        """
        serializer.save(reviewer=self.request.user)


class FavoritesViewSet(FlexFieldsMixin, ModelViewSet):
    """
    A viewset for managing user favorites.
    """
    queryset = Favorites.objects.all()
    authentication_classes = [
        BasicAuthentication,
        SessionAuthentication,
        JWTAuthentication,
    ]
    permission_classes = [IsOwner]
    serializer_class = FavoritesSerializer
    filterset_class = FavoritesFilterSet
    filter_backends = [FlexFieldsFilterBackend] + api_settings.DEFAULT_FILTER_BACKENDS
    permitted_expands = ["book", "user"]
    permit_list_expands = permitted_expands

    def get_queryset(self) -> QuerySet[Favorites]:
        """
        Returns a queryset of Favorites objects filtered by the current user.

        If the request has the 'book' parameter expanded, it will use select_related to fetch
        the related book objects in a single query. If the 'user' parameter is expanded,
        it will also fetch the related user objects.

        Returns:
            - QuerySet[Favorites]: A queryset of Favorites objects filtered by the current user,
              potentially with related book and user pre-fetched.
        """
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        if is_expanded(self.request, "book"):
            queryset = queryset.select_related("book")
        if is_expanded(self.request, "user"):
            queryset = queryset.select_related("user")
        return queryset

    def perform_create(self, serializer: BaseSerializer) -> None:
        """
        Saves the favorites instance with the current user as the owner.

        Args:
            - serializer (BaseSerializer): The serializer instance containing the favorites data.
        """
        serializer.save(user=self.request.user)
