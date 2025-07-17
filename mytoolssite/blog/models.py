# blog/models.py
from django.db import models
from django.conf import settings # To get the User model
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone # For default date

class Post(models.Model):
    # Basic Fields
    title = models.CharField(max_length=200)
    # unique=True ensures no two posts have the same slug
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE # Or models.SET_NULL if posts can exist without author
    )
    content = models.TextField()
    published_date = models.DateTimeField(default=timezone.now)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    # Add status later if needed (e.g., Draft, Published)
    # status = models.CharField(max_length=10, choices=[('draft', 'Draft'), ('published', 'Published')], default='draft')

    class Meta:
        ordering = ['-published_date'] # Default order: newest first

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate slug from title if it's blank
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure slug is unique if auto-generated
            original_slug = self.slug
            counter = 1
            while Post.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs) # Call the "real" save() method.

    def get_absolute_url(self):
        # Generates the URL for a single post instance
        return reverse('blog:post_detail', kwargs={'slug': self.slug})