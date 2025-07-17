# faq/views.py
from django.shortcuts import render
from .models import FAQItem

def faq_list_view(request):
    """Displays a list of active FAQ items."""
    faq_items = FAQItem.objects.filter(is_active=True).order_by('display_order', 'question') # Fetch active FAQs
    context = {
        'faq_items': faq_items,
        'page_title': 'Frequently Asked Questions (FAQ)'
    }
    return render(request, 'faq/faq_list.html', context)