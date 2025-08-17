from django.urls import path, include

from rest_framework import routers

from books.api.views import BookViewSet, ReviewViewSet, FavoritesViewSet


app_name = 'books'

router = routers.DefaultRouter()
router.register(r'books', BookViewSet, basename='books')
router.register(r'reviews', ReviewViewSet, basename='reviews')
router.register(r'favorites', FavoritesViewSet, basename='favorites')

urlpatterns = [
    path('', include(router.urls), name='books_routes'),
]
