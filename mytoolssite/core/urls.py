# core/urls.py (Create this file)
from django.urls import path
from . import views # Import views from the current directory

urlpatterns = [
    # When someone visits the root path (''), use the 'home' view
    path('', views.home, name='home'),
    path('simple-tools/', views.simple_tools_page, name='simple_tools_page'),
    path('ai-tools/', views.ai_tools_page, name='ai_tools_page'),
    # Using a 'tools/' prefix for organization
    path('tools/pdf/', views.category_pdf_page, name='category_pdf'),
    path('tools/image/', views.category_image_page, name='category_image'),
    path('tools/text/', views.category_text_page, name='category_text'),
    path('tools/audio/', views.category_audio_page, name='category_audio'),
    path('tools/video/', views.category_video_page, name='category_video'),
    path('tools/developer/', views.category_developer_page, name='category_developer'),
    path('tools/utilities/', views.category_utility_page, name='category_utility'),
    path('tools/archive/', views.category_archive_page, name='category_archive'),


]