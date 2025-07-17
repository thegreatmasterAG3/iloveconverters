# developer_tools/urls.py
from django.urls import path
from . import views

app_name = 'developer_tools'

urlpatterns = [
    path('xml-formatter/', views.xml_formatter_view, name='xml_formatter'),
    path('regex-tester/', views.regex_tester_view, name='regex_tester'),
    # Add paths for other developer tools here later
]