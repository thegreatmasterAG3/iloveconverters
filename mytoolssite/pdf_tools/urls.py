# pdf_tools/urls.py
from django.urls import path
from . import views # We will create the view shortly

app_name = 'pdf_tools'

urlpatterns = [
    # URL for JPG to PDF tool - view name will be 'jpg_to_pdf_view'
    path('jpg-to-pdf/', views.jpg_to_pdf_view, name='jpg_to_pdf'),
    path('merge-pdf/', views.merge_pdf_view, name='merge_pdf'),
    path('split-pdf/', views.split_pdf_view, name='split_pdf'),
    path('compress-pdf/', views.compress_pdf_view, name='compress_pdf'),
    path('rotate-pdf/', views.rotate_pdf_view, name='rotate_pdf'),
    path('pdf-to-png/', views.pdf_to_png_view, name='pdf_to_png'),
    path('pdf-to-jpg/', views.pdf_to_jpg_view, name='pdf_to_jpg'),
    path('png-to-pdf/', views.png_to_pdf_view, name='png_to_pdf'),
    path('pdf-to-word/', views.pdf_to_word_view, name='pdf_to_word'),
    path('pdf-to-excel/', views.pdf_to_excel_view, name='pdf_to_excel'),
    path('pdf-to-powerpoint/', views.pdf_to_pptx_view, name='pdf_to_pptx'),
    path('add-watermark/', views.watermark_pdf_view, name='add_watermark'),
    path('protect-pdf/', views.protect_pdf_view, name='protect_pdf'),
    path('unlock-pdf/', views.unlock_pdf_view, name='unlock_pdf'),
]