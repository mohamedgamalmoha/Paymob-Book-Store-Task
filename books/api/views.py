from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from accounts.api.permissions import IsAuthor, IsReviewer, IsOwner, ReadOnly
from books.models import Book, Review, Favorites
from books.api.filters import BookFilterSet, ReviewFilterSet, FavoritesFilterSet
from books.api.serializers import BookSerializer, ReviewSerializer, FavoritesSerializer


class BookViewSet(ModelViewSet):
    queryset = Book.objects.all()
    authentication_classes = [
        BasicAuthentication,
        SessionAuthentication,
        JWTAuthentication,
    ]
    permission_classes = [ReadOnly | IsAuthor]
    serializer_class = BookSerializer
    filterset_class = BookFilterSet

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class ReviewViewSet(ModelViewSet):
    queryset = Review.objects.all()
    authentication_classes = [
        BasicAuthentication,
        SessionAuthentication,
        JWTAuthentication,
    ]
    permission_classes = [ReadOnly | IsReviewer]
    serializer_class = ReviewSerializer
    filterset_class = ReviewFilterSet

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)


class FavoritesViewSet(ModelViewSet):
    queryset = Favorites.objects.all()
    authentication_classes = [
        BasicAuthentication,
        SessionAuthentication,
        JWTAuthentication,
    ]
    permission_classes = [IsOwner]
    serializer_class = FavoritesSerializer
    filterset_class = FavoritesFilterSet

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
