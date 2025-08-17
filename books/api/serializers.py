from rest_framework import serializers
from books.models import Book, Review, Favorites


class BookSerializer(serializers.ModelSerializer):

    class Meta:
        model = Book
        exclude = ()
        read_only_fields = ('created_at', 'updated_at')


class ReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        exclude = ()
        read_only_fields = ('created_at', 'updated_at')


class FavoritesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorites
        exclude = ()
        read_only_fields = ('created_at', 'updated_at')
