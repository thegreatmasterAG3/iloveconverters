# converters/urls.py (Create this file)
from django.urls import path
from . import views # We will create views soon

# Define an app_name for namespacing URLs (good practice)
app_name = 'converters'

urlpatterns = [
    # Example URL for the JPG to PDF tool
    # We'll create the 'jpg_to_pdf_view' function later
    path('jpg-to-pdf/', views.jpg_to_pdf_view, name='jpg_to_pdf'),
    # Add paths for other converters here later
    # path('word-to-pdf/', views.word_to_pdf_view, name='word_to_pdf'),
]