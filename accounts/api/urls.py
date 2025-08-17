from django.urls import path, include

from rest_framework import routers

from accounts.api.views import UserViewSet


app_name = 'accounts'

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls), name='accounts_routes'),
]
