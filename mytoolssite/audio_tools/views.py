# audio_tools/views.py
from django.shortcuts import render

def live_speech_to_text_view(request):
    """Displays the live speech-to-text tool page."""
    context = {
        'page_title': 'Live Speech to Text (Dictation)',
        # Add browser compatibility note
        'browser_note': 'This tool relies on browser features primarily available in Chrome and Edge.'
    }
    return render(request, 'audio_tools/tool_live_speech_to_text.html', context)