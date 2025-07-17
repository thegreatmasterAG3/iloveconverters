# news/views.py
from django.shortcuts import render
from .models import NewsItem

def news_list(request):
    """Displays a list of curated AI news items."""
    news_items = NewsItem.objects.all() # Already ordered by Meta
    context = {
        'news_items': news_items,
        'page_title': 'Latest AI News & Articles'
    }
    return render(request, 'news/news_list.html', context)