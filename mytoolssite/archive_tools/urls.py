# archive_tools/urls.py
from django.urls import path
from . import views

app_name = 'archive_tools'

urlpatterns = [
    path('zip-viewer/', views.zip_list_view, name='zip_viewer'),
    path('zip-extractor/', views.zip_extractor_view, name='zip_extractor'),
    path('zip-extractor/download/<path:internal_path>', views.download_zip_entry_view, name='download_zip_entry'),
    path('create-zip/', views.create_zip_view, name='create_zip'),

    path('rar-extractor/', views.rar_extractor_view, name='rar_extractor'),
    path('rar-extractor/download/<path:internal_path>', views.download_rar_entry_view, name='download_rar_entry'),
    # Add paths for other archive tools here later
]