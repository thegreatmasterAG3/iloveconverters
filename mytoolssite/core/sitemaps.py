# core/sitemaps.py

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from blog.models import Post # Import your Post model

class StaticViewSitemap(Sitemap):
    """
    Sitemap for your static pages (homepage, categories, etc.).
    """
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        # Return a list of URL names for your static pages
        return [
            'core:home',
            'core:simple_tools_page',
            'core:ai_tools_page',
            'core:category_pdf',
            'core:category_image',
            'core:category_text',
            'core:category_audio',
            'core:category_video',
            'core:category_developer',
            'core:category_utility',
            'core:category_archive',
            'blog:post_list',
            'news:news_list',
            'toolrequests:request_form',
            'contact:contact_form',
            'faq:faq_list',
        ]

    def location(self, item):
        # For each item in the list above, this generates its URL
        return reverse(item)


# --- NEW SITEMAP CLASS FOR TOOLS ---
class ToolViewSitemap(Sitemap):
    """
    Sitemap for your individual tool pages.
    """
    changefreq = 'monthly' # Tools themselves don't change often
    priority = 0.9       # These are very important pages

    def items(self):
        # Return a list of all your specific tool URL names
        return [
            # PDF Tools
            'pdf_tools:jpg_to_pdf',
            'pdf_tools:merge_pdf',
            'pdf_tools:split_pdf',
            'pdf_tools:compress_pdf',
            'pdf_tools:rotate_pdf',
            'pdf_tools:pdf_to_png',
            'pdf_tools:pdf_to_jpg',
            'pdf_tools:png_to_pdf',
            'pdf_tools:pdf_to_word',
            'pdf_tools:pdf_to_excel',
            'pdf_tools:pdf_to_pptx',
            'pdf_tools:add_watermark',
            'pdf_tools:protect_pdf',
            'pdf_tools:unlock_pdf',

            # Image Tools
            'image_tools:png_to_jpg',
            'image_tools:resize_image',
            'image_tools:jpg_to_png',
            'image_tools:image_to_base64',
            'image_tools:compress_image',
            'image_tools:webp_to_png',
            'image_tools:webp_to_jpg',
            'image_tools:jpg_to_webp',
            'image_tools:ico_converter',
            'image_tools:rotate_image',
            'image_tools:image_color_picker',
            'image_tools:favicon_generator',
            'image_tools:remove_background',

            # Text Tools
            'text_tools:word_counter',
            'text_tools:case_converter',
            'text_tools:lorem_ipsum_generator',
            'text_tools:reverse_text',
            'text_tools:remove_line_breaks',
            'text_tools:text_cleaner',
            'text_tools:text_compare',
            'text_tools:markdown_previewer',
            'text_tools:slug_generator',
            'text_tools:json_formatter',
            'text_tools:binary_converter',

            # Utility Tools
            'utility_tools:qr_code_generator',
            'utility_tools:uuid_generator',
            'utility_tools:hash_generator',
            'utility_tools:url_encoder_decoder',
            'utility_tools:base64_encoder_decoder',
            'utility_tools:unit_converter',
            'utility_tools:color_converter',
            'utility_tools:barcode_generator',
            'utility_tools:password_generator',
            'utility_tools:timestamp_converter',
            'utility_tools:css_gradient_generator',
            'utility_tools:timezone_converter',
            'utility_tools:random_number_generator',
            'utility_tools:calculator',
            'utility_tools:whats_my_ip',
            'utility_tools:screen_resolution',

            # Archive Tools
            'archive_tools:zip_viewer',
            'archive_tools:zip_extractor',
            'archive_tools:create_zip',
            'archive_tools:rar_extractor',

            # Developer Tools
            'developer_tools:xml_formatter',
            'developer_tools:regex_tester',

            # Audio Tools
            'audio_tools:live_speech_to_text',
        ]

    def location(self, item):
        # This function works the same as in the StaticViewSitemap
        return reverse(item)
# --- END NEW SITEMAP CLASS ---


class PostSitemap(Sitemap):
    """
    Sitemap for your dynamic blog posts.
    """
    changefreq = 'monthly'
    priority = 0.7

    def items(self):
        # Return the queryset of all Post objects you want in the sitemap
        return Post.objects.all() # You can filter this later (e.g., for published posts)

    def lastmod(self, obj):
        # Return the last modified date for each post
        return obj.updated_date