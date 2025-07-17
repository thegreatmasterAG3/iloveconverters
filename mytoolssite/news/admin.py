# news/admin.py
from django.contrib import admin
from .models import NewsItem

@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'source_name', 'published_date', 'url')
    list_filter = ('published_date', 'source_name')
    search_fields = ('title', 'source_name', 'url')
    date_hierarchy = 'published_date'
    ordering = ('-published_date',)