# blog/urls.py
from django.urls import path
from . import views

app_name = 'blog' # Namespace for URLs

urlpatterns = [
    # Example: /blog/
    path('', views.post_list, name='post_list'),
    # Example: /blog/my-first-post/
    path('<slug:slug>/', views.post_detail, name='post_detail'),
]