# contact/models.py
from django.db import models
from django.utils import timezone

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    submitted_date = models.DateTimeField(default=timezone.now)
    responded = models.BooleanField(default=False, help_text="Check if someone has responded to this message")

    class Meta:
        ordering = ['-submitted_date']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"