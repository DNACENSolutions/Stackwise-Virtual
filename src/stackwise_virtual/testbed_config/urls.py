from django.urls import path
from . import views

urlpatterns = [
    path('', views.test_view, name="test"),
    path('yaml-preview', views.yaml_view, name="yaml-preview")
]