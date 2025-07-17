# text_tools/urls.py
from django.urls import path
from . import views

app_name = 'text_tools'

urlpatterns = [
    path('word-counter/', views.word_count_view, name='word_counter'),
    path('case-converter/', views.case_converter_view, name='case_converter'),
    path('lorem-ipsum-generator/', views.lorem_ipsum_view, name='lorem_ipsum_generator'),
    path('reverse-text/', views.reverse_text_view, name='reverse_text'),
    path('remove-line-breaks/', views.remove_line_breaks_view, name='remove_line_breaks'),
    path('text-cleaner/', views.text_cleaner_view, name='text_cleaner'),
    path('text-compare/', views.text_compare_view, name='text_compare'),
    path('markdown-previewer/', views.markdown_previewer_view, name='markdown_previewer'),
    path('slug-generator/', views.slug_generator_view, name='slug_generator'),
    path('json-formatter/', views.json_formatter_view, name='json_formatter'),
    path('binary-converter/', views.binary_converter_view, name='binary_converter'),
    # Add paths for other text tools here later
]