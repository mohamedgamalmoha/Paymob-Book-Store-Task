from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet
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
    lookup_field = 'slug'
    permitted_expands = ['author', 'reviews']
    permit_list_expands = permitted_expands

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_expanded(self.request, 'author'):
            queryset = queryset.select_related('author')
        if is_expanded(self.request, 'reviews'):
            queryset = queryset.prefetch_related('reviews')
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class ReviewViewSet(FlexFieldsMixin, ModelViewSet):
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
    permitted_expands = ['book', 'reviewer']
    permit_list_expands = permitted_expands

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_expanded(self.request, 'book'):
            queryset = queryset.select_related('book')
        if is_expanded(self.request, 'reviewer'):
            queryset = queryset.select_related('reviewer')
        return queryset

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)


class FavoritesViewSet(FlexFieldsMixin, ModelViewSet):
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
    permitted_expands = ['book', 'user']
    permit_list_expands = permitted_expands

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        if is_expanded(self.request, 'book'):
            queryset = queryset.select_related('book')
        if is_expanded(self.request, 'user'):
            queryset = queryset.select_related('user')
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
