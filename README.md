# Paymob-Book-Store-Task

A Django REST Framework-based API for managing a book store with user roles, book management, reviews, and favorites functionality.

## Features

- **User Management**: Custom user model with role-based access (Admin, Author, Reviewer)
- **Book Management**: Full CRUD operations for books with file uploads
- **Review System**: Users can review books with ratings (1-5 stars)
- **Favorites System**: Users can mark books as favorites with reasons
- **JWT Authentication**: Secure token-based authentication
- **API Documentation**: Auto-generated documentation with Swagger/Redoc
- **Admin Interface**: Beautiful Django admin with Jazzmin theme
- **Flexible API**: Support for field expansion and filtering

## Tech Stack

- **Backend**: Django 5.2.5 + Django REST Framework 3.16.1
- **Database**: PostgreSQL
- **Authentication**: JWT (Simple JWT)
- **Documentation**: drf-spectacular (OpenAPI 3.0)
- **Admin**: Django Admin with Jazzmin theme
- **Additional**: CORS support, flexible fields, filtering

## User Roles

- **Admin**: Full system access
- **Author**: Can create and manage their own books
- **Reviewer**: Can create reviews for books
- **Other**: Basic user role

## API Endpoints

### Authentication
- `POST /api/auth/token/` - Obtain JWT token pair
- `POST /api/auth/token/refresh/` - Refresh access token
- `POST /api/auth/token/verify/` - Verify token validity

### Users
- `GET /api/users/` - List users (paginated)
- `POST /api/users/` - Create new user (public)
- `GET /api/users/{id}/` - Get user details
- `PUT /api/users/{id}/` - Update user
- `DELETE /api/users/{id}/` - Delete user
- `GET /api/users/me/` - Get current user profile

### Books
- `GET /api/books/` - List books with filtering
- `POST /api/books/` - Create book (Authors only)
- `GET /api/books/{slug}/` - Get book by slug
- `PUT /api/books/{slug}/` - Update book (Author only)
- `DELETE /api/books/{slug}/` - Delete book (Author only)

### Reviews
- `GET /api/reviews/` - List reviews
- `POST /api/reviews/` - Create review (Reviewers only)
- `GET /api/reviews/{id}/` - Get review details
- `PUT /api/reviews/{id}/` - Update review (Owner only)
- `DELETE /api/reviews/{id}/` - Delete review (Owner only)

### Favorites
- `GET /api/favorites/` - List user's favorites
- `POST /api/favorites/` - Add book to favorites
- `GET /api/favorites/{id}/` - Get favorite details
- `PUT /api/favorites/{id}/` - Update favorite
- `DELETE /api/favorites/{id}/` - Remove from favorites

## Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL
- pip (Python package manager)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd book-store-api
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
Run the provided PostgreSQL setup script:
```bash
chmod +x setup_postgres.sh
./setup_postgres.sh
```

Or manually create the database:
```sql
CREATE DATABASE book_store_db;
CREATE USER book_store_user WITH PASSWORD 'book_store_password';
ALTER USER book_store_user WITH CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE book_store_db TO book_store_user;
```

### 5. Environment Variables
Create a `.env` file in the root directory:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
RDS_DB_ENGINE=django.db.backends.postgresql
RDS_DB_NAME=book_store_db
RDS_TEST_DB_NAME=test_book_store_db
RDS_USERNAME=book_store_user
RDS_PASSWORD=book_store_password
RDS_HOSTNAME=localhost
RDS_PORT=5432

# CORS
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOW_CREDENTIALS=True
```

### 6. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser
```bash
python manage.py createsuperuser
```

### 8. Collect Static Files
```bash
python manage.py collectstatic
```

### 9. Run Development Server
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

## API Documentation

Once the server is running, access the API documentation:
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **Redoc**: `http://localhost:8000/api/docs/redoc/`
- **Admin Interface**: `http://localhost:8000/admin/`

## Usage Examples

### 1. Register a New User
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_author",
    "email": "john@example.com",
    "password": "securepassword123",
    "role": 2,
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### 2. Get JWT Token
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_author",
    "password": "securepassword123"
  }'
```

### 3. Create a Book (Authors only)
```bash
curl -X POST http://localhost:8000/api/books/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Django for Beginners",
    "slug": "django-for-beginners",
    "description": "Learn Django web development",
    "content": "Full book content here...",
    "language": 1,
    "pages": 300,
    "publication_date": "2024-01-15",
    "publisher": "Tech Books Inc"
  }'
```

### 4. Get Books with Expanded Author Info
```bash
curl "http://localhost:8000/api/books/?expand=author" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Create a Review (Reviewers only)
```bash
curl -X POST http://localhost:8000/api/reviews/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "book": 1,
    "title": "Great book!",
    "content": "This book helped me learn Django effectively.",
    "rating": 5
  }'
```

## API Features

### Field Expansion
The API supports expanding related fields:
```
GET /api/books/?expand=author,reviews
GET /api/users/?expand=books,reviews,favorites
```

### Filtering
Books can be filtered by various criteria:
```
GET /api/books/?search=django
GET /api/books/?author=1&language=1
GET /api/books/?is_available=true
```

### Pagination
All list endpoints support pagination:
```
GET /api/books/?page=2
```

## Project Structure

```
book-store-api/
├── accounts/                 # User management app
│   ├── api/                 # API views, serializers, permissions
│   ├── models.py            # Custom user model with roles
│   └── enums.py             # User role choices
├── books/                   # Books management app
│   ├── api/                 # Book, Review, Favorites APIs
│   ├── models.py            # Book, Review, Favorites models
│   └── enums.py             # Language and reason choices
├── core/                    # Django project settings
├── static/                  # Static files
├── media/                   # User uploads
└── requirements.txt         # Python dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email your-email@example.com or create an issue in the repository.

## Roadmap

- [ ] Add book categories/genres
- [ ] Implement book lending system
- [ ] Add book recommendations
- [ ] Implement social features (follow authors)
- [ ] Add book rating aggregation
- [ ] Implement notification system