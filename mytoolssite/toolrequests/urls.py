# toolrequests/urls.py
from django.urls import path
from . import views

app_name = 'toolrequests'

urlpatterns = [
    # URL for the request form page
    path('', views.request_tool_view, name='request_form'),
]