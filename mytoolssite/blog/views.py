# blog/views.py
from django.shortcuts import render, get_object_or_404
from .models import Post

def post_list(request):
    """Displays a list of published blog posts."""
    # Add filtering for published status later if needed
    posts = Post.objects.all().order_by('-published_date') # Fetch all for now
    context = {
        'posts': posts,
        'page_title': 'Blog'
    }
    return render(request, 'blog/post_list.html', context)

def post_detail(request, slug):
    """Displays a single blog post."""
    # Add filtering for published status later if needed
    post = get_object_or_404(Post, slug=slug) # Fetch specific post by slug
    context = {
        'post': post,
        'page_title': post.title # Use post title for page title
    }
    return render(request, 'blog/post_detail.html', context)