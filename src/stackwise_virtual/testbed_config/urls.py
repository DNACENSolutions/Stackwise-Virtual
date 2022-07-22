from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', views.test_view, name="test"),
    path('yaml-view', views.yaml_view, name="yaml-view"),
    path('yaml-preview', views.yaml_preview, name="yaml-preview"),
    path('tests_view', views.tests_view, name="run-tests")
]