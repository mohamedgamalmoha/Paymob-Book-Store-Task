from django.db import transaction
from django.core import exceptions as django_exceptions
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from rest_flex_fields import FlexFieldsModelSerializer

from accounts.enums import UserRole
from accounts.models import User


RESTRICTED_ROLE_CHOICES = [
    (UserRole.AUTHOR.value, UserRole.AUTHOR.label),
    (UserRole.REVIEWER.value, UserRole.REVIEWER.label),
]


class UserSerializer(FlexFieldsModelSerializer):
    """
    Serializer for User model, handling user creation and updates.
    """
    role = serializers.ChoiceField(
        choices=RESTRICTED_ROLE_CHOICES,
        default=UserRole.REVIEWER,
    )

    class Meta:
        model = User
        exclude = ("is_superuser", "is_staff", "groups", "user_permissions")
        read_only_fields = ("is_active", "last_login", "date_joined")
        extra_kwargs = {"password": {"write_only": True}}
        expandable_fields = {
            "books": ("books.api.serializers.BooksSerializer", {"many": True}),
            "reviews": ("books.api.serializers.ReviewSerializer", {"many": True}),
            "favorites": ("books.api.serializers.FavoritesSerializer", {"many": True}),
        }

    def validate(self, data: dict) -> dict:
        """
        Validates the provided data for creating or updating a User instance.

        Args:
            - data (dict): The data to validate.

        Returns:
            - dict: The validated data.

        Raises:
            - serializers.ValidationError: If the password validation fails.
        """
        user = User(**data)
        password = data.get("password")

        try:
            validate_password(password, user)
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError({"password": e})

        return data

    @transaction.atomic
    def create(self, validated_data: dict) -> User:
        """
        Creates a new User instance with the provided validated data.

        Args:
            - validated_data (dict): The validated data for creating a User.

        Returns:
            - User: The created User instance.

        Raises:
            - serializers.ValidationError: If the password validation fails.
        """
        return User.objects.create_user(**validated_data)

    @transaction.atomic
    def update(self, instance: User, validated_data: dict) -> User:
        """
        Updates an existing User instance with the provided validated data.

        Args:
            - instance (User): The User instance to update.
            - validated_data (dict): The validated data for updating the User.

        Returns:
            - User: The updated User instance.
        """
        validated_data.pop('role', None)
        return super().update(instance, validated_data)
