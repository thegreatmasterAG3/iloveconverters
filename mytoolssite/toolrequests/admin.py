# toolrequests/admin.py
from django.contrib import admin
from .models import ToolRequest

@admin.register(ToolRequest)
class ToolRequestAdmin(admin.ModelAdmin):
    list_display = ('tool_name', 'requester_email', 'requested_date')
    list_filter = ('requested_date',)
    search_fields = ('tool_name', 'description', 'requester_email')
    readonly_fields = ('requested_date',) # Don't allow editing the submission date