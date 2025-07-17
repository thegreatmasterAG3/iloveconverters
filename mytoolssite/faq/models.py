# faq/models.py
from django.db import models

class FAQItem(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    # Optional field to control the order FAQs appear in
    display_order = models.PositiveIntegerField(default=0, help_text="FAQs will be ordered by this number, lowest first.")
    # Optional: Add category later if you have many FAQs
    # category = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Only active FAQs will be displayed.")

    class Meta:
        ordering = ['display_order', 'question'] # Order by display_order, then question
        verbose_name = "FAQ Item"
        verbose_name_plural = "FAQ Items"

    def __str__(self):
        return self.question