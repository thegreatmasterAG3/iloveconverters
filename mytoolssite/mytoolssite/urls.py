"""
URL configuration for mytoolssite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings # Import settings
from django.conf.urls.static import static # Import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('convert/', include('converters.urls')),

    path('blog/', include('blog.urls', namespace='blog')),

    path('ai-news/', include('news.urls', namespace='news')),

    path('request-tool/', include('toolrequests.urls', namespace='toolrequests')),

    path('contact/', include('contact.urls', namespace='contact')),

    path('faq/', include('faq.urls', namespace='faq')),

    # --- NEW: Group tool apps under /tools/ ---
    path('tools/pdf/', include('pdf_tools.urls', namespace='pdf_tools')),
    
    path('tools/image/', include('image_tools.urls', namespace='image_tools')),

    path('tools/text/', include('text_tools.urls', namespace='text_tools')),

    path('tools/utility/', include('utility_tools.urls', namespace='utility_tools')),

    path('tools/archive/', include('archive_tools.urls', namespace='archive_tools')),

    path('tools/developer/', include('developer_tools.urls', namespace='developer_tools')),

    path('tools/audio/', include('audio_tools.urls', namespace='audio_tools')),
]




# Add this line at the end for development media serving
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)