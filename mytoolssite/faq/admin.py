# faq/admin.py
from django.contrib import admin
from .models import FAQItem

@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ('question', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active') # Allow editing these directly in the list
    search_fields = ('question', 'answer')
    list_filter = ('is_active',)
    ordering = ('display_order', 'question')