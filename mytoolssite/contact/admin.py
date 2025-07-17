# contact/admin.py
from django.contrib import admin
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'submitted_date', 'responded')
    list_filter = ('submitted_date', 'responded')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'subject', 'message', 'submitted_date') # Make content read-only, only toggle 'responded'
    list_editable = ('responded',) # Allow quick toggling of 'responded' in list view