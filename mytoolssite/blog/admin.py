# blog/admin.py
from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'author', 'published_date') # Fields to show in list view
    list_filter = ('published_date', 'author') # Filters in the sidebar
    search_fields = ('title', 'content') # Fields to search by
    prepopulated_fields = {'slug': ('title',)} # Auto-fill slug based on title
    date_hierarchy = 'published_date' # Add date navigation
    ordering = ('-published_date',) # Order in admin view