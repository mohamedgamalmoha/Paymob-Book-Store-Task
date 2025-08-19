from rest_flex_fields import FlexFieldsModelSerializer

from books.models import Book, Review, Favorites


class BookSerializer(FlexFieldsModelSerializer):
    """
    Serializer for the Book model, including expandable fields for author and reviews.
    """

    class Meta:
        model = Book
        exclude = ()
        read_only_fields = ("created_at", "updated_at")
        expandable_fields = {
            "author": ("accounts.api.serializers.UserSerializer", {"many": False}),
            "reviews": ("books.api.serializers.ReviewSerializer", {"many": True}),
        }


class ReviewSerializer(FlexFieldsModelSerializer):
    """
    Serializer for the Review model, including expandable fields for book and reviewer.
    """

    class Meta:
        model = Review
        exclude = ()
        read_only_fields = ("created_at", "updated_at")
        expandable_fields = {
            "book": ("books.api.serializers.BookSerializer", {"many": False}),
            "reviewer": ("accounts.api.serializers.UserSerializer", {"many": False}),
        }


class FavoritesSerializer(FlexFieldsModelSerializer):
    """
    Serializer for the Favorites model, including expandable fields for book and user.
    """

    class Meta:
        model = Favorites
        exclude = ()
        read_only_fields = ("created_at", "updated_at")
        expandable_fields = {
            "book": ("books.api.serializers.BookSerializer", {"many": False}),
            "user": ("accounts.api.serializers.UserSerializer", {"many": False}),
        }
