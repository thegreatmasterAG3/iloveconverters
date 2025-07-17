# image_tools/urls.py
from django.urls import path
from . import views

app_name = 'image_tools'

urlpatterns = [
    path('png-to-jpg/', views.png_to_jpg_view, name='png_to_jpg'),
    path('resize-image/', views.resize_image_view, name='resize_image'),
    path('jpg-to-png/', views.jpg_to_png_view, name='jpg_to_png'),
    path('image-to-base64/', views.image_to_base64_view, name='image_to_base64'),
    path('compress-image/', views.compress_image_view, name='compress_image'),
    path('webp-to-png/', views.webp_to_png_view, name='webp_to_png'),
    path('webp-to-jpg/', views.webp_to_jpg_view, name='webp_to_jpg'),
    path('jpg-to-webp/', views.jpg_to_webp_view, name='jpg_to_webp'),
    path('ico-converter/', views.ico_converter_view, name='ico_converter'),
    path('rotate-image/', views.rotate_image_view, name='rotate_image'),
    path('add-watermark/', views.add_watermark_view, name='add_watermark'),
    path('image-color-picker/', views.image_color_picker_view, name='image_color_picker'),
    path('favicon-generator/', views.favicon_generator_view, name='favicon_generator'),
    path('remove-background/', views.remove_background_view, name='remove_background'),
]