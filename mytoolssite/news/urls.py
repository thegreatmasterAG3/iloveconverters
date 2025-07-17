# news/urls.py
from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    # This will be the view for '/ai-news/'
    path('', views.news_list, name='news_list'),
]