# audio_tools/urls.py
from django.urls import path
from . import views

app_name = 'audio_tools'

urlpatterns = [
    path('live-speech-to-text/', views.live_speech_to_text_view, name='live_speech_to_text'),
    # path('cut-audio/', views.cut_audio_view, name='cut_audio'),
    # Add paths for other audio tools here later
]