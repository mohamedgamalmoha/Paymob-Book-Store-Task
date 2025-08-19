from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from books.models import Book, Review, Favorites


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """
    Admin interface for managing books.
    """
    list_display = ("title", "author", "is_available", "created_at", "updated_at")
    fieldsets = (
        (_("Main info"), {"fields": ("title", "slug",  "author", "is_available")}),
        (_("Detail"), {"fields": ("description", "content", "language", "pages", "publication_date", "publisher")}),
        (_("Files"), {"fields": ("cover_image", "file")}),
        (_("Important dates"), {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")
    search_fields = ("title", "description", "content")
    list_filter = ("is_available", "language")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for managing book reviews.
    """
    list_display = ("book", "reviewer", "title", "rating", "is_trusted", "created_at", "updated_at")
    fieldsets = (
        (_("Main info"), {"fields": ("book", "reviewer", "title", "content")}),
        (_("Rating"), {"fields": ("rating", "is_trusted")}),
        (_("Important dates"), {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")
    search_fields = ("title", "content")
    list_filter = ("rating", "is_trusted")


@admin.register(Favorites)
class FavoritesAdmin(admin.ModelAdmin):
    """
    Admin interface for managing user favorites.
    """
    list_display = ("user", "book", "reason", "created_at", "updated_at")
    fieldsets = (
        (_("Main info"), {"fields": ("user", "book", "reason", "notes")}),
        (_("Important dates"), {"fields": ( "created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")
    search_fields = ("notes", )
    list_filter = ("reason",)
