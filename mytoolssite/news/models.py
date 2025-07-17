# news/models.py
from django.db import models
from django.utils import timezone

class NewsItem(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField(max_length=500) # URL to the actual news article
    source_name = models.CharField(max_length=100, blank=True, help_text="e.g., TechCrunch, OpenAI Blog") # Name of the source website
    published_date = models.DateField(default=timezone.now, db_index=True) # Date the news was published or added
    added_date = models.DateTimeField(auto_now_add=True) # When we added it

    class Meta:
        ordering = ['-published_date', '-added_date'] # Show newest first
        verbose_name = "AI News Item"
        verbose_name_plural = "AI News Items"

    def __str__(self):
        return self.title

    # Optional: Helper to try and get base domain (can be tricky)
    # from urllib.parse import urlparse
    # def get_source_domain(self):
    #     try:
    #         return urlparse(self.url).netloc.replace('www.', '')
    #     except:
    #          return None