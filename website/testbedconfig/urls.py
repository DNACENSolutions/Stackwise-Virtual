from django.urls import path
from . import views

urlpatterns = [
    path('saved-files', views.saved_files_view, name="saved-files"),
    path('testbed-preview', views.testbed_yaml_preview, name="testbed-preview"),
    path('testbed-file', views.testbed_file, name="testbed-file"),
    path('', views.form_view, name="testbed-config"),
]