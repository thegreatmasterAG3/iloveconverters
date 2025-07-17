# faq/urls.py
from django.urls import path
from . import views

app_name = 'faq'

urlpatterns = [
    # URL for the main FAQ listing page
    path('', views.faq_list_view, name='faq_list'),
]