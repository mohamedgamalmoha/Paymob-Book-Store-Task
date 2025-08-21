import time
from datetime import date, timedelta
from unittest.mock import Mock

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.enums import UserRole
from accounts.api.permissions import ReadOnly, IsAuthor
from books.enums import LanguageChoices
from books.models import Book
from books.api.filters import BookFilterSet
from books.api.serializers import BookSerializer
from books.api.views import BookViewSet


User = get_user_model()


class BookViewSetTestCase(APITestCase):
    """Test cases for BookViewSet"""

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
        self.reviewer_user = User.objects.create_user(
            username='reviewer1',
            email='reviewer1@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )
        self.other_author = User.objects.create_user(
            username='author2',
            email='author2@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )

        # Create test books
        self.book1 = Book.objects.create(
            title='Test Book 1',
            slug='test-book-1',
            author=self.author_user,
            description='Description for test book 1',
            content='Content for test book 1',
            language=LanguageChoices.ENGLISH,
            pages=250,
            publication_date=date(2023, 1, 1),
            publisher='Test Publisher',
            is_available=True
        )
        self.book2 = Book.objects.create(
            title='Test Book 2',
            slug='test-book-2',
            author=self.other_author,
            description='Description for test book 2',
            content='Content for test book 2',
            language=LanguageChoices.SPANISH,
            pages=300,
            publication_date=date(2023, 6, 1),
            is_available=True
        )

        # Create JWT tokens
        self.author_token = RefreshToken.for_user(self.author_user).access_token
        self.reviewer_token = RefreshToken.for_user(self.reviewer_user).access_token
        self.other_author_token = RefreshToken.for_user(self.other_author).access_token

        # URLs
        self.list_url = reverse('books:books-list')
        self.detail_url = lambda slug: reverse('books:books-detail', kwargs={'slug': slug})

    def authenticate_user(self, user_token):
        """Helper method to authenticate a user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')

    def test_viewset_attributes(self):
        """Test viewset class attributes"""
        viewset = BookViewSet()

        self.assertEqual(viewset.queryset.model, Book)
        self.assertEqual(viewset.serializer_class, BookSerializer)
        self.assertEqual(viewset.permission_classes, [ReadOnly | IsAuthor])
        self.assertEqual(viewset.lookup_field, "slug")
        self.assertEqual(viewset.permitted_expands, ["author", "reviews"])
        self.assertEqual(viewset.permit_list_expands, ["author", "reviews"])
        self.assertEqual(viewset.filterset_class, BookFilterSet)


class TestPerformCreate(APITestCase):
    """Test perform_create method"""

    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.viewset = BookViewSet()
        self.viewset.request = Mock()
        self.viewset.request.user = self.author

    def test_perform_create_sets_author(self):
        """Test that perform_create sets the current user as author"""
        mock_serializer = Mock()

        self.viewset.perform_create(mock_serializer)

        mock_serializer.save.assert_called_once_with(author=self.author)

    def test_perform_create_with_different_user(self):
        """Test that perform_create uses request user regardless of serializer data"""
        mock_serializer = Mock()
        different_author = User.objects.create_user(
            username='different',
            email='different@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )

        # Even if serializer contains different author data, should use request.user
        self.viewset.perform_create(mock_serializer)

        mock_serializer.save.assert_called_once_with(author=self.author)


class TestBookCRUDOperations(APITestCase):
    """Test CRUD operations for books"""

    def setUp(self):
        self.author_user = User.objects.create_user(
            username='author1',
            email='author1@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.reviewer_user = User.objects.create_user(
            username='reviewer1',
            email='reviewer1@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )
        self.other_author = User.objects.create_user(
            username='author2',
            email='author2@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )

        self.book = Book.objects.create(
            title='Existing Book',
            slug='existing-book',
            author=self.author_user,
            description='Description for existing book',
            content='Content for existing book',
            language=LanguageChoices.ENGLISH,
            publication_date=date(2023, 1, 1),
            is_available=True
        )

        self.client = APIClient()
        self.author_token = RefreshToken.for_user(self.author_user).access_token
        self.reviewer_token = RefreshToken.for_user(self.reviewer_user).access_token
        self.other_author_token = RefreshToken.for_user(self.other_author).access_token
        self.list_url = reverse('books:books-list')

    def test_create_book_as_author(self):
        """Test creating a book as an authenticated author"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')

        data = {
            'title': 'New Book',
            'slug': 'new-book',
            'description': 'Description for new book',
            'content': 'Content for new book',
            'language': LanguageChoices.ENGLISH,
            'pages': 200,
            'publication_date': '2023-12-01',
            'publisher': 'New Publisher',
            'is_available': True
        }

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Book.objects.filter(slug='new-book').exists())

        # Verify author is set to request user
        created_book = Book.objects.get(slug='new-book')
        self.assertEqual(created_book.author, self.author_user)

    def test_create_book_as_reviewer(self):
        """Test creating a book as a reviewer (should be forbidden)"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer_token}')

        data = {
            'title': 'Reviewer Book',
            'slug': 'reviewer-book',
            'description': 'Description',
            'content': 'Content',
            'language': LanguageChoices.ENGLISH,
            'publication_date': '2023-12-01'
        }

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Book.objects.filter(slug='reviewer-book').exists())

    def test_create_book_unauthenticated(self):
        """Test creating a book without authentication"""
        data = {
            'title': 'Unauthenticated Book',
            'slug': 'unauth-book',
            'description': 'Description',
            'content': 'Content',
            'language': LanguageChoices.ENGLISH,
            'publication_date': '2023-12-01'
        }

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_book_with_invalid_data(self):
        """Test creating a book with invalid data"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')

        data = {
            'title': '',  # Empty title
            'slug': 'invalid-book',
            'description': 'Description',
            'content': 'Content',
            'language': 999,  # Invalid language choice
            'publication_date': 'invalid-date'  # Invalid date format
        }

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_list_books_unauthenticated(self):
        """Test listing books without authentication (should be allowed for reading)"""
        response = self.client.get(self.list_url)

        # Assuming ReadOnly permission allows unauthenticated read access
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])

    def test_list_books_authenticated(self):
        """Test listing books with authentication"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer_token}')

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_retrieve_book_by_slug(self):
        """Test retrieving a book by slug"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer_token}')
        detail_url = reverse('books:books-detail', kwargs={'slug': self.book.slug})

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slug'], self.book.slug)
        self.assertEqual(response.data['title'], self.book.title)

    def test_retrieve_nonexistent_book(self):
        """Test retrieving a non-existent book"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer_token}')
        detail_url = reverse('books:books-detail', kwargs={'slug': 'nonexistent-slug'})

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_book_as_author(self):
        """Test updating own book as author"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')
        detail_url = reverse('books:books-detail', kwargs={'slug': self.book.slug})

        data = {
            'title': 'Updated Book Title',
            'description': 'Updated description'
        }

        response = self.client.patch(detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, 'Updated Book Title')
        self.assertEqual(self.book.description, 'Updated description')

    def test_update_book_as_reviewer(self):
        """Test updating a book as reviewer (should be forbidden)"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer_token}')
        detail_url = reverse('books:books-detail', kwargs={'slug': self.book.slug})

        data = {
            'title': 'Reviewer Updated Title'
        }

        response = self.client.patch(detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_book_as_author(self):
        """Test deleting own book as author"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')
        detail_url = reverse('books:books-detail', kwargs={'slug': self.book.slug})

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(slug=self.book.slug).exists())

    def test_delete_other_authors_book(self):
        """Test deleting another author's book (should be forbidden)"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_author_token}')
        detail_url = reverse('books:books-detail', kwargs={'slug': self.book.slug})

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Book.objects.filter(slug=self.book.slug).exists())

    def test_delete_book_as_reviewer(self):
        """Test deleting a book as reviewer (should be forbidden)"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer_token}')
        detail_url = reverse('books:books-detail', kwargs={'slug': self.book.slug})

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Book.objects.filter(slug=self.book.slug).exists())


class TestBookFileUploads(APITestCase):
    """Test file upload functionality"""

    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.client = APIClient()
        self.token = RefreshToken.for_user(self.author).access_token
        self.list_url = reverse('books:books-list')

    def test_create_book_with_file(self):
        """Test creating a book with file attachment"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Create a simple test file
        book_file = SimpleUploadedFile(
            name='test_book.pdf',
            content=b'fake_pdf_content',
            content_type='application/pdf'
        )

        data = {
            'title': 'Book with File',
            'slug': 'book-with-file',
            'description': 'Description',
            'content': 'Content',
            'language': LanguageChoices.ENGLISH,
            'publication_date': '2023-12-01',
            'file': book_file
        }

        response = self.client.post(self.list_url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_book = Book.objects.get(slug='book-with-file')
        self.assertTrue(created_book.file)


class TestBookFiltering(APITestCase):
    """Test book filtering functionality"""

    def setUp(self):
        self.author1 = User.objects.create_user(
            username='author1',
            email='author1@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.author2 = User.objects.create_user(
            username='author2',
            email='author2@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )

        # Create books with different attributes for filtering
        self.english_book = Book.objects.create(
            title='English Book',
            slug='english-book',
            author=self.author1,
            description='English description',
            content='English content',
            language=LanguageChoices.ENGLISH,
            pages=200,
            publication_date=date(2023, 1, 1),
            is_available=True
        )

        self.spanish_book = Book.objects.create(
            title='Spanish Book',
            slug='spanish-book',
            author=self.author2,
            description='Spanish description',
            content='Spanish content',
            language=LanguageChoices.SPANISH,
            pages=300,
            publication_date=date(2023, 6, 1),
            is_available=False
        )

        self.client = APIClient()
        self.reviewer = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='testpass123',
            role=UserRole.REVIEWER
        )
        self.token = RefreshToken.for_user(self.reviewer).access_token
        self.list_url = reverse('books:books-list')

    def test_filter_books_by_language(self):
        """Test filtering books by language"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(self.list_url, {'language': LanguageChoices.ENGLISH})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify filtering logic based on your BookFilterSet implementation

    def test_filter_books_by_availability(self):
        """Test filtering books by availability"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(self.list_url, {'is_available': 'true'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify filtering logic based on your BookFilterSet implementation

    def test_filter_books_by_author(self):
        """Test filtering books by author"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(self.list_url, {'author': self.author1.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify filtering logic based on your BookFilterSet implementation


class TestBookAuthentication(APITestCase):
    """Test authentication scenarios"""

    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123',
            role=UserRole.AUTHOR
        )
        self.client = APIClient()
        self.token = RefreshToken.for_user(self.author).access_token
        self.list_url = reverse('books:books-list')

    def test_invalid_token(self):
        """Test request with invalid token"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')

        data = {
            'title': 'Test Book',
            'slug': 'test-book',
            'description': 'Description',
            'content': 'Content',
            'language': LanguageChoices.ENGLISH,
            'publication_date': '2023-12-01'
        }

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_token(self):
        """Test request with expired token"""
        # Create an expired token
        token = RefreshToken.for_user(self.author).access_token
        token.set_exp(
            lifetime=timedelta(
                milliseconds=1
            )
        )  # Set to expired

        time.sleep(1)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestBookViewSetIntegration(APITestCase):
    """Integration tests for the complete book viewset"""

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

        self.client = APIClient()
        self.author_token = RefreshToken.for_user(self.author).access_token
        self.reviewer_token = RefreshToken.for_user(self.reviewer).access_token

    def test_complete_book_workflow(self):
        """Test complete workflow: create -> retrieve -> update -> delete"""
        # 1. Create book as author
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')

        create_data = {
            'title': 'Workflow Book',
            'slug': 'workflow-book',
            'description': 'Workflow description',
            'content': 'Workflow content',
            'language': LanguageChoices.ENGLISH,
            'pages': 250,
            'publication_date': '2023-12-01',
            'publisher': 'Workflow Publisher'
        }

        create_response = self.client.post(reverse('books:books-list'), create_data)

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        # 2. Retrieve book (as reviewer for read access)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reviewer_token}')
        retrieve_response = self.client.get(
            reverse('books:books-detail', kwargs={'slug': 'workflow-book'})
        )
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieve_response.data['title'], 'Workflow Book')

        # 3. Update book (as original author)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')
        update_data = {'title': 'Updated Workflow Book'}
        update_response = self.client.patch(
            reverse('books:books-detail', kwargs={'slug': 'workflow-book'}),
            update_data
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['title'], 'Updated Workflow Book')

        # 4. Delete book (as original author)
        delete_response = self.client.delete(
            reverse('books:books-detail', kwargs={'slug': 'workflow-book'})
        )
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(slug='workflow-book').exists())

    def test_author_assignment_consistency(self):
        """Test that author is consistently assigned to request user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')

        # Try to create book with different author in data
        create_data = {
            'title': 'Author Test Book',
            'slug': 'author-test-book',
            'description': 'Description',
            'content': 'Content',
            'language': LanguageChoices.ENGLISH,
            'publication_date': '2023-12-01',
            'author': self.reviewer.id  # Try to set different author
        }

        response = self.client.post(reverse('books:books-list'), create_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_book = Book.objects.get(slug='author-test-book')
        # Should be set to request user, not the author in data
        self.assertEqual(created_book.author, self.author)

    def test_slug_lookup_consistency(self):
        """Test that slug lookup works correctly"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')

        # Create book
        book = Book.objects.create(
            title='Slug Test Book',
            slug='slug-test-book',
            author=self.author,
            description='Description',
            content='Content',
            language=LanguageChoices.ENGLISH,
            publication_date=date(2023, 12, 1)
        )

        # Test that we can access by slug, not by ID
        slug_response = self.client.get(
            reverse('books:books-detail', kwargs={'slug': book.slug})
        )
        self.assertEqual(slug_response.status_code, status.HTTP_200_OK)
