# utility_tools/urls.py
from django.urls import path
from . import views

app_name = 'utility_tools'

urlpatterns = [
    path('qr-code-generator/', views.qr_code_view, name='qr_code_generator'),
    path('uuid-generator/', views.uuid_generator_view, name='uuid_generator'),
    path('hash-generator/', views.hash_generator_view, name='hash_generator'),
    path('url-encoder-decoder/', views.url_encode_decode_view, name='url_encoder_decoder'),
    path('base64-encoder-decoder/', views.base64_view, name='base64_encoder_decoder'),
    path('unit-converter/', views.unit_converter_view, name='unit_converter'),
    path('color-converter/', views.color_converter_view, name='color_converter'),
    path('barcode-generator/', views.barcode_generator_view, name='barcode_generator'),
    path('password-generator/', views.password_generator_view, name='password_generator'),
    path('timestamp-converter/', views.timestamp_converter_view, name='timestamp_converter'),
    path('css-gradient-generator/', views.gradient_generator_view, name='css_gradient_generator'),
    path('timezone-converter/', views.timezone_converter_view, name='timezone_converter'),
    path('random-number-generator/', views.random_number_view, name='random_number_generator'),
    path('calculator/', views.calculator_view, name='calculator'),
    path('whats-my-ip/', views.whats_my_ip_view, name='whats_my_ip'),
    path('screen-resolution/', views.screen_resolution_view, name='screen_resolution'),

    # Add paths for other utility tools here later
]