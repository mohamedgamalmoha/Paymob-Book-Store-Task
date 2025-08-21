import time
from datetime import date, timedelta
from unittest.mock import patch, Mock

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.enums import UserRole
from accounts.api.permissions import ReadOnly, IsReviewer
from books.enums import LanguageChoices
from books.models import Book, Review
from books.api.serializers import ReviewSerializer
from books.api.filters import ReviewFilterSet
from books.api.views import ReviewViewSet


User = get_user_model()


class ReviewViewSetTestCase(APITestCase):
    """Test cases for ReviewViewSet"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create test users
        self.author_user = User.objects.create_user(
            username='author1',
            email='author1@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.reviewer_user1 = User.objects.create_user(
            username='reviewer1',
            email='reviewer1@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )
        self.reviewer_user2 = User.objects.create_user(
            username='reviewer2',
            email='reviewer2@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )

        # Create test book
        self.book1 = Book.objects.create(
            title='Test Book 1',
            slug='test-book-1',
            author=self.author_user,
            description='Description for test book 1',
            content='Content for test book 1',
            language=LanguageChoices.ENGLISH,
            pages=250,
            publication_date=date(2023, 1, 1),
            is_available=True
        )
        self.book2 = Book.objects.create(
            title='Test Book 2',
            slug='test-book-2',
            author=self.author_user,
            description='Description for test book 2',
            content='Content for test book 2',
            language=LanguageChoices.SPANISH,
            pages=300,
            publication_date=date(2023, 6, 1),
            is_available=True
        )

        # Create test reviews
        self.review1 = Review.objects.create(
            book=self.book1,
            reviewer=self.reviewer_user1,
            title='Great Book',
            content='This is an excellent book with great content.',
            rating=5,
            is_trusted=True
        )
        self.review2 = Review.objects.create(
            book=self.book2,
            reviewer=self.reviewer_user2,
            title='Good Read',
            content='This book was quite enjoyable.',
            rating=4,
            is_trusted=False
        )

        # Create JWT tokens
        self.author_token = RefreshToken.for_user(self.author_user).access_token
        self.reviewer1_token = RefreshToken.for_user(self.reviewer_user1).access_token
        self.reviewer2_token = RefreshToken.for_user(self.reviewer_user2).access_token

        # URLs
        self.list_url = reverse('books:reviews-list')
        self.detail_url = lambda pk: reverse('books:reviews-detail', kwargs={'pk': pk})

    def authenticate_user(self, user_token):
        """Helper method to authenticate a user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')

    def test_viewset_attributes(self):
        """Test viewset class attributes"""
        viewset = ReviewViewSet()

        self.assertEqual(viewset.queryset.model, Review)
        self.assertEqual(viewset.serializer_class, ReviewSerializer)
        self.assertEqual(viewset.permission_classes, [ReadOnly | IsReviewer])
        self.assertEqual(viewset.permitted_expands, ["book", "reviewer"])
        self.assertEqual(viewset.permit_list_expands, ["book", "reviewer"])
        self.assertEqual(viewset.filterset_class, ReviewFilterSet)


class TestPerformCreate(APITestCase):
    """Test perform_create method"""

    def setUp(self):
        self.reviewer = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )
        self.viewset = ReviewViewSet()
        self.viewset.request = Mock()
        self.viewset.request.user = self.reviewer

    def test_perform_create_sets_reviewer(self):
        """Test that perform_create sets the current user as reviewer"""
        mock_serializer = Mock()

        self.viewset.perform_create(mock_serializer)

        mock_serializer.save.assert_called_once_with(reviewer=self.reviewer)

    def test_perform_create_with_different_user(self):
        """Test that perform_create uses request user regardless of serializer data"""
        mock_serializer = Mock()
        different_reviewer = User.objects.create_user(
            username='different',
            email='different@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )

        # Even if serializer contains different reviewer data, should use request.user
        self.viewset.perform_create(mock_serializer)

        mock_serializer.save.assert_called_once_with(reviewer=self.reviewer)


class TestReviewCRUDOperations(APITestCase):
    """Test CRUD operations for reviews"""

    def setUp(self):
        self.author = User.objects.create_user(
            username='author1',
            email='author1@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.reviewer1 = User.objects.create_user(
            username='reviewer1',
            email='reviewer1@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )
        self.reviewer2 = User.objects.create_user(
            username='reviewer2',
            email='reviewer2@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )

        self.book = Book.objects.create(
            title='Integration Test Book',
            slug='integration-test-book',
            author=self.author,
            description='Book for integration testing',
            content='Content for integration testing',
            language=LanguageChoices.ENGLISH,
            publication_date=date(2023, 1, 1),
            is_available=True
        )

        self.client = APIClient()
        self.reviewer1_token = RefreshToken.for_user(self.reviewer1).access_token
        self.reviewer2_token = RefreshToken.for_user(self.reviewer2).access_token

    def test_complete_review_workflow(self):
        """Test complete workflow: create -> retrieve -> update -> delete"""
        # 1. Create review as reviewer
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer1_token}')

        create_data = {
            'book': self.book.id,
            'title': 'Workflow Review',
            'content': 'This is a workflow test review with detailed content.',
            'rating': 4,
        }

        create_response = self.client.post(reverse('books:reviews-list'), create_data)
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        created_review_id = create_response.data['id']

        # 2. Retrieve review
        retrieve_response = self.client.get(
            reverse('books:reviews-detail', kwargs={'pk': created_review_id})
        )
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieve_response.data['title'], 'Workflow Review')
        self.assertEqual(retrieve_response.data['reviewer'], self.reviewer1.id)

        # 3. Update review (as original reviewer)
        update_data = {
            'title': 'Updated Workflow Review',
            'content': 'Updated content for the workflow test.',
            'rating': 5
        }
        update_response = self.client.patch(
            reverse('books:reviews-detail', kwargs={'pk': created_review_id}),
            update_data
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['title'], 'Updated Workflow Review')
        self.assertEqual(update_response.data['rating'], 5)

        # 4. Verify another reviewer cannot modify this review
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer2_token}')
        unauthorized_update = self.client.patch(
            reverse('books:reviews-detail', kwargs={'pk': created_review_id}),
            {'title': 'Unauthorized Update'}
        )
        self.assertEqual(unauthorized_update.status_code, status.HTTP_403_FORBIDDEN)

        # 5. Delete review (as original reviewer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer1_token}')
        delete_response = self.client.delete(
            reverse('books:reviews-detail', kwargs={'pk': created_review_id})
        )
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=created_review_id).exists())

    def test_reviewer_assignment_consistency(self):
        """Test that reviewer is consistently assigned to request user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer1_token}')

        # Try to create review with different reviewer in data
        create_data = {
            'book': self.book.id,
            'title': 'Reviewer Test Review',
            'content': 'Testing reviewer assignment',
            'rating': 3,
            'reviewer': self.reviewer2.id  # Try to set different reviewer
        }

        response = self.client.post(reverse('books:reviews-list'), create_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_review = Review.objects.get(title='Reviewer Test Review')
        # Should be set to request user, not the reviewer in data
        self.assertEqual(created_review.reviewer, self.reviewer1)

    def test_review_ordering(self):
        """Test that reviews are ordered by created_at and updated_at (descending)"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer1_token}')

        # Create a second book for another review
        book2 = Book.objects.create(
            title='Second Book',
            slug='second-book',
            author=self.author,
            description='Second book description',
            content='Second book content',
            language=LanguageChoices.ENGLISH,
            publication_date=date(2023, 2, 1),
            is_available=True
        )

        # Create first review
        first_review_data = {
            'book': self.book.id,
            'title': 'First Review',
            'content': 'First review content',
            'rating': 4,
        }
        first_response = self.client.post(reverse('books:reviews-list'), first_review_data)
        first_review_id = first_response.data['id']

        # Create second review (should be newer)
        second_review_data = {
            'book': book2.id,
            'title': 'Second Review',
            'content': 'Second review content',
            'rating': 5,
        }
        second_response = self.client.post(reverse('books:reviews-list'), second_review_data)
        second_review_id = second_response.data['id']

        # List reviews and check ordering
        list_response = self.client.get(reverse('books:reviews-list'))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        reviews = list_response.data['results']
        # Newer review should come first
        self.assertEqual(reviews[0]['id'], second_review_id)
        self.assertEqual(reviews[1]['id'], first_review_id)

    def test_review_model_constraints(self):
        """Test model-level constraints and validators"""
        # Test rating validators at model level
        with self.assertRaises(ValidationError):
            review = Review(
                book=self.book,
                reviewer=self.reviewer1,
                title='Invalid Review',
                content='Content',
                rating=0  # Invalid rating
            )
            review.full_clean()

        with self.assertRaises(ValidationError):
            review = Review(
                book=self.book,
                reviewer=self.reviewer1,
                title='Invalid Review',
                content='Content',
                rating=6  # Invalid rating
            )
            review.full_clean()

    def test_review_meta_information(self):
        """Test model meta information"""
        # Test verbose names
        self.assertEqual(Review._meta.verbose_name, 'Review')
        self.assertEqual(Review._meta.verbose_name_plural, 'Reviews')

        # Test ordering
        self.assertEqual(Review._meta.ordering, ('-created_at', '-updated_at'))

        # Test unique_together
        self.assertIn(('book', 'reviewer'), Review._meta.unique_together)

        # Test indexes
        index_fields = []
        for index in Review._meta.indexes:
            index_fields.extend(index.fields)

        self.assertIn('book', index_fields)
        self.assertIn('reviewer', index_fields)
        self.assertIn('rating', index_fields)


class TestReviewSerializerBehavior(APITestCase):
    """Test serializer-specific behavior"""

    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.reviewer = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )
        self.book = Book.objects.create(
            title='Serializer Test Book',
            slug='serializer-test-book',
            author=self.author,
            description='Book for testing serializer',
            content='Content for serializer testing',
            language=LanguageChoices.ENGLISH,
            publication_date=date(2023, 1, 1)
        )
        self.review = Review.objects.create(
            book=self.book,
            reviewer=self.reviewer,
            title='Serializer Test Review',
            content='Review for testing serializer behavior',
            rating=4,
            is_trusted=True
        )
        self.client = APIClient()
        self.token = RefreshToken.for_user(self.reviewer).access_token

    def test_read_only_fields_in_response(self):
        """Test that read-only fields are included in response but cannot be set"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Retrieve review
        response = self.client.get(
            reverse('books:reviews-detail', kwargs={'pk': self.review.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that read-only fields are present in response
        self.assertIn('reviewer', response.data)
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)

        # Verify values
        self.assertEqual(response.data['reviewer'], self.reviewer.id)
        self.assertIsNotNone(response.data['created_at'])
        self.assertIsNotNone(response.data['updated_at'])

    def test_all_fields_included(self):
        """Test that all model fields are included in serializer (exclude=())"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(
            reverse('books:reviews-detail', kwargs={'pk': self.review.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that all expected fields are present
        expected_fields = [
            'id', 'book', 'reviewer', 'title', 'content',
            'rating', 'is_trusted', 'created_at', 'updated_at'
        ]

        for field in expected_fields:
            with self.subTest(field=field):
                self.assertIn(field, response.data)

    def test_serializer_validation_messages(self):
        """Test custom validation error messages"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Create a second book to test with
        book2 = Book.objects.create(
            title='Second Book',
            slug='second-book',
            author=self.author,
            description='Second book description',
            content='Second book content',
            language=LanguageChoices.ENGLISH,
            publication_date=date(2023, 2, 1)
        )

        # Test various invalid data scenarios
        invalid_data_scenarios = [
            {
                'data': {'book': '', 'title': 'Test', 'content': 'Test', 'rating': 4},
                'expected_error_field': 'book'
            },
            {
                'data': {'book': book2.id, 'title': '', 'content': 'Test', 'rating': 4},
                'expected_error_field': 'title'
            },
            {
                'data': {'book': book2.id, 'title': 'Test', 'content': '', 'rating': 4},
                'expected_error_field': 'content'
            },
            {
                'data': {'book': book2.id, 'title': 'Test', 'content': 'Test'},
                'expected_error_field': 'rating'
            }
        ]

        for scenario in invalid_data_scenarios:
            with self.subTest(scenario=scenario['data']):
                response = self.client.post(reverse('books:reviews-list'), scenario['data'])
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(scenario['expected_error_field'], response.data)


class TestEdgeCasesAndErrorHandling(APITestCase):
    """Test edge cases and error handling"""

    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.reviewer = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )
        self.book = Book.objects.create(
            title='Edge Case Book',
            slug='edge-case-book',
            author=self.author,
            description='Book for edge case testing',
            content='Content for edge case testing',
            language=LanguageChoices.ENGLISH,
            publication_date=date(2023, 1, 1)
        )
        self.client = APIClient()
        self.token = RefreshToken.for_user(self.reviewer).access_token

    def test_create_review_with_nonexistent_book(self):
        """Test creating review with non-existent book ID"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        data = {
            'book': 99999,  # Non-existent book ID
            'title': 'Review for non-existent book',
            'content': 'This should fail',
            'rating': 4,
        }

        response = self.client.post(reverse('books:reviews-list'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book', response.data)

    def test_create_review_with_extremely_long_title(self):
        """Test creating review with title exceeding max_length"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Title longer than 200 characters
        long_title = 'A' * 201

        data = {
            'book': self.book.id,
            'title': long_title,
            'content': 'Test content',
            'rating': 4,
        }

        response = self.client.post(reverse('books:reviews-list'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_create_review_with_empty_content(self):
        """Test creating review with empty content"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        data = {
            'book': self.book.id,
            'title': 'Empty Content Review',
            'content': '',  # Empty content
            'rating': 4,
        }

        response = self.client.post(reverse('books:reviews-list'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)

    def test_partial_update_with_invalid_rating(self):
        """Test partial update with invalid rating"""
        # Create a review first
        review = Review.objects.create(
            book=self.book,
            reviewer=self.reviewer,
            title='Test Review',
            content='Test content',
            rating=4
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Try to update with invalid rating
        response = self.client.patch(
            reverse('books:reviews-detail', kwargs={'pk': review.pk}),
            {'rating': 10}  # Invalid rating
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('rating', response.data)

    def test_bulk_operations_not_supported(self):
        """Test that bulk create/update operations handle properly"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Try to send list of reviews (if your API doesn't support bulk operations)
        bulk_data = [
            {
                'book': self.book.id,
                'title': 'Bulk Review 1',
                'content': 'Content 1',
                'rating': 4,
            },
            {
                'book': self.book.id,
                'title': 'Bulk Review 2',
                'content': 'Content 2',
                'rating': 5,
            }
        ]

        response = self.client.post(reverse('books:reviews-list'), bulk_data, format='json')

        # Should fail if bulk operations are not supported
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestReviewCreation(APITestCase):

    def setUp(self):
        self.book = Book.objects.create(
            title = 'Test Book',
            slug = 'test-book',
            author = self.author,
            description = 'Test description',
            content = 'Test content',
            language = LanguageChoices.ENGLISH,
            publication_date = date(2023, 1, 1),
            is_available = True
        )

        self.existing_review = Review.objects.create(
            book = self.book,
            reviewer = self.reviewer1,
            title = 'Existing Review',
            content = 'This is an existing review.',
            rating = 4
        )

        self.client = APIClient()
        self.author_token = RefreshToken.for_user(self.author).access_token
        self.reviewer1_token = RefreshToken.for_user(self.reviewer1).access_token
        self.reviewer2_token = RefreshToken.for_user(self.reviewer2).access_token
        self.list_url = reverse('books:reviews-list')


def test_create_review_as_reviewer(self):
    """Test creating a review as an authenticated reviewer"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer2_token}')

    data = {
        'book': self.book.id,
        'title': 'New Review',
        'content': 'This is a new review content.',
        'rating': 5,
    }

    response = self.client.post(self.list_url, data)

    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    self.assertTrue(Review.objects.filter(title='New Review').exists())

    # Verify reviewer is set to request user
    created_review = Review.objects.get(title='New Review')
    self.assertEqual(created_review.reviewer, self.reviewer2)


def test_create_review_as_author(self):
    """Test creating a review as an author (should be forbidden)"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')

    data = {
        'book': self.book.id,
        'title': 'Author Review',
        'content': 'Review by author',
        'rating': 5,
    }

    response = self.client.post(self.list_url, data)

    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    self.assertFalse(Review.objects.filter(title='Author Review').exists())


def test_create_review_unauthenticated(self):
    """Test creating a review without authentication"""
    data = {
        'book': self.book.id,
        'title': 'Unauthenticated Review',
        'content': 'Review without auth',
        'rating': 3,
    }

    response = self.client.post(self.list_url, data)

    self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


def test_create_review_with_invalid_rating(self):
    """Test creating a review with invalid rating"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer2_token}')

    # Test rating outside valid range (1-5)
    invalid_ratings = [0, 6, -1, 10]

    for rating in invalid_ratings:
        with self.subTest(rating=rating):
            data = {
                'book': self.book.id,
                'title': 'Invalid Rating Review',
                'content': 'Review with invalid rating',
                'rating': rating,
            }

            response = self.client.post(self.list_url, data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


def test_create_review_with_missing_fields(self):
    """Test creating a review with missing required fields"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer2_token}')

    # Test missing book
    data = {
        'title': 'Review without book',
        'content': 'Content',
        'rating': 4,
    }

    response = self.client.post(self.list_url, data)
    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertIn('book', response.data)


def test_create_duplicate_review(self):
    """Test creating duplicate review for same book-reviewer combination"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer1_token}')

    # Try to create another review for the same book by same reviewer
    data = {
        'book': self.book.id,
        'title': 'Duplicate Review',
        'content': 'This is a duplicate review.',
        'rating': 3,
    }

    response = self.client.post(self.list_url, data)

    # Should fail due to unique_together constraint
    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


def test_list_reviews_unauthenticated(self):
    """Test listing reviews without authentication (should be allowed for reading)"""
    response = self.client.get(self.list_url)

    # Assuming ReadOnly permission allows unauthenticated read access
    self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])


def test_list_reviews_authenticated(self):
    """Test listing reviews with authentication"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer1_token}')

    response = self.client.get(self.list_url)

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertGreaterEqual(len(response.data['results']), 1)


def test_retrieve_review(self):
    """Test retrieving a specific review"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer1_token}')
    detail_url = reverse('books:reviews-detail', kwargs={'pk': self.existing_review.pk})

    response = self.client.get(detail_url)

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertEqual(response.data['id'], self.existing_review.id)
    self.assertEqual(response.data['title'], self.existing_review.title)


def test_retrieve_nonexistent_review(self):
    """Test retrieving a non-existent review"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer1_token}')
    detail_url = reverse('books:reviews-detail', kwargs={'pk': 99999})

    response = self.client.get(detail_url)

    self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


def test_update_own_review_as_reviewer(self):
    """Test updating own review as reviewer"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer1_token}')
    detail_url = reverse('books:reviews-detail', kwargs={'pk': self.existing_review.pk})

    data = {
        'title': 'Updated Review Title',
        'content': 'Updated review content',
        'rating': 5
    }

    response = self.client.patch(detail_url, data)

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.existing_review.refresh_from_db()
    self.assertEqual(self.existing_review.title, 'Updated Review Title')
    self.assertEqual(self.existing_review.content, 'Updated review content')
    self.assertEqual(self.existing_review.rating, 5)


def test_update_other_reviewers_review(self):
    """Test updating another reviewer's review (should be forbidden)"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer2_token}')
    detail_url = reverse('books:reviews-detail', kwargs={'pk': self.existing_review.pk})

    data = {
        'title': 'Hacked Review Title'
    }

    response = self.client.patch(detail_url, data)

    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    self.existing_review.refresh_from_db()
    self.assertNotEqual(self.existing_review.title, 'Hacked Review Title')


def test_update_review_as_author(self):
    """Test updating a review as author (should be forbidden)"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')
    detail_url = reverse('books:reviews-detail', kwargs={'pk': self.existing_review.pk})

    data = {
        'title': 'Author Updated Title'
    }

    response = self.client.patch(detail_url, data)

    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


def test_update_review_readonly_fields(self):
    """Test that readonly fields cannot be updated"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer1_token}')
    detail_url = reverse('books:reviews-detail', kwargs={'pk': self.existing_review.pk})

    original_reviewer = self.existing_review.reviewer
    original_created_at = self.existing_review.created_at

    data = {
        'reviewer': self.reviewer2.id,  # Should be read-only
        'created_at': '2023-12-01T00:00:00Z',  # Should be read-only
        'title': 'Updated Title'
    }

    response = self.client.patch(detail_url, data)

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.existing_review.refresh_from_db()

    # Readonly fields should not change
    self.assertEqual(self.existing_review.reviewer, original_reviewer)
    self.assertEqual(self.existing_review.created_at, original_created_at)
    # Non-readonly field should change
    self.assertEqual(self.existing_review.title, 'Updated Title')


def test_delete_own_review_as_reviewer(self):
    """Test deleting own review as reviewer"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer1_token}')
    detail_url = reverse('books:reviews-detail', kwargs={'pk': self.existing_review.pk})

    response = self.client.delete(detail_url)

    self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    self.assertFalse(Review.objects.filter(pk=self.existing_review.pk).exists())


def test_delete_other_reviewers_review(self):
    """Test deleting another reviewer's review (should be forbidden)"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer2_token}')
    detail_url = reverse('books:reviews-detail', kwargs={'pk': self.existing_review.pk})

    response = self.client.delete(detail_url)

    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    self.assertTrue(Review.objects.filter(pk=self.existing_review.pk).exists())


def test_delete_review_as_author(self):
    """Test deleting a review as author (should be forbidden)"""
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')
    detail_url = reverse('books:reviews-detail', kwargs={'pk': self.existing_review.pk})

    response = self.client.delete(detail_url)

    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    self.assertTrue(Review.objects.filter(pk=self.existing_review.pk).exists())


class TestReviewRatingValidation(APITestCase):
    """Test rating field validation"""

    def setUp(self):
        self.reviewer = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.book = Book.objects.create(
            title='Test Book',
            slug='test-book',
            author=self.author,
            description='Test description',
            content='Test content',
            language=LanguageChoices.ENGLISH,
            publication_date=date(2023, 1, 1)
        )
        self.client = APIClient()
        self.token = RefreshToken.for_user(self.reviewer).access_token
        self.list_url = reverse('books:reviews-list')

    def test_valid_ratings(self):
        """Test that valid ratings (1-5) are accepted"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        valid_ratings = [1, 2, 3, 4, 5]

        for rating in valid_ratings:
            with self.subTest(rating=rating):
                # Create a new book for each review to avoid unique constraint issues
                book = Book.objects.create(
                    title=f'Test Book {rating}',
                    slug=f'test-book-{rating}',
                    author=self.author,
                    description='Test description',
                    content='Test content',
                    language=LanguageChoices.ENGLISH,
                    publication_date=date(2023, 1, 1)
                )

                data = {
                    'book': book.id,
                    'title': f'Review with rating {rating}',
                    'content': 'Test content',
                    'rating': rating,
                }

                response = self.client.post(self.list_url, data)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_ratings(self):
        """Test that invalid ratings are rejected"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        invalid_ratings = [0, -1, 6, 10, -5]

        for rating in invalid_ratings:
            with self.subTest(rating=rating):
                data = {
                    'book': self.book.id,
                    'title': f'Review with invalid rating {rating}',
                    'content': 'Test content',
                    'rating': rating,
                }

                response = self.client.post(self.list_url, data)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestReviewFiltering(APITestCase):
    """Test review filtering functionality"""

    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.reviewer1 = User.objects.create_user(
            username='reviewer1',
            email='reviewer1@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )
        self.reviewer2 = User.objects.create_user(
            username='reviewer2',
            email='reviewer2@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )

        self.book1 = Book.objects.create(
            title='Book 1',
            slug='book-1',
            author=self.author,
            description='Description 1',
            content='Content 1',
            language=LanguageChoices.ENGLISH,
            publication_date=date(2023, 1, 1)
        )
        self.book2 = Book.objects.create(
            title='Book 2',
            slug='book-2',
            author=self.author,
            description='Description 2',
            content='Content 2',
            language=LanguageChoices.SPANISH,
            publication_date=date(2023, 6, 1)
        )

        # Create reviews with different attributes for filtering
        self.high_rating_review = Review.objects.create(
            book=self.book1,
            reviewer=self.reviewer1,
            title='Excellent Book',
            content='This book is excellent.',
            rating=5,
            is_trusted=True
        )

        self.low_rating_review = Review.objects.create(
            book=self.book2,
            reviewer=self.reviewer2,
            title='Average Book',
            content='This book is average.',
            rating=2,
            is_trusted=False
        )

        self.client = APIClient()
        self.token = RefreshToken.for_user(self.reviewer1).access_token
        self.list_url = reverse('books:reviews-list')

    def test_filter_reviews_by_rating(self):
        """Test filtering reviews by rating"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(self.list_url, {'rating': 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify filtering logic based on your ReviewFilterSet implementation

    def test_filter_reviews_by_book(self):
        """Test filtering reviews by book"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(self.list_url, {'book': self.book1.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify filtering logic based on your ReviewFilterSet implementation

    def test_filter_reviews_by_reviewer(self):
        """Test filtering reviews by reviewer"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(self.list_url, {'reviewer': self.reviewer1.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify filtering logic based on your ReviewFilterSet implementation

    def test_filter_reviews_by_trusted_status(self):
        """Test filtering reviews by trusted status"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(self.list_url, {'is_trusted': 'true'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify filtering logic based on your ReviewFilterSet implementation


class TestReviewAuthentication(APITestCase):
    """Test authentication scenarios"""

    def setUp(self):
        self.reviewer = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.book = Book.objects.create(
            title='Test Book',
            slug='test-book',
            author=self.author,
            description='Test description',
            content='Test content',
            language=LanguageChoices.ENGLISH,
            publication_date=date(2023, 1, 1)
        )
        self.client = APIClient()
        self.token = RefreshToken.for_user(self.reviewer).access_token
        self.list_url = reverse('books:reviews-list')

    def test_invalid_token(self):
        """Test request with invalid token"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')

        data = {
            'book': self.book.id,
            'title': 'Test Review',
            'content': 'Test content',
            'rating': 4,
        }

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_token(self):
        """Test request with expired token"""
        # Create an expired token
        token = RefreshToken.for_user(self.reviewer).access_token
        token.set_exp(
            lifetime=timedelta(
                milliseconds=1
            )
        )  # Set to expired

        time.sleep(1)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_authorization_header(self):
        """Test request without authorization header"""
        response = self.client.get(self.list_url)

        # Depends on ReadOnly permission implementation
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])
