import time
from datetime import timedelta
from unittest.mock import Mock

from django.urls import reverse

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.enums import UserRole
from accounts.models import User
from accounts.api.permissions import IsOwner
from accounts.api.serializers import UserSerializer
from accounts.api.views import UserViewSet


class UserViewSetTestCase(APITestCase):
    """Test cases for UserViewSet"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )

        # Create JWT tokens
        self.token1 = RefreshToken.for_user(self.user1).access_token
        self.token2 = RefreshToken.for_user(self.user2).access_token

        # URLs
        self.list_url = reverse('accounts:users-list')
        self.detail_url = lambda pk: reverse('accounts:users-detail', kwargs={'pk': pk})
        self.me_url = reverse('accounts:users-me')

    def authenticate_user(self, user_token):
        """Helper method to authenticate a user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')

    def test_viewset_attributes(self):
        """Test viewset class attributes"""
        viewset = UserViewSet()

        self.assertEqual(viewset.queryset.model, User)
        self.assertEqual(viewset.serializer_class, UserSerializer)
        self.assertEqual(viewset.permission_classes, [IsOwner])
        self.assertEqual(viewset.permitted_expands, ["books", "reviews", "favorites"])
        self.assertEqual(viewset.permit_list_expands, ["books", "reviews", "favorites"])


class TestGetPermissions(APITestCase):
    """Test get_permissions method"""

    def setUp(self):
        self.viewset = UserViewSet()

    def test_get_permissions_create_action(self):
        """Test that create action allows any user"""
        self.viewset.action = 'create'
        permissions = self.viewset.get_permissions()

        self.assertEqual(len(permissions), 1)
        self.assertIsInstance(permissions[0], AllowAny)

    def test_get_permissions_other_actions(self):
        """Test that other actions use default permissions"""
        actions = ['list', 'retrieve', 'update', 'destroy', 'me']

        for action in actions:
            with self.subTest(action=action):
                self.viewset.action = action
                permissions = self.viewset.get_permissions()

                # Should return default permissions (IsOwner)
                self.assertEqual(len(permissions), 1)
                self.assertIsInstance(permissions[0], IsOwner)


class TestGetCurrentUser(APITestCase):
    """Test get_current_user method"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.viewset = UserViewSet()
        self.viewset.request = Mock()
        self.viewset.request.user = self.user

    def test_get_current_user(self):
        """Test get_current_user returns request.user"""
        result = self.viewset.get_current_user()
        self.assertEqual(result, self.user)


class TestMeAction(APITestCase):
    """Test the 'me' action"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.client = APIClient()
        self.token = RefreshToken.for_user(self.user).access_token
        self.me_url = reverse('accounts:users-me')

    def test_me_action_authenticated(self):
        """Test me action with authenticated user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user.id)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['email'], self.user.email)

    def test_me_action_unauthenticated(self):
        """Test me action without authentication"""
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_action_method_not_allowed(self):
        """Test me action with unsupported HTTP methods"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Test POST, PUT, PATCH, DELETE
        unsupported_methods = [
            self.client.post,
            self.client.put,
            self.client.patch,
            self.client.delete
        ]

        for method in unsupported_methods:
            with self.subTest(method=method.__name__):
                response = method(self.me_url)
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class TestCRUDOperations(APITestCase):
    """Test CRUD operations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )
        self.client = APIClient()
        self.token = RefreshToken.for_user(self.user).access_token
        self.other_token = RefreshToken.for_user(self.other_user).access_token
        self.list_url = reverse('accounts:users-list')

    def test_create_user_unauthenticated(self):
        """Test creating a user without authentication (should be allowed)"""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'role': UserRole.AUTHOR.value
        }

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_create_user_with_invalid_data(self):
        """Test creating a user with invalid data"""
        data = {
            'username': '',  # Invalid empty username
            'email': 'invalid-email',  # Invalid email format
            'password': '123',  # Too simple password
        }

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_list_users_unauthenticated(self):
        """Test listing users without authentication"""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_users_authenticated(self):
        """Test listing users with authentication"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(self.list_url)

        # Based on IsOwner permission, user should only see themselves
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_own_user(self):
        """Test retrieving own user details"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        detail_url = reverse('accounts:users-detail', kwargs={'pk': self.user.pk})

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user.id)

    def test_retrieve_other_user_forbidden(self):
        """Test retrieving another user's details (should be forbidden by IsOwner)"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        detail_url = reverse('accounts:users-detail', kwargs={'pk': self.other_user.pk})

        response = self.client.get(detail_url)

        # This depends on IsOwner permission implementation
        # Assuming it returns 403 for non-owners
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_update_own_user(self):
        """Test updating own user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        detail_url = reverse('accounts:users-detail', kwargs={'pk': self.user.pk})

        data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
        }

        response = self.client.patch(detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.user.email, 'updated@example.com')

    def test_update_other_user_forbidden(self):
        """Test updating another user (should be forbidden)"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        detail_url = reverse('accounts:users-detail', kwargs={'pk': self.other_user.pk})

        data = {
            'username': 'hackername',
        }

        response = self.client.patch(detail_url, data)

        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_delete_own_user(self):
        """Test deleting own user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        detail_url = reverse('accounts:users-detail', kwargs={'pk': self.user.pk})

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    def test_delete_other_user_forbidden(self):
        """Test deleting another user (should be forbidden)"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        detail_url = reverse('accounts:users-detail', kwargs={'pk': self.other_user.pk})

        response = self.client.delete(detail_url)

        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        self.assertTrue(User.objects.filter(pk=self.other_user.pk).exists())


class TestAuthenticationAndAuthorization(APITestCase):
    """Test authentication and authorization"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.token = RefreshToken.for_user(self.user).access_token
        self.list_url = reverse('accounts:users-list')

    def test_invalid_token(self):
        """Test request with invalid token"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_token(self):
        """Test request with expired token"""
        # Create an expired token
        token = RefreshToken.for_user(self.user).access_token
        token.set_exp(
            lifetime=timedelta(
                milliseconds=1
            )
        )

        time.sleep(1)  # Wait for token to expire

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_authorization_header(self):
        """Test request without authorization header"""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_malformed_authorization_header(self):
        """Test request with malformed authorization header"""
        self.client.credentials(HTTP_AUTHORIZATION='InvalidFormat token')

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestViewSetIntegration(APITestCase):
    """Integration tests for the complete viewset"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.client = APIClient()
        self.token = RefreshToken.for_user(self.user).access_token

    def test_complete_user_workflow(self):
        """Test complete workflow: create -> retrieve -> update -> delete"""
        # 1. Create user (unauthenticated)
        create_data = {
            'username': 'workflowuser',
            'email': 'workflow@example.com',
            'password': 'workflowpass123',
            'role': UserRole.REVIEWER.value
        }

        create_response = self.client.post(reverse('accounts:users-list'), create_data)
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        created_user_id = create_response.data['id']

        # Create token for new user
        new_user = User.objects.get(id=created_user_id)
        new_token = RefreshToken.for_user(new_user).access_token

        # 2. Retrieve user (authenticated as new user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_token}')
        retrieve_response = self.client.get(
            reverse('accounts:users-detail', kwargs={'pk': created_user_id})
        )
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieve_response.data['username'], 'workflowuser')

        # 3. Update user
        update_data = {'username': 'updatedworkflowuser'}
        update_response = self.client.patch(
            reverse('accounts:users-detail', kwargs={'pk': created_user_id}),
            update_data
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['username'], 'updatedworkflowuser')

        # 4. Test 'me' endpoint
        me_response = self.client.get(reverse('accounts:users-me'))
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['id'], created_user_id)

        # 5. Delete user
        delete_response = self.client.delete(
            reverse('accounts:users-detail', kwargs={'pk': created_user_id})
        )
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=created_user_id).exists())

    def test_me_action_consistency(self):
        """Test that 'me' action returns same data as retrieve for same user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Get data from 'me' endpoint
        me_response = self.client.get(reverse('accounts:users-me'))

        # Get data from retrieve endpoint
        retrieve_response = self.client.get(
            reverse('accounts:users-detail', kwargs={'pk': self.user.pk})
        )

        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data, retrieve_response.data)
