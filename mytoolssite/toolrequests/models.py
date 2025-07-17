# toolrequests/models.py
from django.db import models
from django.utils import timezone

class ToolRequest(models.Model):
    tool_name = models.CharField(max_length=150, help_text="Name or idea for the tool")
    description = models.TextField(help_text="Describe what the tool should do, its features, etc.")
    requester_email = models.EmailField(blank=True, null=True, help_text="(Optional) Provide your email if you'd like an update.")
    requested_date = models.DateTimeField(default=timezone.now)
    # You could add a status later (e.g., Pending, Considered, Implemented, Rejected)
    # status = models.CharField(max_length=20, default='Pending')

    class Meta:
        ordering = ['-requested_date']
        verbose_name = "Tool Request"
        verbose_name_plural = "Tool Requests"

    def __str__(self):
        return self.tool_name