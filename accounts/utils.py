from django.contrib.auth import get_user_model

from accounts.enums import UserRole


User = get_user_model()


def is_author(user: User) -> bool:
    """
    Check if the user is an author.

    Args:
        - user (User): The user instance to check.

    Returns:
        - bool: `True` if the user has the author role, otherwise `False`.
    """
    return user.role == UserRole.AUTHOR


def is_reviewer(user: User) -> bool:
    """
    Check if the user is a reviewer.

    Args:
        - user (User): The user instance to check.

    Returns:
        - bool: `True` if the user has the reviewer role, otherwise `False`.
    """
    return user.role == UserRole.REVIEWER
