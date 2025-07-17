# contact/urls.py
from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    # URL for the contact form page
    path('', views.contact_view, name='contact_form'),
]