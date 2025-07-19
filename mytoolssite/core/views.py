# core/views.py
from django.shortcuts import render

# --- Existing Views ---
def home(request):
    return render(request, 'core/home.html')

def about_page(request):
    """Renders the About Us page."""
    context = {'page_title': 'About Us'}
    return render(request, 'core/about_page.html', context)

def simple_tools_page(request):
    context = {'page_title': 'Simple Online Tools'}
    return render(request, 'core/simple_tools.html', context)

def ai_tools_page(request):
    context = {'page_title': 'AI-Powered Tools'}
    return render(request, 'core/ai_tools.html', context)

# --- NEW CATEGORY VIEWS ---
def category_pdf_page(request):
    """Renders the page listing only PDF tools."""
    context = {'page_title': 'PDF Tools'}
    return render(request, 'core/category_pdf.html', context)

def category_image_page(request):
    """Renders the page listing only Image tools."""
    context = {'page_title': 'Image Tools'}
    return render(request, 'core/category_image.html', context)

def category_text_page(request):
    """Renders the page listing only Text tools."""
    context = {'page_title': 'Text Tools'}
    return render(request, 'core/category_text.html', context)

def category_audio_page(request):
    """Renders the page listing only Audio tools."""
    context = {'page_title': 'Audio Tools'}
    return render(request, 'core/category_audio.html', context)

def category_video_page(request):
    """Renders the page listing only Video tools."""
    context = {'page_title': 'Video Tools'}
    return render(request, 'core/category_video.html', context)

def category_developer_page(request):
    """Renders the page listing only Developer tools."""
    context = {'page_title': 'Developer Tools'}
    return render(request, 'core/category_developer.html', context)

def category_utility_page(request):
    """Renders the page listing only Utilities tools."""
    context = {'page_title': 'Utilitiy Tools'}
    return render(request, 'core/category_utility.html', context)

def category_archive_page(request):
    """Renders the page listing only Archive tools."""
    context = {'page_title': 'Archive Tools'}
    return render(request, 'core/category_archive.html', context)

# --- END NEW CATEGORY VIEWS ---