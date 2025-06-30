from rest_framework.routers import DefaultRouter
from .views import FormViewSet, SubmissionViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'forms', FormViewSet, basename='form')
router.register(r'submissions', SubmissionViewSet, basename='submission')

urlpatterns = [
    path('', include(router.urls)),
]
