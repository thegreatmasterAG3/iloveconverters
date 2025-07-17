# image_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .png_to_jpg_converter import convert_png_to_jpg # Import the logic
import os
import base64

MAX_UPLOAD_SIZE = 20 * 1024 * 1024 # 20 MB
ALLOWED_EXTENSIONS = ['.png']

def png_to_jpg_view(request):
    # Clear previous data from session
    if request.method == 'GET' or 'pngfile' in request.FILES: # Check specific input name
        if 'jpg_data_b64' in request.session: del request.session['jpg_data_b64']
        if 'jpg_filename' in request.session: del request.session['jpg_filename']

    if request.method == 'POST':
        # Check if download button was clicked
        if 'download_jpg' in request.POST:
             jpg_data_b64 = request.session.get('jpg_data_b64')
             jpg_filename = request.session.get('jpg_filename', 'converted.jpg')
             if jpg_data_b64:
                 try:
                     jpg_data = base64.b64decode(jpg_data_b64.encode('ascii'))
                     response = HttpResponse(jpg_data, content_type='image/jpeg')
                     response['Content-Disposition'] = f'attachment; filename="{jpg_filename}"'
                     del request.session['jpg_data_b64']
                     del request.session['jpg_filename']
                     return response
                 except Exception as e:
                     print(f"Error decoding/serving JPG from session: {e}")
                     messages.error(request, "Could not retrieve generated JPG.")
             else:
                 messages.error(request, "No generated JPG found to download.")
             return redirect('image_tools:png_to_jpg')

        # --- Handle Conversion ---
        else:
            uploaded_file = request.FILES.get('pngfile') # Use get for single file
            try:
                 # Clamp quality between 1 and 95
                quality = max(1, min(95, int(request.POST.get('quality', '90'))))
            except ValueError:
                quality = 90 # Default quality

            # Background color (default white) - more robust parsing needed for hex
            bg_color_str = request.POST.get('bg_color', 'ffffff').lstrip('#')
            try:
                # Convert hex string to RGB tuple
                bg_color_rgb = tuple(int(bg_color_str[i:i+2], 16) for i in (0, 2, 4))
                if len(bg_color_rgb) != 3: raise ValueError("Invalid hex length")
            except (ValueError, TypeError):
                bg_color_rgb = (255, 255, 255) # Default white on error

            # --- Validation ---
            if not uploaded_file:
                messages.error(request, "No file was uploaded.")
                return redirect('image_tools:png_to_jpg')

            if uploaded_file.size > MAX_UPLOAD_SIZE:
                 messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
                 return redirect('image_tools:png_to_jpg')

            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                messages.error(request, f"Invalid file type '{ext}'. Only PNG files allowed.")
                return redirect('image_tools:png_to_jpg')

            if uploaded_file.content_type != 'image/png':
                 messages.warning(request, f"File might not be a valid PNG (MIME type: {uploaded_file.content_type}).")
            # --- End Validation ---

            # --- Conversion ---
            print(f"Converting {uploaded_file.name} with Quality={quality}, BG={bg_color_rgb}")
            jpg_data = convert_png_to_jpg(
                png_file=uploaded_file,
                background_color=bg_color_rgb,
                quality=quality
            )
            # --- End Conversion ---

            context = { 'page_title': 'Convert PNG to JPG' } # Basic context

            if jpg_data:
                print("PNG>JPG Conversion successful, storing JPG in session.")
                jpg_data_b64 = base64.b64encode(jpg_data).decode('ascii')
                request.session['jpg_data_b64'] = jpg_data_b64
                # Create output filename
                base_filename = os.path.splitext(uploaded_file.name)[0]
                filename = f"{base_filename}.jpg"
                request.session['jpg_filename'] = filename

                context['conversion_success'] = True
                context['download_filename'] = filename
                messages.success(request, "Conversion Successful!")

            else:
                print("PNG>JPG Conversion function returned None.")
                context['conversion_success'] = False
                messages.error(request, "Failed to convert PNG to JPG. File might be corrupted.")

            return render(request, 'image_tools/tool_png_to_jpg.html', context)

    # --- GET Request Handling ---
    else:
        context = { 'page_title': 'Convert PNG to JPG' }
        return render(request, 'image_tools/tool_png_to_jpg.html', context)
    


# image_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .png_to_jpg_converter import convert_png_to_jpg
# --- NEW IMPORT ---
from .resize_image_logic import resize_image
# --- END NEW IMPORT ---
import os
import base64

MAX_UPLOAD_SIZE = 20 * 1024 * 1024 # 20 MB
# Allowed input image types for resizing
ALLOWED_RESIZE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff']
ALLOWED_RESIZE_MIMES = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/gif', 'image/tiff']



# --- NEW VIEW for Image Resizer ---
def resize_image_view(request):
    # Clear previous data from session
    if request.method == 'GET' or 'imagefile' in request.FILES:
        if 'resized_data_b64' in request.session: del request.session['resized_data_b64']
        if 'resized_filename' in request.session: del request.session['resized_filename']

    if request.method == 'POST':
        # Handle Download Request
        if 'download_resized' in request.POST:
             resized_data_b64 = request.session.get('resized_data_b64')
             resized_filename = request.session.get('resized_filename', 'resized_image.jpg') # Default extension might vary
             if resized_data_b64:
                 try:
                     image_data = base64.b64decode(resized_data_b64.encode('ascii'))
                     # Determine content type from filename extension
                     ext = os.path.splitext(resized_filename)[1].lower()
                     content_type = {
                         '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                         '.png': 'image/png', '.webp': 'image/webp',
                         '.gif': 'image/gif', '.bmp': 'image/bmp',
                         '.tiff': 'image/tiff'
                     }.get(ext, 'application/octet-stream') # Fallback

                     response = HttpResponse(image_data, content_type=content_type)
                     response['Content-Disposition'] = f'attachment; filename="{resized_filename}"'
                     del request.session['resized_data_b64']
                     del request.session['resized_filename']
                     return response
                 except Exception as e:
                     print(f"Error decoding/serving resized image from session: {e}")
                     messages.error(request, "Could not retrieve the resized image.")
             else:
                 messages.error(request, "No resized image found to download.")
             return redirect('image_tools:resize_image')

        # --- Handle Resize Request ---
        else:
            uploaded_file = request.FILES.get('imagefile') # Single file input

            # --- Get Options ---
            resize_mode = request.POST.get('resize_mode', 'pixels')
            aspect_ratio = request.POST.get('aspect_ratio', 'on') == 'on' # Checkbox value
            output_format = request.POST.get('output_format', 'ORIGINAL')
            quality = 90 # Default

            target_width = None
            target_height = None
            percentage = 100 # Default

            try:
                if resize_mode == 'pixels':
                    w_str = request.POST.get('target_width', '').strip()
                    h_str = request.POST.get('target_height', '').strip()
                    if w_str: target_width = int(w_str)
                    if h_str: target_height = int(h_str)
                    if target_width is None and target_height is None:
                        raise ValueError("Width or Height required for pixel mode.")
                elif resize_mode == 'percentage':
                    p_str = request.POST.get('percentage', '100').strip()
                    percentage = int(p_str)
                    if percentage <= 0: raise ValueError("Percentage must be positive.")

                q_str = request.POST.get('quality', '90').strip()
                quality = max(1, min(95, int(q_str))) # Clamp JPEG/WebP quality

            except ValueError as e:
                messages.error(request, f"Invalid input value: {e}")
                return redirect('image_tools:resize_image')

            # --- Validation ---
            if not uploaded_file:
                messages.error(request, "No file was uploaded.")
                return redirect('image_tools:resize_image')
            if uploaded_file.size > MAX_UPLOAD_SIZE:
                 messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
                 return redirect('image_tools:resize_image')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_RESIZE_EXTENSIONS:
                messages.error(request, f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_RESIZE_EXTENSIONS)}")
                return redirect('image_tools:resize_image')
            if uploaded_file.content_type not in ALLOWED_RESIZE_MIMES:
                 messages.warning(request, f"File type might be incorrect (MIME type: {uploaded_file.content_type}).")
            # --- End Validation ---

            # --- Conversion ---
            print(f"Resizing {uploaded_file.name}. Mode: {resize_mode}, W: {target_width}, H: {target_height}, %: {percentage}, Aspect: {aspect_ratio}, Format: {output_format}, Q: {quality}")
            resized_data, output_filename = resize_image(
                image_file=uploaded_file,
                resize_mode=resize_mode,
                target_width=target_width,
                target_height=target_height,
                percentage=percentage,
                maintain_aspect_ratio=aspect_ratio,
                output_format=output_format,
                jpeg_quality=quality
            )
            # --- End Conversion ---

            context = { 'page_title': 'Resize Image' }

            if resized_data and output_filename:
                print("Resize successful, storing image in session.")
                resized_data_b64 = base64.b64encode(resized_data).decode('ascii')
                request.session['resized_data_b64'] = resized_data_b64
                request.session['resized_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                messages.success(request, "Resizing Successful!")
            else:
                print("Resize function returned None.")
                context['conversion_success'] = False
                messages.error(request, "Failed to resize image. File might be corrupted or invalid.")

            # Store previous options to repopulate form slightly better
            context['prev_options'] = request.POST
            return render(request, 'image_tools/tool_resize_image.html', context)

    # --- GET Request Handling ---
    else:
        context = { 'page_title': 'Resize Image' }
        return render(request, 'image_tools/tool_resize_image.html', context)
    





# image_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .png_to_jpg_converter import convert_png_to_jpg
from .resize_image_logic import resize_image
from .jpg_to_png_converter import convert_jpg_to_png # Keep this import
import os
import base64

MAX_UPLOAD_SIZE = 20 * 1024 * 1024
# ... (Keep other ALLOWED constants) ...
ALLOWED_JPG_EXTENSIONS = ['.jpg', '.jpeg']
ALLOWED_JPG_MIMES = ['image/jpeg', 'image/jpg']



# --- UPDATED jpg_to_png_view ---
def jpg_to_png_view(request):
    # Clear session data
    if request.method == 'GET' or 'jpgfile' in request.FILES:
        if 'png_data_b64' in request.session: del request.session['png_data_b64']
        if 'png_filename' in request.session: del request.session['png_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_png' in request.POST:
            # ... (Download logic remains the same as before) ...
             png_data_b64 = request.session.get('png_data_b64')
             png_filename = request.session.get('png_filename', 'converted.png')
             if png_data_b64:
                 try:
                     png_data = base64.b64decode(png_data_b64.encode('ascii'))
                     response = HttpResponse(png_data, content_type='image/png')
                     response['Content-Disposition'] = f'attachment; filename="{png_filename}"'
                     del request.session['png_data_b64']
                     del request.session['png_filename']
                     return response
                 except Exception as e:
                     print(f"Error decoding/serving PNG from session: {e}")
                     messages.error(request, "Could not retrieve generated PNG.")
             else:
                 messages.error(request, "No generated PNG found to download.")
             return redirect('image_tools:jpg_to_png')

        # Handle Conversion
        else:
            uploaded_file = request.FILES.get('jpgfile')

            # --- Get Options ---
            try:
                # Clamp compression level between 0 and 9
                compression = max(0, min(9, int(request.POST.get('compression', '6'))))
            except ValueError:
                compression = 6 # Default compression
            # Get interlace option (checkbox value is 'on' if checked)
            interlace = request.POST.get('interlace', 'off') == 'on'
            # --- End Get Options ---


            # --- Validation (Keep as before) ---
            if not uploaded_file:
                messages.error(request, "No file was uploaded.")
                return redirect('image_tools:jpg_to_png')
            if uploaded_file.size > MAX_UPLOAD_SIZE:
                 messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
                 return redirect('image_tools:jpg_to_png')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_JPG_EXTENSIONS:
                messages.error(request, f"Invalid file type '{ext}'. Only JPG/JPEG files allowed.")
                return redirect('image_tools:jpg_to_png')
            if uploaded_file.content_type not in ALLOWED_JPG_MIMES:
                 messages.warning(request, f"File might not be a valid JPG (MIME type: {uploaded_file.content_type}).")
            # --- End Validation ---


            # --- Conversion (Pass options) ---
            print(f"Converting {uploaded_file.name} from JPG to PNG with Compression={compression}, Interlace={interlace}")
            png_data, output_filename = convert_jpg_to_png(
                jpg_file=uploaded_file,
                compression=compression,
                interlace=interlace
            )
            # --- End Conversion ---

            context = { 'page_title': 'Convert JPG to PNG' }

            if png_data and output_filename:
                print("JPG>PNG Conversion successful, storing PNG in session.")
                png_data_b64 = base64.b64encode(png_data).decode('ascii')
                request.session['png_data_b64'] = png_data_b64
                request.session['png_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                messages.success(request, "Conversion Successful!")

            else:
                print("JPG>PNG Conversion function returned None.")
                context['conversion_success'] = False
                messages.error(request, "Failed to convert JPG to PNG. File might be corrupted.")

            # Store previous options for repopulation if needed (less critical here)
            context['prev_options'] = request.POST
            return render(request, 'image_tools/tool_jpg_to_png.html', context)

    # --- GET Request Handling ---
    else:
        context = { 'page_title': 'Convert JPG to PNG' }
        return render(request, 'image_tools/tool_jpg_to_png.html', context)
    




# image_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
# ... other imports ...
# --- NEW IMPORT ---
from .image_to_base64_logic import convert_image_to_base64
# --- END NEW IMPORT ---
import os
import base64

MAX_UPLOAD_SIZE = 20 * 1024 * 1024 # 20 MB
# Allowed input types for Base64 encoding
ALLOWED_B64_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.svg']
ALLOWED_B64_MIMES = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/gif', 'image/tiff', 'image/svg+xml']



# --- NEW VIEW for Image to Base64 ---
def image_to_base64_view(request):
    context = { 'page_title': 'Image to Base64 Converter' }

    if request.method == 'POST':
        uploaded_file = request.FILES.get('imagefile_b64') # Unique name for file input

        # --- Get Options ---
        use_data_uri = request.POST.get('data_uri_format', 'on') == 'on' # Default ON
        line_breaks = request.POST.get('line_breaks', 'off') == 'on' # Default OFF

        # --- Validation ---
        if not uploaded_file:
            messages.error(request, "No file was uploaded.")
            return render(request, 'image_tools/tool_image_to_base64.html', context)

        if uploaded_file.size > MAX_UPLOAD_SIZE:
             messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
             return render(request, 'image_tools/tool_image_to_base64.html', context)

        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in ALLOWED_B64_EXTENSIONS:
            messages.error(request, f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_B64_EXTENSIONS)}")
            return render(request, 'image_tools/tool_image_to_base64.html', context)

        # MIME check is less critical here, mimetypes library will handle guessing
        # if uploaded_file.content_type not in ALLOWED_B64_MIMES:
        #      messages.warning(request, f"File type might be incorrect (MIME type: {uploaded_file.content_type}).")
        # --- End Validation ---

        # --- Conversion ---
        print(f"Converting {uploaded_file.name} to Base64. Data URI: {use_data_uri}, Line Breaks: {line_breaks}")
        base64_string = convert_image_to_base64(
            image_file=uploaded_file,
            use_data_uri=use_data_uri,
            line_breaks=line_breaks
        )
        # --- End Conversion ---

        if base64_string:
            print("Base64 Conversion successful.")
            context['conversion_success'] = True
            context['base64_string'] = base64_string
            context['original_filename'] = uploaded_file.name
            messages.success(request, "Image successfully converted to Base64!")
        else:
            print("Base64 Conversion function returned None.")
            context['conversion_success'] = False
            messages.error(request, "Failed to convert image to Base64. File might be corrupted.")

        # Store previous options for repopulation
        context['prev_options'] = request.POST
        # Re-render the same page with results/errors
        return render(request, 'image_tools/tool_image_to_base64.html', context)

    # --- GET Request Handling ---
    else:
        # Just display the form
        return render(request, 'image_tools/tool_image_to_base64.html', context)
    




# image_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .png_to_jpg_converter import convert_png_to_jpg
from .resize_image_logic import resize_image
from .jpg_to_png_converter import convert_jpg_to_png
from .image_to_base64_logic import convert_image_to_base64
# --- NEW IMPORT ---
from .compress_image_logic import compress_image_file
# --- END NEW IMPORT ---
import os
import base64

MAX_UPLOAD_SIZE = 20 * 1024 * 1024 # 20 MB
# Allowed input image types for compression (adjust as needed)
ALLOWED_COMPRESS_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
ALLOWED_COMPRESS_MIMES = ['image/jpeg', 'image/png', 'image/webp']



# image_tools/views.py
# ... (keep imports and other views) ...

def compress_image_view(request):
    # Clear previous data
    if request.method == 'GET' or 'imagefile_compress' in request.FILES:
        if 'compressed_data_b64' in request.session: del request.session['compressed_data_b64']
        if 'compressed_filename' in request.session: del request.session['compressed_filename']
        if 'original_size' in request.session: del request.session['original_size']
        # Clear calculated results too
        if 'compressed_size' in request.session: del request.session['compressed_size']
        if 'size_reduction_percent' in request.session: del request.session['size_reduction_percent']

    if request.method == 'POST':
        # Handle Download
        if 'download_compressed' in request.POST:
            # ... (Download logic remains the same) ...
             compressed_data_b64 = request.session.get('compressed_data_b64')
             compressed_filename = request.session.get('compressed_filename', 'compressed_image.jpg')
             if compressed_data_b64:
                 try:
                     image_data = base64.b64decode(compressed_data_b64.encode('ascii'))
                     ext = os.path.splitext(compressed_filename)[1].lower()
                     content_type = {'jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}.get(ext, 'application/octet-stream')
                     response = HttpResponse(image_data, content_type=content_type)
                     response['Content-Disposition'] = f'attachment; filename="{compressed_filename}"'
                     # Clean up session
                     if 'compressed_data_b64' in request.session: del request.session['compressed_data_b64']
                     if 'compressed_filename' in request.session: del request.session['compressed_filename']
                     if 'original_size' in request.session: del request.session['original_size']
                     if 'compressed_size' in request.session: del request.session['compressed_size']
                     if 'size_reduction_percent' in request.session: del request.session['size_reduction_percent']
                     return response
                 except Exception as e:
                     messages.error(request, "Could not retrieve compressed image.")
             else:
                 messages.error(request, "No compressed image found to download.")
             return redirect('image_tools:compress_image')

        # --- Handle Compression ---
        else:
            uploaded_file = request.FILES.get('imagefile_compress')
            try: quality = max(1, min(95, int(request.POST.get('quality', '75'))))
            except ValueError: quality = 75

            # --- Validation (Keep as before) ---
            if not uploaded_file: # ... etc ...
                messages.error(request, "No file uploaded.")
                return redirect('image_tools:compress_image')
            if uploaded_file.size > MAX_UPLOAD_SIZE: # ... etc ...
                 messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
                 return redirect('image_tools:compress_image')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_COMPRESS_EXTENSIONS: # ... etc ...
                messages.error(request, f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_COMPRESS_EXTENSIONS)}")
                return redirect('image_tools:compress_image')
            original_size = uploaded_file.size
            # --- End Validation ---

            # --- Compression ---
            print(f"Compressing {uploaded_file.name} with Quality={quality}")
            compressed_data, output_filename = compress_image_file(
                image_file=uploaded_file,
                quality=quality
            )
            # --- End Compression ---

            context = { 'page_title': 'Compress Image' }

            if compressed_data and output_filename:
                print("Compression successful, storing image in session.")
                compressed_data_b64 = base64.b64encode(compressed_data).decode('ascii')
                compressed_size = len(compressed_data)

                request.session['compressed_data_b64'] = compressed_data_b64
                request.session['compressed_filename'] = output_filename
                request.session['original_size'] = original_size
                request.session['compressed_size'] = compressed_size # Store compressed size

                # --- Calculate Reduction Percentage ---
                size_reduction_percent = 0
                if original_size > 0: # Avoid division by zero
                    reduction = original_size - compressed_size
                    if reduction > 0: # Only show positive reduction
                       size_reduction_percent = round((reduction / original_size) * 100)
                request.session['size_reduction_percent'] = size_reduction_percent # Store percentage
                # --- End Calculation ---

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_size'] = original_size
                context['compressed_size'] = compressed_size
                context['size_reduction_percent'] = size_reduction_percent # Pass to template
                messages.success(request, "Compression Successful!")
            else:
                print("Compression function returned None.")
                context['conversion_success'] = False
                messages.error(request, "Failed to compress image.")

            context['prev_options'] = request.POST
            return render(request, 'image_tools/tool_compress_image.html', context)

    # --- GET Request Handling ---
    else:
        # Retrieve results from session if redirected after download failure or page refresh
        context = {
            'page_title': 'Compress Image',
            'conversion_success': request.session.get('compressed_data_b64') is not None, # Check if data exists
            'download_filename': request.session.get('compressed_filename'),
            'original_size': request.session.get('original_size'),
            'compressed_size': request.session.get('compressed_size'),
            'size_reduction_percent': request.session.get('size_reduction_percent')
        }
        return render(request, 'image_tools/tool_compress_image.html', context)
    





# image_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
# ... other imports ...
# --- NEW IMPORT ---
from .webp_to_png_converter import convert_webp_to_png
# --- END NEW IMPORT ---
import os
import base64

MAX_UPLOAD_SIZE = 20 * 1024 * 1024
# ... other ALLOWED constants ...
ALLOWED_WEBP_EXTENSIONS = ['.webp']
ALLOWED_WEBP_MIMES = ['image/webp']


# --- NEW VIEW for WebP to PNG ---
def webp_to_png_view(request):
    # Clear session data
    if request.method == 'GET' or 'webpfile' in request.FILES:
        if 'w2p_png_data_b64' in request.session: del request.session['w2p_png_data_b64']
        if 'w2p_png_filename' in request.session: del request.session['w2p_png_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_w2p_png' in request.POST:
            png_data_b64 = request.session.get('w2p_png_data_b64')
            png_filename = request.session.get('w2p_png_filename', 'converted.png')
            if png_data_b64:
                try:
                    png_data = base64.b64decode(png_data_b64.encode('ascii'))
                    response = HttpResponse(png_data, content_type='image/png')
                    response['Content-Disposition'] = f'attachment; filename="{png_filename}"'
                    # Clean up session
                    if 'w2p_png_data_b64' in request.session: del request.session['w2p_png_data_b64']
                    if 'w2p_png_filename' in request.session: del request.session['w2p_png_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve converted PNG.")
            else:
                messages.error(request, "No converted PNG found to download.")
            return redirect('image_tools:webp_to_png')

        # --- Handle Conversion ---
        else:
            uploaded_file = request.FILES.get('webpfile') # Unique name

            # --- Validation ---
            if not uploaded_file:
                messages.error(request, "No file uploaded.")
                return redirect('image_tools:webp_to_png')
            if uploaded_file.size > MAX_UPLOAD_SIZE:
                 messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
                 return redirect('image_tools:webp_to_png')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_WEBP_EXTENSIONS:
                messages.error(request, f"Invalid file type '{ext}'. Only WEBP files allowed.")
                return redirect('image_tools:webp_to_png')
            if uploaded_file.content_type not in ALLOWED_WEBP_MIMES:
                 messages.warning(request, f"File might not be a valid WEBP (MIME: {uploaded_file.content_type}).")
            # --- End Validation ---

            # --- Conversion ---
            print(f"Converting {uploaded_file.name} from WebP to PNG")
            png_data, output_filename, error_message = convert_webp_to_png( # Expect 3 values now
                webp_file=uploaded_file
            )
            # --- End Conversion ---

            context = { 'page_title': 'Convert WebP to PNG' }

            if png_data and output_filename:
                print("WebP->PNG Conversion successful, storing PNG in session.")
                png_data_b64 = base64.b64encode(png_data).decode('ascii')
                request.session['w2p_png_data_b64'] = png_data_b64
                request.session['w2p_png_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_filename'] = uploaded_file.name
                messages.success(request, "WebP converted successfully to PNG!")
            else:
                print(f"WebP->PNG Conversion function returned error: {error_message}")
                context['conversion_success'] = False
                # Pass specific error message from logic function if available
                messages.error(request, error_message or "Failed to convert WebP to PNG. File might be invalid or unsupported.")

            # Re-render same page
            return render(request, 'image_tools/tool_webp_to_png.html', context)

    # --- GET Request Handling ---
    else:
        # Display form, check session for previous results
        context = {
            'page_title': 'Convert WebP to PNG',
            'conversion_success': request.session.get('w2p_png_data_b64') is not None,
            'download_filename': request.session.get('w2p_png_filename'),
            'original_filename': None # Not needed on GET
        }
        return render(request, 'image_tools/tool_webp_to_png.html', context)
    





# image_tools/views.py
# ... (other imports) ...
# --- NEW IMPORT ---
from .webp_to_jpg_converter import convert_webp_to_jpg
# --- END NEW IMPORT ---
# ...

MAX_UPLOAD_SIZE = 20 * 1024 * 1024
# ... other ALLOWED constants ...
ALLOWED_WEBP_EXTENSIONS = ['.webp']
ALLOWED_WEBP_MIMES = ['image/webp']

# --- Existing Views ---
# ...

# --- NEW VIEW for WebP to JPG ---
def webp_to_jpg_view(request):
    # Clear session data
    if request.method == 'GET' or 'webpfile' in request.FILES: # Unique input name
        if 'w2j_jpg_data_b64' in request.session: del request.session['w2j_jpg_data_b64']
        if 'w2j_jpg_filename' in request.session: del request.session['w2j_jpg_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_w2j_jpg' in request.POST:
            jpg_data_b64 = request.session.get('w2j_jpg_data_b64')
            jpg_filename = request.session.get('w2j_jpg_filename', 'converted.jpg')
            if jpg_data_b64:
                try:
                    jpg_data = base64.b64decode(jpg_data_b64.encode('ascii'))
                    response = HttpResponse(jpg_data, content_type='image/jpeg')
                    response['Content-Disposition'] = f'attachment; filename="{jpg_filename}"'
                    # Clean up session
                    if 'w2j_jpg_data_b64' in request.session: del request.session['w2j_jpg_data_b64']
                    if 'w2j_jpg_filename' in request.session: del request.session['w2j_jpg_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve converted JPG.")
            else:
                messages.error(request, "No converted JPG found to download.")
            return redirect('image_tools:webp_to_jpg')

        # --- Handle Conversion ---
        else:
            uploaded_file = request.FILES.get('webpfile') # Unique name
            # --- Get Options ---
            try:
                quality = max(1, min(95, int(request.POST.get('quality', '90'))))
            except ValueError:
                quality = 90 # Default quality
            bg_color_str = request.POST.get('bg_color', 'ffffff').lstrip('#')
            try:
                bg_color_rgb = tuple(int(bg_color_str[i:i+2], 16) for i in (0, 2, 4))
                if len(bg_color_rgb) != 3: raise ValueError("Invalid hex length")
            except (ValueError, TypeError, IndexError):
                bg_color_rgb = (255, 255, 255) # Default white on error
            # --- End Get Options ---

            # --- Validation ---
            if not uploaded_file: messages.error(request, "No file uploaded."); return redirect('image_tools:webp_to_jpg')
            if uploaded_file.size > MAX_UPLOAD_SIZE: messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB."); return redirect('image_tools:webp_to_jpg')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_WEBP_EXTENSIONS: messages.error(request, f"Invalid file type '{ext}'. Only WEBP files allowed."); return redirect('image_tools:webp_to_jpg')
            if uploaded_file.content_type not in ALLOWED_WEBP_MIMES: messages.warning(request, f"File might not be a valid WEBP (MIME: {uploaded_file.content_type}).")
            # --- End Validation ---

            # --- Conversion ---
            print(f"Converting {uploaded_file.name} from WebP to JPG. Quality={quality}, BG={bg_color_rgb}")
            jpg_data, output_filename, error_message = convert_webp_to_jpg(
                webp_file=uploaded_file,
                background_color=bg_color_rgb,
                quality=quality
            )
            # --- End Conversion ---

            context = { 'page_title': 'Convert WebP to JPG' }

            if jpg_data and output_filename:
                print("WebP->JPG Conversion successful, storing JPG in session.")
                jpg_data_b64 = base64.b64encode(jpg_data).decode('ascii')
                request.session['w2j_jpg_data_b64'] = jpg_data_b64
                request.session['w2j_jpg_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_filename'] = uploaded_file.name
                # Pass image data for preview in success section
                context['result_image_b64'] = jpg_data_b64 # Pass result for preview
                messages.success(request, "WebP converted successfully to JPG!")
            else:
                print(f"WebP->JPG function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to convert WebP to JPG.")

            context['prev_options'] = request.POST
            return render(request, 'image_tools/tool_webp_to_jpg.html', context)

    # --- GET Request Handling ---
    else:
        context = {
            'page_title': 'Convert WebP to JPG',
            'conversion_success': request.session.get('w2j_jpg_data_b64') is not None,
            'download_filename': request.session.get('w2j_jpg_filename'),
            'result_image_b64': request.session.get('w2j_jpg_data_b64'), # Get for potential refresh
            'original_filename': None
        }
        return render(request, 'image_tools/tool_webp_to_jpg.html', context)
    






# image_tools/views.py
# ... (other imports) ...
# --- NEW IMPORT ---
from .jpg_to_webp_converter import convert_jpg_to_webp
# --- END NEW IMPORT ---
# ...

# --- Existing Views ---
# ...

# --- NEW VIEW for JPG to WebP ---
def jpg_to_webp_view(request):
    # Use unique session keys
    session_key_data = 'j2w_data_b64'
    session_key_filename = 'j2w_filename'
    session_key_is_zip = 'j2w_is_zip'

    # Clear session data
    if request.method == 'GET' or 'jpgfiles_j2w' in request.FILES:
        if session_key_data in request.session: del request.session[session_key_data]
        if session_key_filename in request.session: del request.session[session_key_filename]
        if session_key_is_zip in request.session: del request.session[session_key_is_zip]

    if request.method == 'POST':
        # Handle Download
        if 'download_j2w' in request.POST:
            data_b64 = request.session.get(session_key_data)
            filename = request.session.get(session_key_filename, 'converted.webp')
            is_zip = request.session.get(session_key_is_zip, False)

            if data_b64:
                try:
                    file_data = base64.b64decode(data_b64.encode('ascii'))
                    content_type = 'application/zip' if is_zip else 'image/webp'
                    response = HttpResponse(file_data, content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    # Clean up session
                    if session_key_data in request.session: del request.session[session_key_data]
                    if session_key_filename in request.session: del request.session[session_key_filename]
                    if session_key_is_zip in request.session: del request.session[session_key_is_zip]
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve generated file.")
            else:
                messages.error(request, "No generated file found to download.")
            return redirect('image_tools:jpg_to_webp')

        # --- Handle Conversion ---
        else:
            uploaded_files = request.FILES.getlist('jpgfiles_j2w') # Unique name

            # --- Get Options ---
            try:
                quality = max(1, min(100, int(request.POST.get('quality', '80')))) # WebP 0-100
            except ValueError:
                quality = 80
            lossless = request.POST.get('lossless', 'off') == 'on'
            # --- End Get Options ---

            # --- Validation ---
            if not uploaded_files: messages.error(request, "No JPG/JPEG files uploaded."); return redirect('image_tools:jpg_to_webp')
            valid_files = []
            total_size = 0
            # ... (Size, Extension, MIME checks similar to jpg_to_png) ...
            for file in uploaded_files:
                total_size += file.size
                if total_size > MAX_UPLOAD_SIZE: messages.error(request, f"Total size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB."); return redirect('image_tools:jpg_to_webp')
                ext = os.path.splitext(file.name)[1].lower()
                if ext not in ALLOWED_JPG_EXTENSIONS: messages.error(request, f"Invalid type '{ext}' in '{file.name}'. Only JPG/JPEG allowed."); return redirect('image_tools:jpg_to_webp')
                if file.content_type not in ALLOWED_JPG_MIMES: messages.warning(request, f"File '{file.name}' might not be valid JPG (MIME: {file.content_type}).")
                valid_files.append(file)
            if not valid_files: messages.error(request, "No valid JPG files found."); return redirect('image_tools:jpg_to_webp')
            # --- End Validation ---

            # --- Conversion ---
            print(f"Converting {len(valid_files)} JPGs to WebP. Quality={quality}, Lossless={lossless}")
            output_data, output_filename, error_message, is_zip = convert_jpg_to_webp(
                image_files=valid_files,
                quality=quality,
                lossless=lossless
            )
            # --- End Conversion ---

            context = { 'page_title': 'Convert JPG to WebP' }

            if output_data and output_filename:
                print(f"JPG->WebP Conversion successful. Output: {output_filename}, Is Zip: {is_zip}")
                output_data_b64 = base64.b64encode(output_data).decode('ascii')
                request.session[session_key_data] = output_data_b64
                request.session[session_key_filename] = output_filename
                request.session[session_key_is_zip] = is_zip

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_filenames'] = [f.name for f in valid_files]
                context['is_zip'] = is_zip # Pass to template
                messages.success(request, "JPG(s) converted successfully to WebP!")
                if error_message: # Show non-fatal errors if any files failed in batch
                     messages.warning(request, f"Note: {error_message}")
            else:
                print(f"JPG->WebP function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to convert JPG to WebP.")

            context['prev_options'] = request.POST
            return render(request, 'image_tools/tool_jpg_to_webp.html', context)

    # --- GET Request Handling ---
    else:
        context = {
            'page_title': 'Convert JPG to WebP',
            'conversion_success': request.session.get(session_key_data) is not None,
            'download_filename': request.session.get(session_key_filename),
            'original_filenames': None, # Only show after conversion
            'is_zip': request.session.get(session_key_is_zip, False)
        }
        return render(request, 'image_tools/tool_jpg_to_webp.html', context)
    







# image_tools/views.py
# ... other imports ...
# --- NEW IMPORT ---
from .ico_converter_logic import convert_image_to_ico, ICO_SIZES
# --- END NEW IMPORT ---
# ...

# Allowed input image types for ICO conversion (Pillow supports many)
ALLOWED_ICO_INPUT_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'] # Common ones
ALLOWED_ICO_INPUT_MIMES = ['image/png', 'image/jpeg', 'image/bmp', 'image/gif', 'image/tiff']

# --- Existing Views ---
# ...

# --- NEW VIEW for ICO Converter ---
def ico_converter_view(request):
    # Clear session data
    if request.method == 'GET' or 'imagefile_ico' in request.FILES:
        if 'ico_data_b64' in request.session: del request.session['ico_data_b64']
        if 'ico_filename' in request.session: del request.session['ico_filename']

    context = {
        'page_title': 'ICO Converter (Favicon Generator)',
        'conversion_success': False,
        'ico_sizes': ICO_SIZES, # Pass available sizes to template
        'default_sizes': [16, 32, 48] # Define defaults for template checkboxes
    }

    if request.method == 'POST':
        # Handle Download
        if 'download_ico' in request.POST:
            ico_data_b64 = request.session.get('ico_data_b64')
            ico_filename = request.session.get('ico_filename', 'favicon.ico')
            if ico_data_b64:
                try:
                    ico_data = base64.b64decode(ico_data_b64.encode('ascii'))
                    # Correct MIME type for .ico
                    content_type = 'image/vnd.microsoft.icon' # or image/x-icon
                    response = HttpResponse(ico_data, content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="{ico_filename}"'
                    # Clean up session
                    if 'ico_data_b64' in request.session: del request.session['ico_data_b64']
                    if 'ico_filename' in request.session: del request.session['ico_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve generated ICO file.")
            else:
                messages.error(request, "No generated ICO file found to download.")
            return redirect('image_tools:ico_converter')

        # --- Handle Conversion ---
        else:
            uploaded_file = request.FILES.get('imagefile_ico') # Unique name
            # --- Get Options ---
            selected_sizes_str = request.POST.getlist('ico_sizes') # Get list of selected sizes
            selected_sizes = []
            try:
                 # Convert selected size strings to integers
                 selected_sizes = [int(s) for s in selected_sizes_str if s.isdigit() and int(s) in ICO_SIZES]
            except ValueError:
                 messages.error(request, "Invalid size selection.")
                 # Fall through, logic function will use defaults or return error

            if not selected_sizes:
                 messages.warning(request, "No sizes selected, using defaults (16, 32, 48).")
                 selected_sizes = [16, 32, 48] # Ensure defaults if none selected/valid
            # --- End Get Options ---


            # --- File Validation ---
            if not uploaded_file: messages.error(request, "No image file uploaded."); return redirect('image_tools:ico_converter')
            if uploaded_file.size > MAX_UPLOAD_SIZE: messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB."); return redirect('image_tools:ico_converter')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_ICO_INPUT_EXTENSIONS: messages.error(request, f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_ICO_INPUT_EXTENSIONS)}"); return redirect('image_tools:ico_converter')
            # Allow common image MIME types
            # if uploaded_file.content_type not in ALLOWED_ICO_INPUT_MIMES: messages.warning(request, f"File might be an unsupported image type (MIME: {uploaded_file.content_type}).")
            # --- End File Validation ---


            # --- Conversion ---
            print(f"Converting {uploaded_file.name} to ICO with sizes: {selected_sizes}")
            ico_data, output_filename, error_message = convert_image_to_ico(
                image_file=uploaded_file,
                selected_sizes=selected_sizes
            )
            # --- End Conversion ---

            if ico_data and output_filename:
                print("ICO Conversion successful, storing ICO in session.")
                ico_data_b64 = base64.b64encode(ico_data).decode('ascii')
                request.session['ico_data_b64'] = ico_data_b64
                request.session['ico_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_filename'] = uploaded_file.name
                context['generated_ico_b64'] = ico_data_b64 # Pass for preview
                messages.success(request, "Image converted successfully to ICO!")
            else:
                print(f"ICO Conversion function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to convert image to ICO.")

            context['prev_options'] = request.POST # Pass back selection attempt
            return render(request, 'image_tools/tool_ico_converter.html', context)

    # --- GET Request Handling ---
    else:
        # Display form, check session for previous results
        context['conversion_success'] = request.session.get('ico_data_b64') is not None
        if context['conversion_success']:
            context['download_filename'] = request.session.get('ico_filename')
            context['generated_ico_b64'] = request.session.get('ico_data_b64')
            # Note: Don't repopulate checkboxes on GET after success
        return render(request, 'image_tools/tool_ico_converter.html', context)
    







# image_tools/views.py
# ... (other imports) ...
# --- NEW IMPORT ---
from .rotate_flip_image_logic import rotate_flip_image
# --- END NEW IMPORT ---

# ... (constants and other views) ...

# --- NEW VIEW for Rotate/Flip Image ---
def rotate_image_view(request):
    # Clear session data
    if request.method == 'GET' or 'imagefile_rotate' in request.FILES:
        if 'rotated_data_b64' in request.session: del request.session['rotated_data_b64']
        if 'rotated_filename' in request.session: del request.session['rotated_filename']
        if 'rotated_format' in request.session: del request.session['rotated_format'] # Store format for display

    context = { 'page_title': 'Rotate & Flip Image' }

    if request.method == 'POST':
        # Handle Download
        if 'download_rotated' in request.POST:
            # ... (Download logic similar to other tools) ...
            rotated_data_b64 = request.session.get('rotated_data_b64')
            rotated_filename = request.session.get('rotated_filename', 'rotated_image.jpg')
            rotated_format = request.session.get('rotated_format', 'JPEG')
            if rotated_data_b64:
                try:
                    image_data = base64.b64decode(rotated_data_b64.encode('ascii'))
                    ext = os.path.splitext(rotated_filename)[1].lower()
                    content_type = {'jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.gif': 'image/gif', '.bmp': 'image/bmp', '.tiff': 'image/tiff'}.get(ext, 'application/octet-stream')
                    response = HttpResponse(image_data, content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="{rotated_filename}"'
                    # Clean up session
                    if 'rotated_data_b64' in request.session: del request.session['rotated_data_b64']
                    if 'rotated_filename' in request.session: del request.session['rotated_filename']
                    if 'rotated_format' in request.session: del request.session['rotated_format']
                    return response
                except Exception as e: messages.error(request, "Could not retrieve rotated image.")
            else: messages.error(request, "No rotated image found to download.")
            return redirect('image_tools:rotate_image')

        # --- Handle Rotate/Flip ---
        else:
            uploaded_file = request.FILES.get('imagefile_rotate')

            # --- Get Options ---
            rotation_option = request.POST.get('rotation_option', '0') # 90, 180, 270, custom
            custom_angle_str = request.POST.get('custom_angle', '0').strip()
            flip_h = request.POST.get('flip_horizontal', 'off') == 'on'
            flip_v = request.POST.get('flip_vertical', 'off') == 'on'
            bg_color = request.POST.get('bg_color_rotate', '#ffffff')
            output_format = request.POST.get('output_format_rotate', 'ORIGINAL')
            try: quality = max(1, min(95, int(request.POST.get('quality_rotate', '90'))))
            except ValueError: quality = 90

            # Determine final angle
            rotation_angle = 0.0
            try:
                if rotation_option == 'custom':
                    rotation_angle = float(custom_angle_str) if custom_angle_str else 0.0
                elif rotation_option in ['90', '180', '270']:
                    rotation_angle = float(rotation_option)
            except ValueError:
                messages.error(request, "Invalid custom rotation angle entered.")
                return redirect('image_tools:rotate_image')

            # --- File Validation (similar to resizer) ---
            if not uploaded_file:
                messages.error(request, "No file uploaded.")
                return redirect('image_tools:rotate_image')
            if uploaded_file.size > MAX_UPLOAD_SIZE:
                 messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
                 return redirect('image_tools:rotate_image')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_RESIZE_EXTENSIONS: # Use broader list for input
                messages.error(request, f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_RESIZE_EXTENSIONS)}")
                return redirect('image_tools:rotate_image')
            # --- End File Validation ---

            # --- Processing ---
            print(f"Rotating {uploaded_file.name}. Angle: {rotation_angle}, FlipH: {flip_h}, FlipV: {flip_v}, Format: {output_format}, Q: {quality}, BG: {bg_color}")
            processed_data, output_filename, error_message = rotate_flip_image(
                image_file=uploaded_file,
                rotation_angle=rotation_angle,
                flip_horizontal=flip_h,
                flip_vertical=flip_v,
                background_color_hex=bg_color,
                output_format=output_format,
                jpeg_quality=quality
            )
            # --- End Processing ---

            if processed_data and output_filename:
                print("Rotation/Flip successful, storing image in session.")
                processed_data_b64 = base64.b64encode(processed_data).decode('ascii')
                request.session['rotated_data_b64'] = processed_data_b64
                request.session['rotated_filename'] = output_filename
                request.session['rotated_format'] = os.path.splitext(output_filename)[1].upper().replace('.', '') # Store format

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['result_image_b64'] = processed_data_b64 # Pass for display
                context['result_format'] = request.session['rotated_format'] # Pass format
                messages.success(request, "Image processed successfully!")
            else:
                print(f"Rotation/Flip failed: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to process image.")

            context['prev_options'] = request.POST
            # Also pass original file info for preview
            try:
                 uploaded_file.seek(0)
                 context['original_image_b64'] = base64.b64encode(uploaded_file.read()).decode('ascii')
                 context['original_image_mime'] = uploaded_file.content_type
            except Exception as e:
                 print(f"Could not read original image for preview: {e}")

            return render(request, 'image_tools/tool_rotate_image.html', context)

    # --- GET Request Handling ---
    else:
        # Display the form, check if results are in session
        context['conversion_success'] = request.session.get('rotated_data_b64') is not None
        if context['conversion_success']:
            context['download_filename'] = request.session.get('rotated_filename')
            context['result_image_b64'] = request.session.get('rotated_data_b64')
            context['result_format'] = request.session.get('rotated_format')
            # Note: original image preview won't persist across requests via session easily

        return render(request, 'image_tools/tool_rotate_image.html', context)
    









# image_tools/views.py
# ... (other imports: render, redirect, HttpResponse, messages, base64, os) ...
from .png_to_jpg_converter import convert_png_to_jpg
from .resize_image_logic import resize_image
from .jpg_to_png_converter import convert_jpg_to_png
from .image_to_base64_logic import convert_image_to_base64
from .compress_image_logic import compress_image_file
# --- NEW IMPORT ---
from .watermark_logic import add_watermark
# --- END NEW IMPORT ---

MAX_UPLOAD_SIZE = 20 * 1024 * 1024 # 20 MB for base image
MAX_WATERMARK_SIZE = 5 * 1024 * 1024 # 5 MB for watermark image
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff'] # For base image
ALLOWED_IMAGE_MIMES = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/gif', 'image/tiff']
ALLOWED_WATERMARK_EXTENSIONS = ['.png'] # Prefer PNG for watermark transparency
ALLOWED_WATERMARK_MIMES = ['image/png']

# ... (other views) ...

# --- NEW VIEW for Add Watermark ---
def add_watermark_view(request):
    # Clear session data
    if request.method == 'GET' or 'base_image' in request.FILES:
        if 'watermarked_data_b64' in request.session: del request.session['watermarked_data_b64']
        if 'watermarked_filename' in request.session: del request.session['watermarked_filename']

    context = {
        'page_title': 'Add Watermark to Image',
        'prev_options': request.POST if request.method == 'POST' else {} # For repopulating form
    }

    if request.method == 'POST':
        # Handle Download
        if 'download_watermarked' in request.POST:
            # ... (Similar download logic as other tools) ...
            data_b64 = request.session.get('watermarked_data_b64')
            filename = request.session.get('watermarked_filename', 'watermarked_image.png')
            if data_b64:
                try:
                    image_data = base64.b64decode(data_b64.encode('ascii'))
                    ext = os.path.splitext(filename)[1].lower()
                    content_type = {'jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.gif':'image/gif'}.get(ext, 'application/octet-stream')
                    response = HttpResponse(image_data, content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    # Clean up session
                    if 'watermarked_data_b64' in request.session: del request.session['watermarked_data_b64']
                    if 'watermarked_filename' in request.session: del request.session['watermarked_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve watermarked image.")
            else:
                messages.error(request, "No watermarked image found to download.")
            return redirect('image_tools:add_watermark')

        # --- Handle Watermarking ---
        else:
            base_image_file = request.FILES.get('base_image')
            watermark_type = request.POST.get('watermark_type', 'text')
            watermark_image_file = request.FILES.get('watermark_image') if watermark_type == 'image' else None
            text_content = request.POST.get('watermark_text', '').strip()
            text_color_hex = request.POST.get('text_color', '#808080')
            text_size_preset = request.POST.get('text_size', 'M')
            image_scale_percent_str = request.POST.get('image_scale', '15')
            position = request.POST.get('position', 'BR')
            opacity_str = request.POST.get('opacity', '0.5')

            # --- Validation ---
            if not base_image_file:
                messages.error(request, "Please upload a base image.")
                return render(request, 'image_tools/tool_add_watermark.html', context)

            # Validate base image
            if base_image_file.size > MAX_UPLOAD_SIZE:
                 messages.error(request, f"Base image size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
                 return render(request, 'image_tools/tool_add_watermark.html', context)
            ext = os.path.splitext(base_image_file.name)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                messages.error(request, f"Invalid base image type '{ext}'. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")
                return render(request, 'image_tools/tool_add_watermark.html', context)

            # Validate watermark type and specific inputs
            if watermark_type == 'text' and not text_content:
                messages.error(request, "Please enter the watermark text.")
                return render(request, 'image_tools/tool_add_watermark.html', context)
            elif watermark_type == 'image':
                if not watermark_image_file:
                     messages.error(request, "Please upload a watermark image (PNG recommended).")
                     return render(request, 'image_tools/tool_add_watermark.html', context)
                # Validate watermark image
                if watermark_image_file.size > MAX_WATERMARK_SIZE:
                     messages.error(request, f"Watermark image size exceeds {MAX_WATERMARK_SIZE // (1024*1024)} MB.")
                     return render(request, 'image_tools/tool_add_watermark.html', context)
                wm_ext = os.path.splitext(watermark_image_file.name)[1].lower()
                if wm_ext not in ALLOWED_WATERMARK_EXTENSIONS:
                     messages.warning(request, f"Watermark image is not PNG ({wm_ext}). Transparency may not work as expected.")

            # Validate numeric options
            try:
                opacity = max(0.0, min(1.0, float(opacity_str)))
                image_scale_percent = max(5, min(50, int(image_scale_percent_str))) if watermark_type == 'image' else 15
            except ValueError:
                messages.error(request, "Invalid value provided for opacity or image scale.")
                return render(request, 'image_tools/tool_add_watermark.html', context)
            # --- End Validation ---


            # --- Add Watermark ---
            print(f"Adding watermark. Type: {watermark_type}, Pos: {position}, Opacity: {opacity}")
            watermarked_data, output_filename, error_message = add_watermark(
                base_image_file=base_image_file,
                watermark_type=watermark_type,
                text_content=text_content,
                text_color_hex=text_color_hex,
                text_size_preset=text_size_preset,
                watermark_image_file=watermark_image_file,
                image_scale_percent=image_scale_percent,
                position=position,
                opacity=opacity
            )
            # --- End Add Watermark ---


            if watermarked_data and output_filename:
                print("Watermarking successful.")
                watermarked_data_b64 = base64.b64encode(watermarked_data).decode('ascii')
                request.session['watermarked_data_b64'] = watermarked_data_b64
                request.session['watermarked_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                messages.success(request, "Watermark added successfully!")
            else:
                print(f"Watermark function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to add watermark.")

            # Re-render same page with results/errors
            return render(request, 'image_tools/tool_add_watermark.html', context)

    # --- GET Request Handling ---
    else:
        # Display form, check for previous results in session
        context['conversion_success'] = request.session.get('watermarked_data_b64') is not None
        if context['conversion_success']:
            context['download_filename'] = request.session.get('watermarked_filename')

        return render(request, 'image_tools/tool_add_watermark.html', context)
    





# image_tools/views.py
from django.shortcuts import render # Only need render
# ... other imports for existing views ...

# --- Keep existing views: png_to_jpg_view, resize_image_view, etc. ---
# ...

# --- NEW VIEW for Image Color Picker ---
def image_color_picker_view(request):
    """Displays the Image Color Picker tool page."""
    context = {
        'page_title': 'Image Color Picker'
    }
    # No POST handling needed for V1, all interaction is client-side
    return render(request, 'image_tools/tool_image_color_picker.html', context)















# image_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
# Other view imports (if any)
# ...
# Specific imports for this view
from .favicon_generator_logic import generate_favicon_assets, get_favicon_html_snippets
import os
import base64
import mimetypes # Ensure this is imported

# Constants defined earlier
MAX_UPLOAD_SIZE = 20 * 1024 * 1024 # Example: 20 MB
ALLOWED_RESIZE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff']
ALLOWED_RESIZE_MIMES = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/gif', 'image/tiff']
ALLOWED_PNG_EXTENSIONS = ['.png']
ALLOWED_PNG_MIMES = ['image/png']
ALLOWED_JPG_EXTENSIONS = ['.jpg', '.jpeg']
ALLOWED_JPG_MIMES = ['image/jpeg', 'image/jpg']
# Specific allowed types for favicon input
ALLOWED_FAVICON_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
ALLOWED_FAVICON_MIMES = ['image/jpeg', 'image/png', 'image/webp']

# --- Other view functions (png_to_jpg_view, resize_image_view, etc.) should exist above or below ---


# --- Favicon Generator View ---
def favicon_generator_view(request):
    """
    Handles GET requests to display the Favicon Generator form and
    POST requests to generate favicon assets or download the generated ZIP.
    """
    # Clear previous favicon data from session on GET or new file upload
    if request.method == 'GET' or 'imagefile_favicon' in request.FILES:
        if 'favicon_zip_b64' in request.session: del request.session['favicon_zip_b64']
        if 'favicon_zip_filename' in request.session: del request.session['favicon_zip_filename']
        if 'favicon_html' in request.session: del request.session['favicon_html']
        if 'favicon_previews' in request.session: del request.session['favicon_previews']

    # Initial context
    context = {
        'page_title': 'Favicon Generator',
        'prev_options': request.POST if request.method == 'POST' else {}, # For repopulating options on error
        'generation_success': False # Default state
    }

    if request.method == 'POST':
        # --- Handle Download Request ---
        if 'download_favicons' in request.POST:
            zip_data_b64 = request.session.get('favicon_zip_b64')
            zip_filename = request.session.get('favicon_zip_filename', 'favicons.zip')
            if zip_data_b64:
                try:
                    zip_data = base64.b64decode(zip_data_b64.encode('ascii'))
                    response = HttpResponse(zip_data, content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                    # Clean up session after successful download trigger
                    if 'favicon_zip_b64' in request.session: del request.session['favicon_zip_b64']
                    if 'favicon_zip_filename' in request.session: del request.session['favicon_zip_filename']
                    if 'favicon_html' in request.session: del request.session['favicon_html']
                    if 'favicon_previews' in request.session: del request.session['favicon_previews']
                    return response
                except Exception as e:
                    print(f"Error decoding/serving favicon ZIP from session: {e}")
                    messages.error(request, "Could not retrieve generated ZIP file.")
            else:
                messages.error(request, "No generated ZIP file found to download.")
            # Redirect if download fails or no data found
            return redirect('image_tools:favicon_generator')

        # --- Handle Generation Request ---
        else:
            uploaded_file = request.FILES.get('imagefile_favicon') # Unique name from form
            bg_color = request.POST.get('bg_color', '#ffffff') # Default white from form

            # --- File Validation ---
            if not uploaded_file:
                messages.error(request, "No image file uploaded.")
                # Render form again, keeping previously entered options
                return render(request, 'image_tools/tool_favicon_generator.html', context)

            if uploaded_file.size > MAX_UPLOAD_SIZE:
                 messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB limit for favicon source.")
                 return render(request, 'image_tools/tool_favicon_generator.html', context)

            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_FAVICON_EXTENSIONS:
                messages.error(request, f"Invalid file type '{ext}'. Please use JPG, PNG, or WEBP.")
                return render(request, 'image_tools/tool_favicon_generator.html', context)

            if uploaded_file.content_type not in ALLOWED_FAVICON_MIMES:
                 # Just a warning, as Pillow might handle it
                 messages.warning(request, f"Uploaded file MIME type '{uploaded_file.content_type}' might be unexpected. Trying to process anyway.")
            # --- End File Validation ---

            # --- Generation ---
            print(f"Generating favicons for {uploaded_file.name} with BG: {bg_color}")
            zip_data, error_message = generate_favicon_assets(
                image_file=uploaded_file,
                background_color_hex=bg_color
            )
            # --- End Generation ---

            if zip_data:
                print("Favicon generation successful.")
                zip_data_b64 = base64.b64encode(zip_data).decode('ascii')
                request.session['favicon_zip_b64'] = zip_data_b64
                request.session['favicon_zip_filename'] = "favicons.zip"
                request.session['favicon_html'] = get_favicon_html_snippets() # Get HTML snippet

                # --- Generate Preview Data ---
                preview_data = None
                try:
                    uploaded_file.seek(0) # Rewind original file
                    preview_b64 = base64.b64encode(uploaded_file.read()).decode('ascii')
                    mime_type_preview, _ = mimetypes.guess_type(uploaded_file.name)
                    if not mime_type_preview or not mime_type_preview.startswith('image'):
                         mime_type_preview = 'image/png' # fallback if guess fails
                    # Create a data URI for the preview image
                    preview_data = {'preview_src': f"data:{mime_type_preview};base64,{preview_b64}"}
                    request.session['favicon_previews'] = preview_data
                except Exception as prev_err:
                    print(f"Could not generate preview image: {prev_err}")
                    request.session['favicon_previews'] = None
                # --- End Preview Generation ---

                context['generation_success'] = True
                context['download_filename'] = "favicons.zip"
                context['favicon_html'] = request.session['favicon_html']
                context['favicon_previews'] = preview_data # Pass preview data directly
                messages.success(request, "Favicons generated successfully!")
            else:
                print(f"Favicon generation failed: {error_message}")
                context['generation_success'] = False
                messages.error(request, error_message or "Failed to generate favicons.")

            # Re-render same page with results/errors
            return render(request, 'image_tools/tool_favicon_generator.html', context)

    # --- GET Request Handling ---
    else:
        # Display the form, check if results are in session from previous attempt or failed download
        context['generation_success'] = request.session.get('favicon_zip_b64') is not None
        if context['generation_success']:
            context['download_filename'] = request.session.get('favicon_zip_filename')
            context['favicon_html'] = request.session.get('favicon_html')
            context['favicon_previews'] = request.session.get('favicon_previews')

        return render(request, 'image_tools/tool_favicon_generator.html', context)
    







# image_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
# ... other imports ...
# --- NEW IMPORT ---
from .background_remover_logic import remove_image_background
# --- END NEW IMPORT ---
import os
import base64

MAX_UPLOAD_SIZE = 10 * 1024 * 1024 # Reduce limit for AI tool? (e.g., 10MB)
# Allowed input types for BG Removal
ALLOWED_BGREMOVE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
ALLOWED_BGREMOVE_MIMES = ['image/jpeg', 'image/png', 'image/webp']

# ... (other views: png_to_jpg_view, resize_image_view, etc.) ...
# image_tools/views.py
# ... other imports ...
from .background_remover_logic import remove_image_background
# ...

# --- remove_background_view ---
def remove_background_view(request):
    # Clear session data
    if request.method == 'GET' or 'imagefile_bgremove' in request.FILES:
        # ... (clear session keys: bgremoved_data_b64, bgremoved_filename) ...
        if 'bgremoved_data_b64' in request.session: del request.session['bgremoved_data_b64']
        if 'bgremoved_filename' in request.session: del request.session['bgremoved_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_bgremoved' in request.POST:
            # ... (download logic remains the same, output is always PNG) ...
             bgremoved_data_b64 = request.session.get('bgremoved_data_b64')
             bgremoved_filename = request.session.get('bgremoved_filename', 'no_bg.png')
             if bgremoved_data_b64:
                 try:
                     image_data = base64.b64decode(bgremoved_data_b64.encode('ascii'))
                     response = HttpResponse(image_data, content_type='image/png')
                     response['Content-Disposition'] = f'attachment; filename="{bgremoved_filename}"'
                     if 'bgremoved_data_b64' in request.session: del request.session['bgremoved_data_b64']
                     if 'bgremoved_filename' in request.session: del request.session['bgremoved_filename']
                     return response
                 except Exception as e: messages.error(request, "Could not retrieve image.")
             else: messages.error(request, "No image found to download.")
             return redirect('image_tools:remove_background')

        # --- Handle Background Removal ---
        else:
            uploaded_file = request.FILES.get('imagefile_bgremove')

            # --- Get Options ---
            alpha_matting = request.POST.get('alpha_matting', 'off') == 'on'
            model_name = request.POST.get('model_name', 'u2net') # Get model name
            bg_mode = request.POST.get('bg_mode', 'transparent') # transparent or color
            bg_color_hex = request.POST.get('bg_color', '#FFFFFF') # Get hex color

            # Basic validation for hex color if mode is 'color'
            if bg_mode == 'color':
                if not bg_color_hex.startswith('#') or len(bg_color_hex) != 7:
                    bg_color_hex = '#FFFFFF' # Default to white on invalid hex format

            # --- File Validation (keep as before) ---
            if not uploaded_file: # ... etc ...
                 messages.error(request, "No image file uploaded.")
                 return redirect('image_tools:remove_background')
            if uploaded_file.size > MAX_UPLOAD_SIZE: # ... etc ...
                 messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB limit.")
                 return redirect('image_tools:remove_background')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_BGREMOVE_EXTENSIONS: # ... etc ...
                messages.error(request, f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_BGREMOVE_EXTENSIONS)}")
                return redirect('image_tools:remove_background')
            # --- End File Validation ---

            messages.info(request, "Processing image... This may take a moment.")
            print(f"Removing background for {uploaded_file.name}. Model: {model_name}, Alpha: {alpha_matting}, BGMode: {bg_mode}, BGColor: {bg_color_hex}")

            # --- Processing (pass new options) ---
            processed_data, output_filename, error_message = remove_image_background(
                image_file=uploaded_file,
                model_name=model_name,
                alpha_matting=alpha_matting,
                bg_mode=bg_mode,
                bg_color_hex=bg_color_hex
            )
            # --- End Processing ---

            context = { 'page_title': 'AI Background Remover' }

            if processed_data and output_filename:
                # ... (store in session as before) ...
                print("Background removal successful, storing image in session.")
                processed_data_b64 = base64.b64encode(processed_data).decode('ascii')
                request.session['bgremoved_data_b64'] = processed_data_b64
                request.session['bgremoved_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['result_image_b64'] = processed_data_b64
                messages.success(request, "Background removed successfully!")
            else:
                # ... (handle errors as before) ...
                print(f"Background removal function failed: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to remove background.")

            context['prev_options'] = request.POST # Pass POST data back
            return render(request, 'image_tools/tool_remove_background.html', context)

    # --- GET Request Handling ---
    else:
        context = {
            'page_title': 'AI Background Remover',
            # ... (retrieve session data as before) ...
             'conversion_success': request.session.get('bgremoved_data_b64') is not None,
             'download_filename': request.session.get('bgremoved_filename'),
             'result_image_b64': request.session.get('bgremoved_data_b64')
        }
        return render(request, 'image_tools/tool_remove_background.html', context)
    








