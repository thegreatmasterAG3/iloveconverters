# pdf_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.contrib import messages
from .jpg_to_pdf_converter import convert_images_to_pdf_pillow
import os
import base64 # To store PDF data temporarily in session
import uuid # To generate unique IDs for stored PDFs

MAX_UPLOAD_SIZE = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg']

def jpg_to_pdf_view(request):
    # Clear previous PDF data from session on GET or initial POST
    if request.method == 'GET' or 'jpgfiles' in request.FILES:
        if 'pdf_data_b64' in request.session:
            del request.session['pdf_data_b64']
        if 'pdf_filename' in request.session:
            del request.session['pdf_filename']

    if request.method == 'POST':
        # Check if this POST is for conversion or download
        if 'download_pdf' in request.POST:
             # --- Handle Download Request ---
             pdf_data_b64 = request.session.get('pdf_data_b64')
             pdf_filename = request.session.get('pdf_filename', 'converted_images.pdf')
             if pdf_data_b64:
                 try:
                     pdf_data = base64.b64decode(pdf_data_b64.encode('ascii'))
                     response = HttpResponse(pdf_data, content_type='application/pdf')
                     response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                     # Clean up session after download
                     del request.session['pdf_data_b64']
                     del request.session['pdf_filename']
                     return response
                 except Exception as e:
                     print(f"Error decoding/serving PDF from session: {e}")
                     messages.error(request, "Could not retrieve the generated PDF. Please try converting again.")
             else:
                 messages.error(request, "No generated PDF found to download. Please convert files first.")
             return redirect('pdf_tools:jpg_to_pdf') # Redirect if download fails

        # --- Handle Conversion Request ---
        else:
            uploaded_files = request.FILES.getlist('jpgfiles')
            page_size = request.POST.get('page_size', 'A4')
            orientation = request.POST.get('orientation', 'Auto')
            try:
                margin = int(request.POST.get('margin_size', '10'))
            except ValueError:
                margin = 10
            # Get merge option (defaults to True if not present, as checkbox is checked by default)
            merge_files = request.POST.get('merge_files', 'true').lower() == 'true'

            # --- Validation (Keep as before) ---
            if not uploaded_files:
                messages.error(request, "No files uploaded.")
                return redirect('pdf_tools:jpg_to_pdf')
            valid_files = []
            total_size = 0
            # ... (rest of validation loop) ...
            for file in uploaded_files:
                total_size += file.size
                if total_size > MAX_UPLOAD_SIZE:
                     messages.error(request, f"Total file size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
                     return redirect('pdf_tools:jpg_to_pdf')
                ext = os.path.splitext(file.name)[1].lower()
                if ext not in ALLOWED_EXTENSIONS:
                    messages.error(request, f"Invalid file type '{ext}'. Only JPG allowed.")
                    return redirect('pdf_tools:jpg_to_pdf')
                valid_files.append(file)
            if not valid_files:
                messages.error(request, "No valid JPG files found.")
                return redirect('pdf_tools:jpg_to_pdf')
            # --- End Validation ---

            # --- Conversion ---
            print(f"Converting {len(valid_files)} files with options: Size={page_size}, Orientation={orientation}, Margin={margin}mm, Merge={merge_files}")
            # Note: convert_images_to_pdf_pillow needs to be updated to handle merge_files if necessary
            # For Pillow's save_all, merge_files=True is the default behavior if multiple images are passed
            pdf_data = convert_images_to_pdf_pillow(
                image_files=valid_files,
                page_size_str=page_size,
                orientation_pref=orientation,
                margin_mm=margin
            )
            # --- End Conversion ---

            context = { 'page_title': 'Convert JPG to PDF' } # Basic context

            if pdf_data:
                print("Conversion successful, storing PDF in session.")
                # --- Store PDF data in session (Base64 encoded) ---
                pdf_data_b64 = base64.b64encode(pdf_data).decode('ascii')
                request.session['pdf_data_b64'] = pdf_data_b64
                # Generate a somewhat unique filename (or keep it simple)
                # filename = f"converted_{uuid.uuid4().hex[:8]}.pdf"
                filename = "converted_images.pdf"
                request.session['pdf_filename'] = filename
                # --- End Storing ---

                context['conversion_success'] = True
                context['download_filename'] = filename
                messages.success(request, "Conversion Successful!")

            else:
                print("Conversion function returned None.")
                context['conversion_success'] = False
                messages.error(request, "Failed to convert images. Please check files or server logs.")

            # Re-render the same page with success/error context
            return render(request, 'pdf_tools/tool_jpg_to_pdf.html', context)

    # --- GET Request Handling ---
    else:
        context = { 'page_title': 'Convert JPG to PDF' }
        return render(request, 'pdf_tools/tool_jpg_to_pdf.html', context)

# --- New view to handle the download click ---
# (Alternative if storing in session is problematic or for large files)
# def download_pdf_view(request, file_id):
#    # Logic to retrieve temporary file based on file_id
#    # Create HttpResponse and return
#    pass





# pdf_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .jpg_to_pdf_converter import convert_images_to_pdf_pillow
# --- NEW IMPORT ---
from .merge_pdf_logic import merge_pdf_files
# --- END NEW IMPORT ---
import os
import base64

MAX_UPLOAD_SIZE = 50 * 1024 * 1024 # Increase limit for multiple PDFs? (e.g., 50MB)
# Allowed extensions
ALLOWED_PDF_EXTENSIONS = ['.pdf']
ALLOWED_PDF_MIMES = ['application/pdf']



# --- NEW VIEW for Merge PDF ---
def merge_pdf_view(request):
    # Clear session data
    if request.method == 'GET' or 'pdffiles' in request.FILES:
        if 'merged_pdf_b64' in request.session: del request.session['merged_pdf_b64']
        if 'merged_filename' in request.session: del request.session['merged_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_merged' in request.POST:
            pdf_data_b64 = request.session.get('merged_pdf_b64')
            pdf_filename = request.session.get('merged_filename', 'merged_document.pdf')
            if pdf_data_b64:
                try:
                    pdf_data = base64.b64decode(pdf_data_b64.encode('ascii'))
                    response = HttpResponse(pdf_data, content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                    # Clean up session
                    if 'merged_pdf_b64' in request.session: del request.session['merged_pdf_b64']
                    if 'merged_filename' in request.session: del request.session['merged_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve merged PDF.")
            else:
                messages.error(request, "No merged PDF found to download.")
            return redirect('pdf_tools:merge_pdf')

        # --- Handle Merge ---
        else:
            uploaded_files = request.FILES.getlist('pdffiles') # Unique name 'pdffiles'

            # --- Validation ---
            if not uploaded_files or len(uploaded_files) < 2:
                messages.error(request, "Please upload at least two PDF files to merge.")
                return redirect('pdf_tools:merge_pdf')

            valid_files = []
            total_size = 0
            for file in uploaded_files:
                # Size check
                total_size += file.size
                if total_size > MAX_UPLOAD_SIZE:
                     messages.error(request, f"Total file size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
                     return redirect('pdf_tools:merge_pdf')
                # Extension check
                ext = os.path.splitext(file.name)[1].lower()
                if ext not in ALLOWED_PDF_EXTENSIONS:
                    messages.error(request, f"Invalid file type '{ext}' in '{file.name}'. Only PDF files allowed.")
                    return redirect('pdf_tools:merge_pdf')
                # MIME type check (optional warning)
                if file.content_type not in ALLOWED_PDF_MIMES:
                     messages.warning(request, f"File '{file.name}' might not be a valid PDF (MIME type: {file.content_type}).")
                valid_files.append(file)

            if len(valid_files) < 2: # Double check after potential warnings/skips
                 messages.error(request, "Need at least two valid PDF files to merge.")
                 return redirect('pdf_tools:merge_pdf')
            # --- End Validation ---


            # --- Merging ---
            print(f"Merging {len(valid_files)} PDF files...")
            merged_data, output_filename = merge_pdf_files(valid_files)
            # --- End Merging ---

            context = { 'page_title': 'Merge PDF Files' }

            if merged_data and output_filename:
                print("Merge successful, storing PDF in session.")
                merged_data_b64 = base64.b64encode(merged_data).decode('ascii')
                request.session['merged_pdf_b64'] = merged_data_b64
                request.session['merged_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                # Pass original filenames maybe?
                context['original_filenames'] = [f.name for f in valid_files]
                messages.success(request, "PDFs merged successfully!")
            else:
                print("Merge function returned None.")
                context['conversion_success'] = False
                messages.error(request, "Failed to merge PDF files. Ensure files are valid and not encrypted, or check server logs.")

            # Re-render same page
            return render(request, 'pdf_tools/tool_merge_pdf.html', context)

    # --- GET Request Handling ---
    else:
        context = { 'page_title': 'Merge PDF Files' }
        return render(request, 'pdf_tools/tool_merge_pdf.html', context)
    





# pdf_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .jpg_to_pdf_converter import convert_images_to_pdf_pillow
from .merge_pdf_logic import merge_pdf_files
# --- NEW IMPORT ---
from .split_pdf_logic import split_pdf_by_range
from PyPDF2 import PdfReader # Import Reader to check page count in view
# --- END NEW IMPORT ---
import os
import base64

MAX_UPLOAD_SIZE = 50 * 1024 * 1024 # Adjust as needed
ALLOWED_PDF_EXTENSIONS = ['.pdf']
ALLOWED_PDF_MIMES = ['application/pdf']


# --- NEW VIEW for Split PDF ---
def split_pdf_view(request):
    # Clear session data
    if request.method == 'GET' or 'pdffile_split' in request.FILES:
        if 'split_pdf_b64' in request.session: del request.session['split_pdf_b64']
        if 'split_filename' in request.session: del request.session['split_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_split' in request.POST:
            pdf_data_b64 = request.session.get('split_pdf_b64')
            pdf_filename = request.session.get('split_filename', 'split_document.pdf')
            if pdf_data_b64:
                try:
                    pdf_data = base64.b64decode(pdf_data_b64.encode('ascii'))
                    response = HttpResponse(pdf_data, content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                    # Clean up session
                    if 'split_pdf_b64' in request.session: del request.session['split_pdf_b64']
                    if 'split_filename' in request.session: del request.session['split_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve split PDF.")
            else:
                messages.error(request, "No split PDF found to download.")
            return redirect('pdf_tools:split_pdf')

        # --- Handle Split ---
        else:
            uploaded_file = request.FILES.get('pdffile_split') # Unique name
            start_page_str = request.POST.get('start_page', '').strip()
            end_page_str = request.POST.get('end_page', '').strip()

            # --- File Validation ---
            if not uploaded_file:
                messages.error(request, "No PDF file uploaded.")
                return redirect('pdf_tools:split_pdf')
            if uploaded_file.size > MAX_UPLOAD_SIZE:
                 messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
                 return redirect('pdf_tools:split_pdf')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_PDF_EXTENSIONS:
                messages.error(request, f"Invalid file type '{ext}'. Only PDF allowed.")
                return redirect('pdf_tools:split_pdf')
            if uploaded_file.content_type not in ALLOWED_PDF_MIMES:
                 messages.warning(request, f"File might not be a valid PDF (MIME: {uploaded_file.content_type}).")
            # --- End File Validation ---

            # --- Page Range Validation ---
            total_pages = 0
            start_page = None
            end_page = None
            try:
                # Check total pages without decrypting fully if possible
                uploaded_file.seek(0)
                reader_check = PdfReader(uploaded_file)
                if reader_check.is_encrypted:
                    if not reader_check.decrypt(''): # Try empty password
                         messages.error(request, f"Cannot process encrypted file '{uploaded_file.name}' without password.")
                         return redirect('pdf_tools:split_pdf')
                total_pages = len(reader_check.pages)

                if not start_page_str: raise ValueError("Start Page is required.")
                start_page = int(start_page_str)
                if not end_page_str: raise ValueError("End Page is required.")
                end_page = int(end_page_str)

                if start_page < 1 or end_page < 1:
                    raise ValueError("Page numbers must be positive.")
                if start_page > total_pages or end_page > total_pages:
                    raise ValueError(f"Page number out of range (File has {total_pages} pages).")
                if start_page > end_page:
                    raise ValueError("Start Page cannot be greater than End Page.")

            except ValueError as ve:
                messages.error(request, f"Invalid page numbers entered: {ve}")
                return redirect('pdf_tools:split_pdf')
            except Exception as e: # Catch PyPDF2 errors etc.
                 messages.error(request, f"Could not read PDF file to get page count: {e}")
                 return redirect('pdf_tools:split_pdf')
            # --- End Page Range Validation ---

            # --- Splitting ---
            print(f"Splitting {uploaded_file.name} from page {start_page} to {end_page}")
            split_data, output_filename, error_message = split_pdf_by_range(
                pdf_file=uploaded_file,
                start_page=start_page,
                end_page=end_page
            )
            # --- End Splitting ---

            context = { 'page_title': 'Split PDF by Range' }

            if split_data and output_filename:
                print("Split successful, storing PDF in session.")
                split_data_b64 = base64.b64encode(split_data).decode('ascii')
                request.session['split_pdf_b64'] = split_data_b64
                request.session['split_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_filename'] = uploaded_file.name # Pass original filename
                messages.success(request, "PDF split successfully!")
            else:
                print(f"Split function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to split PDF file.")

            # Store previous options for repopulation
            context['prev_options'] = request.POST
            # Re-render same page
            return render(request, 'pdf_tools/tool_split_pdf.html', context)

    # --- GET Request Handling ---
    else:
         # Retrieve results from session if redirected after download failure or page refresh
        context = {
            'page_title': 'Split PDF by Range',
            'conversion_success': request.session.get('split_pdf_b64') is not None,
            'download_filename': request.session.get('split_filename'),
            'original_filename': None # Not needed on GET usually
        }
        return render(request, 'pdf_tools/tool_split_pdf.html', context)
    





# pdf_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
# ... other imports ...
# --- NEW IMPORT ---
from .compress_pdf_logic import compress_pdf
# --- END NEW IMPORT ---
# ... PyPDF2 import might already be there from split_pdf ...
import os
import base64

MAX_UPLOAD_SIZE = 50 * 1024 * 1024 # Keep 50MB limit?
ALLOWED_PDF_EXTENSIONS = ['.pdf']
ALLOWED_PDF_MIMES = ['application/pdf']



# --- NEW VIEW for Compress PDF ---
def compress_pdf_view(request):
    # Clear session data
    if request.method == 'GET' or 'pdffile_compress' in request.FILES:
        if 'compressed_pdf_b64' in request.session: del request.session['compressed_pdf_b64']
        if 'compressed_pdf_filename' in request.session: del request.session['compressed_pdf_filename']
        if 'original_pdf_size' in request.session: del request.session['original_pdf_size']
        if 'final_pdf_size' in request.session: del request.session['final_pdf_size']
        if 'pdf_reduction_percent' in request.session: del request.session['pdf_reduction_percent']

    if request.method == 'POST':
        # Handle Download
        if 'download_compressed_pdf' in request.POST:
            pdf_data_b64 = request.session.get('compressed_pdf_b64')
            pdf_filename = request.session.get('compressed_pdf_filename', 'compressed.pdf')
            if pdf_data_b64:
                try:
                    pdf_data = base64.b64decode(pdf_data_b64.encode('ascii'))
                    response = HttpResponse(pdf_data, content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                    # Clean up session
                    if 'compressed_pdf_b64' in request.session: del request.session['compressed_pdf_b64']
                    if 'compressed_pdf_filename' in request.session: del request.session['compressed_pdf_filename']
                    if 'original_pdf_size' in request.session: del request.session['original_pdf_size']
                    if 'final_pdf_size' in request.session: del request.session['final_pdf_size']
                    if 'pdf_reduction_percent' in request.session: del request.session['pdf_reduction_percent']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve compressed PDF.")
            else:
                messages.error(request, "No compressed PDF found to download.")
            return redirect('pdf_tools:compress_pdf')

        # --- Handle Compression ---
        else:
            uploaded_file = request.FILES.get('pdffile_compress') # Unique name

            # --- Get Options ---
            compress_streams_opt = request.POST.get('compress_streams', 'on') == 'on' # Default ON
            remove_metadata_opt = request.POST.get('remove_metadata', 'off') == 'on' # Default OFF

            # --- File Validation ---
            if not uploaded_file:
                messages.error(request, "No PDF file uploaded.")
                return redirect('pdf_tools:compress_pdf')
            if uploaded_file.size > MAX_UPLOAD_SIZE:
                 messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
                 return redirect('pdf_tools:compress_pdf')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_PDF_EXTENSIONS:
                messages.error(request, f"Invalid file type '{ext}'. Only PDF allowed.")
                return redirect('pdf_tools:compress_pdf')
            if uploaded_file.content_type not in ALLOWED_PDF_MIMES:
                 messages.warning(request, f"File might not be a valid PDF (MIME: {uploaded_file.content_type}).")
            original_size = uploaded_file.size
            # --- End File Validation ---

            # --- Compression ---
            print(f"Compressing {uploaded_file.name} with options: Streams={compress_streams_opt}, Metadata={remove_metadata_opt}")
            compressed_data, output_filename, error_message = compress_pdf(
                pdf_file=uploaded_file,
                compress_streams=compress_streams_opt, # Pass option (though default in PyPDF2 3+)
                remove_metadata=remove_metadata_opt
            )
            # --- End Compression ---

            context = { 'page_title': 'Compress PDF' }

            if compressed_data and output_filename:
                print("Compression successful, storing PDF in session.")
                compressed_data_b64 = base64.b64encode(compressed_data).decode('ascii')
                compressed_size = len(compressed_data)

                request.session['compressed_pdf_b64'] = compressed_data_b64
                request.session['compressed_pdf_filename'] = output_filename
                request.session['original_pdf_size'] = original_size
                request.session['final_pdf_size'] = compressed_size

                # Calculate Reduction Percentage
                size_reduction_percent = 0
                if original_size > 0:
                    reduction = original_size - compressed_size
                    if reduction > 0:
                       size_reduction_percent = round((reduction / original_size) * 100)
                request.session['pdf_reduction_percent'] = size_reduction_percent

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_size'] = original_size
                context['compressed_size'] = compressed_size
                context['size_reduction_percent'] = size_reduction_percent
                messages.success(request, "PDF compressed successfully!")
            else:
                print(f"Compress function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to compress PDF file.")

            context['prev_options'] = request.POST
            return render(request, 'pdf_tools/tool_compress_pdf.html', context)

    # --- GET Request Handling ---
    else:
         # Retrieve results from session if needed
        context = {
            'page_title': 'Compress PDF',
            'conversion_success': request.session.get('compressed_pdf_b64') is not None,
            'download_filename': request.session.get('compressed_pdf_filename'),
            'original_size': request.session.get('original_pdf_size'),
            'compressed_size': request.session.get('final_pdf_size'),
            'size_reduction_percent': request.session.get('pdf_reduction_percent')
        }
        return render(request, 'pdf_tools/tool_compress_pdf.html', context)
    





# pdf_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
# ... other imports ...
# --- NEW IMPORT ---
from .rotate_pdf_logic import rotate_pdf_pages
# --- END NEW IMPORT ---
# ... PyPDF2 import might already be there ...
import os
import base64

# ... Constants ...
MAX_UPLOAD_SIZE = 50 * 1024 * 1024
ALLOWED_PDF_EXTENSIONS = ['.pdf']
ALLOWED_PDF_MIMES = ['application/pdf']


# --- NEW VIEW for Rotate PDF ---
def rotate_pdf_view(request):
    # Clear session data
    if request.method == 'GET' or 'pdffile_rotate' in request.FILES:
        if 'rotated_pdf_b64' in request.session: del request.session['rotated_pdf_b64']
        if 'rotated_filename' in request.session: del request.session['rotated_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_rotated' in request.POST:
            pdf_data_b64 = request.session.get('rotated_pdf_b64')
            pdf_filename = request.session.get('rotated_filename', 'rotated.pdf')
            if pdf_data_b64:
                try:
                    pdf_data = base64.b64decode(pdf_data_b64.encode('ascii'))
                    response = HttpResponse(pdf_data, content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                    # Clean up session
                    if 'rotated_pdf_b64' in request.session: del request.session['rotated_pdf_b64']
                    if 'rotated_filename' in request.session: del request.session['rotated_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve rotated PDF.")
            else:
                messages.error(request, "No rotated PDF found to download.")
            return redirect('pdf_tools:rotate_pdf')

        # --- Handle Rotation ---
        else:
            uploaded_file = request.FILES.get('pdffile_rotate') # Unique name
            # --- Get Options ---
            try:
                angle = int(request.POST.get('rotation_angle', '90'))
                if angle not in [90, 180, 270]:
                    raise ValueError("Invalid angle selected.")
            except ValueError:
                angle = 90 # Default angle
                messages.warning(request, "Invalid rotation angle selected, defaulting to 90° clockwise.")

            page_mode = request.POST.get('page_selection_mode', 'all')
            page_string = request.POST.get('specific_pages', '').strip()
            # --- End Get Options ---


            # --- File Validation ---
            if not uploaded_file:
                messages.error(request, "No PDF file uploaded.")
                return redirect('pdf_tools:rotate_pdf')
            if uploaded_file.size > MAX_UPLOAD_SIZE:
                 messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
                 return redirect('pdf_tools:rotate_pdf')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_PDF_EXTENSIONS:
                messages.error(request, f"Invalid file type '{ext}'. Only PDF allowed.")
                return redirect('pdf_tools:rotate_pdf')
            if uploaded_file.content_type not in ALLOWED_PDF_MIMES:
                 messages.warning(request, f"File might not be a valid PDF (MIME: {uploaded_file.content_type}).")
            # --- End File Validation ---

            # --- Additional validation for specific pages mode ---
            if page_mode == 'specific' and not page_string:
                 messages.error(request, "Please enter the specific pages or ranges to rotate.")
                 # Re-render with error and previous options
                 context = {'page_title': 'Rotate PDF Pages', 'prev_options': request.POST}
                 return render(request, 'pdf_tools/tool_rotate_pdf.html', context)
             # More detailed range validation happens in the logic function


            # --- Rotation ---
            print(f"Rotating {uploaded_file.name} by {angle} degrees. Mode: {page_mode}, Pages: '{page_string}'")
            rotated_data, output_filename, error_message = rotate_pdf_pages(
                pdf_file=uploaded_file,
                angle=angle,
                page_selection_mode=page_mode,
                page_string=page_string
            )
            # --- End Rotation ---

            context = { 'page_title': 'Rotate PDF Pages' }

            if rotated_data and output_filename:
                print("Rotation successful, storing PDF in session.")
                rotated_data_b64 = base64.b64encode(rotated_data).decode('ascii')
                request.session['rotated_pdf_b64'] = rotated_data_b64
                request.session['rotated_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_filename'] = uploaded_file.name
                messages.success(request, "PDF rotated successfully!")
            else:
                print(f"Rotation function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to rotate PDF file.")

            context['prev_options'] = request.POST
            return render(request, 'pdf_tools/tool_rotate_pdf.html', context)

    # --- GET Request Handling ---
    else:
        # Display form, check session for previous results
        context = {
            'page_title': 'Rotate PDF Pages',
            'conversion_success': request.session.get('rotated_pdf_b64') is not None,
            'download_filename': request.session.get('rotated_filename'),
            'original_filename': None
        }
        return render(request, 'pdf_tools/tool_rotate_pdf.html', context)
    







# pdf_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
# ... other imports ...
# --- NEW IMPORT ---
from .pdf_to_png_logic import convert_pdf_to_png_zip
# --- END NEW IMPORT ---
# ... PyPDF2, fitz (if used elsewhere), os, base64 ...
import os
import base64

MAX_UPLOAD_SIZE = 100 * 1024 * 1024 # Allow larger PDFs? 100MB
ALLOWED_PDF_EXTENSIONS = ['.pdf']
ALLOWED_PDF_MIMES = ['application/pdf']

# --- Existing Views ---
# ...

# --- NEW VIEW for PDF to PNG ---
def pdf_to_png_view(request):
    # Clear session data
    if request.method == 'GET' or 'pdffile_p2p' in request.FILES:
        if 'p2p_zip_b64' in request.session: del request.session['p2p_zip_b64']
        if 'p2p_zip_filename' in request.session: del request.session['p2p_zip_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_p2p_zip' in request.POST:
            zip_data_b64 = request.session.get('p2p_zip_b64')
            zip_filename = request.session.get('p2p_zip_filename', 'pdf_images.zip')
            if zip_data_b64:
                try:
                    zip_data = base64.b64decode(zip_data_b64.encode('ascii'))
                    response = HttpResponse(zip_data, content_type='application/zip') # ZIP content type
                    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                    # Clean up session
                    if 'p2p_zip_b64' in request.session: del request.session['p2p_zip_b64']
                    if 'p2p_zip_filename' in request.session: del request.session['p2p_zip_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve generated ZIP file.")
            else:
                messages.error(request, "No generated ZIP file found to download.")
            return redirect('pdf_tools:pdf_to_png')

        # --- Handle Conversion ---
        else:
            uploaded_file = request.FILES.get('pdffile_p2p') # Unique name
            # --- Get Options ---
            dpi = request.POST.get('dpi_preset', '150') # Default 150
            page_mode = request.POST.get('page_selection_mode', 'all')
            page_string = request.POST.get('specific_pages', '').strip()
            # --- End Get Options ---

            # --- File Validation ---
            if not uploaded_file:
                messages.error(request, "No PDF file uploaded.")
                return redirect('pdf_tools:pdf_to_png')
            if uploaded_file.size > MAX_UPLOAD_SIZE:
                 messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
                 return redirect('pdf_tools:pdf_to_png')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_PDF_EXTENSIONS:
                messages.error(request, f"Invalid file type '{ext}'. Only PDF allowed.")
                return redirect('pdf_tools:pdf_to_png')
            if uploaded_file.content_type not in ALLOWED_PDF_MIMES:
                 messages.warning(request, f"File might not be a valid PDF (MIME: {uploaded_file.content_type}).")
            # --- End File Validation ---

            # --- Specific Pages Validation ---
            if page_mode == 'specific' and not page_string:
                 messages.error(request, "Please enter the specific pages or ranges to convert.")
                 context = {'page_title': 'Convert PDF to PNG', 'prev_options': request.POST}
                 return render(request, 'pdf_tools/tool_pdf_to_png.html', context)
             # Further range validation happens in logic function

            # --- Conversion ---
            print(f"Converting {uploaded_file.name} to PNG. DPI: {dpi}, Mode: {page_mode}, Pages: '{page_string}'")
            zip_data, output_filename, error_message = convert_pdf_to_png_zip(
                pdf_file=uploaded_file,
                dpi_str=dpi,
                page_selection_mode=page_mode,
                page_string=page_string
            )
            # --- End Conversion ---

            context = { 'page_title': 'Convert PDF to PNG' }

            if zip_data and output_filename:
                print("PDF->PNG Conversion successful, storing ZIP in session.")
                zip_data_b64 = base64.b64encode(zip_data).decode('ascii')
                request.session['p2p_zip_b64'] = zip_data_b64
                request.session['p2p_zip_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_filename'] = uploaded_file.name
                messages.success(request, "PDF converted to PNG images successfully!")
            else:
                print(f"PDF->PNG function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to convert PDF to PNG.")

            context['prev_options'] = request.POST
            return render(request, 'pdf_tools/tool_pdf_to_png.html', context)

    # --- GET Request Handling ---
    else:
        context = {
            'page_title': 'Convert PDF to PNG',
            'conversion_success': request.session.get('p2p_zip_b64') is not None,
            'download_filename': request.session.get('p2p_zip_filename'),
            'original_filename': None
        }
        return render(request, 'pdf_tools/tool_pdf_to_png.html', context)
    





# pdf_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
# ... other imports ...
# --- NEW IMPORT ---
from .pdf_to_jpg_logic import convert_pdf_to_jpg_zip
# --- END NEW IMPORT ---
import os
import base64

MAX_UPLOAD_SIZE = 100 * 1024 * 1024 # Keep 100MB?
ALLOWED_PDF_EXTENSIONS = ['.pdf']
ALLOWED_PDF_MIMES = ['application/pdf']

# --- Existing Views ---
# ...

# --- NEW VIEW for PDF to JPG ---
def pdf_to_jpg_view(request):
    # Clear session data
    if request.method == 'GET' or 'pdffile_p2j' in request.FILES:
        if 'p2j_zip_b64' in request.session: del request.session['p2j_zip_b64']
        if 'p2j_zip_filename' in request.session: del request.session['p2j_zip_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_p2j_zip' in request.POST:
            zip_data_b64 = request.session.get('p2j_zip_b64')
            zip_filename = request.session.get('p2j_zip_filename', 'pdf_images.zip')
            if zip_data_b64:
                try:
                    zip_data = base64.b64decode(zip_data_b64.encode('ascii'))
                    response = HttpResponse(zip_data, content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                    # Clean up session
                    if 'p2j_zip_b64' in request.session: del request.session['p2j_zip_b64']
                    if 'p2j_zip_filename' in request.session: del request.session['p2j_zip_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve generated ZIP file.")
            else:
                messages.error(request, "No generated ZIP file found to download.")
            return redirect('pdf_tools:pdf_to_jpg')

        # --- Handle Conversion ---
        else:
            uploaded_file = request.FILES.get('pdffile_p2j') # Unique name
            # --- Get Options ---
            dpi = request.POST.get('dpi_preset', '150')
            page_mode = request.POST.get('page_selection_mode', 'all')
            page_string = request.POST.get('specific_pages', '').strip()
            try:
                 quality = max(1, min(95, int(request.POST.get('quality', '85')))) # Default 85
            except ValueError:
                 quality = 85
            # --- End Get Options ---

            # --- File Validation ---
            if not uploaded_file: messages.error(request, "No PDF file uploaded."); return redirect('pdf_tools:pdf_to_jpg')
            if uploaded_file.size > MAX_UPLOAD_SIZE: messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB."); return redirect('pdf_tools:pdf_to_jpg')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_PDF_EXTENSIONS: messages.error(request, f"Invalid file type '{ext}'. Only PDF allowed."); return redirect('pdf_tools:pdf_to_jpg')
            if uploaded_file.content_type not in ALLOWED_PDF_MIMES: messages.warning(request, f"File might not be a valid PDF (MIME: {uploaded_file.content_type}).")
            # --- End File Validation ---

            # --- Specific Pages Validation ---
            if page_mode == 'specific' and not page_string:
                 messages.error(request, "Please enter the specific pages or ranges to convert.")
                 context = {'page_title': 'Convert PDF to JPG', 'prev_options': request.POST}
                 return render(request, 'pdf_tools/tool_pdf_to_jpg.html', context)
             # Further range validation happens in the logic function

            # --- Conversion ---
            print(f"Converting {uploaded_file.name} to JPG. DPI: {dpi}, Quality: {quality}, Mode: {page_mode}, Pages: '{page_string}'")
            zip_data, output_filename, error_message = convert_pdf_to_jpg_zip(
                pdf_file=uploaded_file,
                dpi_str=dpi,
                quality=quality,
                page_selection_mode=page_mode,
                page_string=page_string
            )
            # --- End Conversion ---

            context = { 'page_title': 'Convert PDF to JPG' }

            if zip_data and output_filename:
                print("PDF->JPG Conversion successful, storing ZIP in session.")
                zip_data_b64 = base64.b64encode(zip_data).decode('ascii')
                request.session['p2j_zip_b64'] = zip_data_b64
                request.session['p2j_zip_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_filename'] = uploaded_file.name
                messages.success(request, "PDF converted to JPG images successfully!")
            else:
                print(f"PDF->JPG function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to convert PDF to JPG.")

            context['prev_options'] = request.POST
            return render(request, 'pdf_tools/tool_pdf_to_jpg.html', context)

    # --- GET Request Handling ---
    else:
        context = {
            'page_title': 'Convert PDF to JPG',
            'conversion_success': request.session.get('p2j_zip_b64') is not None,
            'download_filename': request.session.get('p2j_zip_filename'),
            'original_filename': None
        }
        return render(request, 'pdf_tools/tool_pdf_to_jpg.html', context)









# pdf_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
# ... other imports ...
# --- NEW IMPORT ---
from .png_to_pdf_converter import convert_pngs_to_pdf
# --- END NEW IMPORT ---
# ... other imports ...
import os
import base64

MAX_UPLOAD_SIZE = 50 * 1024 * 1024 # Allow reasonable size for multiple PNGs
ALLOWED_PNG_EXTENSIONS = ['.png']
ALLOWED_PNG_MIMES = ['image/png']

# --- Existing Views ---
# ...

# --- NEW VIEW for PNG to PDF ---
def png_to_pdf_view(request):
    # Clear session data
    if request.method == 'GET' or 'pngfiles' in request.FILES:
        if 'p2p_pdf_data_b64' in request.session: del request.session['p2p_pdf_data_b64']
        if 'p2p_pdf_filename' in request.session: del request.session['p2p_pdf_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_p2p_pdf' in request.POST:
            pdf_data_b64 = request.session.get('p2p_pdf_data_b64')
            pdf_filename = request.session.get('p2p_pdf_filename', 'converted_pngs.pdf')
            if pdf_data_b64:
                try:
                    pdf_data = base64.b64decode(pdf_data_b64.encode('ascii'))
                    response = HttpResponse(pdf_data, content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                    # Clean up session
                    if 'p2p_pdf_data_b64' in request.session: del request.session['p2p_pdf_data_b64']
                    if 'p2p_pdf_filename' in request.session: del request.session['p2p_pdf_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve generated PDF.")
            else:
                messages.error(request, "No generated PDF found to download.")
            return redirect('pdf_tools:png_to_pdf')

        # --- Handle Conversion ---
        else:
            uploaded_files = request.FILES.getlist('pngfiles') # Unique name 'pngfiles'
            # --- Get Options (same as JPG->PDF) ---
            page_size = request.POST.get('page_size', 'A4')
            orientation = request.POST.get('orientation', 'Auto')
            try: margin = int(request.POST.get('margin_size', '10'))
            except ValueError: margin = 10
            # --- End Get Options ---

            # --- File Validation ---
            if not uploaded_files:
                messages.error(request, "No PNG files uploaded.")
                return redirect('pdf_tools:png_to_pdf')
            valid_files = []
            total_size = 0
            for file in uploaded_files:
                total_size += file.size
                if total_size > MAX_UPLOAD_SIZE:
                     messages.error(request, f"Total file size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
                     return redirect('pdf_tools:png_to_pdf')
                ext = os.path.splitext(file.name)[1].lower()
                if ext not in ALLOWED_PNG_EXTENSIONS:
                    messages.error(request, f"Invalid file type '{ext}' in '{file.name}'. Only PNG files allowed.")
                    return redirect('pdf_tools:png_to_pdf')
                if file.content_type not in ALLOWED_PNG_MIMES:
                     messages.warning(request, f"File '{file.name}' might not be a valid PNG (MIME: {file.content_type}).")
                valid_files.append(file)
            if not valid_files:
                messages.error(request, "No valid PNG files found in selection.")
                return redirect('pdf_tools:png_to_pdf')
            # --- End Validation ---

            # --- Conversion ---
            print(f"Converting {len(valid_files)} PNGs to PDF. Size={page_size}, Orientation={orientation}, Margin={margin}mm")
            pdf_data, output_filename, error_message = convert_pngs_to_pdf(
                image_files=valid_files,
                page_size_str=page_size,
                orientation_pref=orientation,
                margin_mm=margin
            )
            # --- End Conversion ---

            context = { 'page_title': 'Convert PNG to PDF' }

            if pdf_data and output_filename:
                print("PNG->PDF Conversion successful, storing PDF in session.")
                pdf_data_b64 = base64.b64encode(pdf_data).decode('ascii')
                request.session['p2p_pdf_data_b64'] = pdf_data_b64
                request.session['p2p_pdf_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_filenames'] = [f.name for f in valid_files] # List original names
                messages.success(request, "PNGs converted successfully to PDF!")
            else:
                print(f"PNG->PDF function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to convert PNGs to PDF.")

            context['prev_options'] = request.POST
            return render(request, 'pdf_tools/tool_png_to_pdf.html', context)

    # --- GET Request Handling ---
    else:
        context = {
            'page_title': 'Convert PNG to PDF',
            'conversion_success': request.session.get('p2p_pdf_data_b64') is not None,
            'download_filename': request.session.get('p2p_pdf_filename'),
            'original_filenames': None
        }
        return render(request, 'pdf_tools/tool_png_to_pdf.html', context)
    




# pdf_tools/views.py
# ... (other imports) ...
# --- NEW IMPORT ---
from .pdf_to_word_logic import convert_pdf_to_word
# --- END NEW IMPORT ---
# ... (constants etc.) ...

# --- Existing Views ---
# ...

# --- NEW VIEW for PDF to Word ---
def pdf_to_word_view(request):
    # Clear session data
    if request.method == 'GET' or 'pdffile_p2w' in request.FILES:
        if 'p2w_docx_b64' in request.session: del request.session['p2w_docx_b64']
        if 'p2w_docx_filename' in request.session: del request.session['p2w_docx_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_p2w_docx' in request.POST:
            docx_data_b64 = request.session.get('p2w_docx_b64')
            docx_filename = request.session.get('p2w_docx_filename', 'converted.docx')
            if docx_data_b64:
                try:
                    docx_data = base64.b64decode(docx_data_b64.encode('ascii'))
                    # Correct DOCX MIME type
                    content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    response = HttpResponse(docx_data, content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="{docx_filename}"'
                    # Clean up session
                    if 'p2w_docx_b64' in request.session: del request.session['p2w_docx_b64']
                    if 'p2w_docx_filename' in request.session: del request.session['p2w_docx_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve generated Word document.")
            else:
                messages.error(request, "No generated Word document found to download.")
            return redirect('pdf_tools:pdf_to_word')

        # --- Handle Conversion ---
        else:
            uploaded_file = request.FILES.get('pdffile_p2w') # Unique name
            # --- Get Options ---
            page_mode = request.POST.get('page_selection_mode', 'all')
            page_string = request.POST.get('specific_pages', '').strip()
            # --- End Get Options ---

            # --- File Validation ---
            if not uploaded_file: messages.error(request, "No PDF file uploaded."); return redirect('pdf_tools:pdf_to_word')
            if uploaded_file.size > MAX_UPLOAD_SIZE: messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB."); return redirect('pdf_tools:pdf_to_word')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_PDF_EXTENSIONS: messages.error(request, f"Invalid file type '{ext}'. Only PDF allowed."); return redirect('pdf_tools:pdf_to_word')
            if uploaded_file.content_type not in ALLOWED_PDF_MIMES: messages.warning(request, f"File might not be a valid PDF (MIME: {uploaded_file.content_type}).")
            # --- End File Validation ---

            # --- Specific Pages Validation (Basic check if mode selected) ---
            if page_mode == 'specific' and not page_string:
                 messages.error(request, "Please enter the specific pages or ranges to convert.")
                 context = {'page_title': 'Convert PDF to Word', 'prev_options': request.POST}
                 return render(request, 'pdf_tools/tool_pdf_to_word.html', context)
             # Full validation happens in logic function after getting total pages

            # --- Conversion ---
            print(f"Converting {uploaded_file.name} to Word. Mode: {page_mode}, Pages: '{page_string}'")
            docx_data, output_filename, error_message = convert_pdf_to_word(
                pdf_file=uploaded_file,
                page_selection_mode=page_mode,
                page_string=page_string
            )
            # --- End Conversion ---

            context = { 'page_title': 'Convert PDF to Word' }

            if docx_data and output_filename:
                print("PDF->Word Conversion successful, storing DOCX in session.")
                docx_data_b64 = base64.b64encode(docx_data).decode('ascii')
                request.session['p2w_docx_b64'] = docx_data_b64
                request.session['p2w_docx_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_filename'] = uploaded_file.name
                messages.success(request, "PDF converted successfully to Word!")
            else:
                print(f"PDF->Word function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to convert PDF to Word.")

            context['prev_options'] = request.POST
            return render(request, 'pdf_tools/tool_pdf_to_word.html', context)

    # --- GET Request Handling ---
    else:
        context = {
            'page_title': 'Convert PDF to Word',
            'conversion_success': request.session.get('p2w_docx_b64') is not None,
            'download_filename': request.session.get('p2w_docx_filename'),
            'original_filename': None
        }
        return render(request, 'pdf_tools/tool_pdf_to_word.html', context)
    




# pdf_tools/views.py
# ... (other imports) ...
# --- NEW IMPORT ---
from .pdf_to_excel_logic import convert_pdf_to_excel
# --- END NEW IMPORT ---
# ...

# --- Existing Views ---
# ...

# --- NEW VIEW for PDF to Excel ---
def pdf_to_excel_view(request):
    # Clear session data
    if request.method == 'GET' or 'pdffile_p2e' in request.FILES:
        if 'p2e_xlsx_b64' in request.session: del request.session['p2e_xlsx_b64']
        if 'p2e_xlsx_filename' in request.session: del request.session['p2e_xlsx_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_p2e_xlsx' in request.POST:
            xlsx_data_b64 = request.session.get('p2e_xlsx_b64')
            xlsx_filename = request.session.get('p2e_xlsx_filename', 'extracted_tables.xlsx')
            if xlsx_data_b64:
                try:
                    xlsx_data = base64.b64decode(xlsx_data_b64.encode('ascii'))
                    # Correct MIME type for .xlsx
                    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    response = HttpResponse(xlsx_data, content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="{xlsx_filename}"'
                    # Clean up session
                    if 'p2e_xlsx_b64' in request.session: del request.session['p2e_xlsx_b64']
                    if 'p2e_xlsx_filename' in request.session: del request.session['p2e_xlsx_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve generated Excel file.")
            else:
                messages.error(request, "No generated Excel file found to download.")
            return redirect('pdf_tools:pdf_to_excel')

        # --- Handle Conversion ---
        else:
            uploaded_file = request.FILES.get('pdffile_p2e') # Unique name
            # --- Get Options ---
            page_mode = request.POST.get('page_selection_mode', 'all')
            page_string = request.POST.get('specific_pages', '').strip()
            extraction_method = request.POST.get('extraction_method', 'lattice') # lattice or stream
            # --- End Get Options ---

            # --- File Validation ---
            if not uploaded_file: messages.error(request, "No PDF file uploaded."); return redirect('pdf_tools:pdf_to_excel')
            if uploaded_file.size > MAX_UPLOAD_SIZE: messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB."); return redirect('pdf_tools:pdf_to_excel')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_PDF_EXTENSIONS: messages.error(request, f"Invalid file type '{ext}'. Only PDF allowed."); return redirect('pdf_tools:pdf_to_excel')
            if uploaded_file.content_type not in ALLOWED_PDF_MIMES: messages.warning(request, f"File might not be a valid PDF (MIME: {uploaded_file.content_type}).")
            # --- End File Validation ---

            # --- Specific Pages Validation ---
            if page_mode == 'specific' and not page_string:
                 messages.error(request, "Please enter the specific pages or ranges to extract tables from.")
                 context = {'page_title': 'PDF to Excel Converter', 'prev_options': request.POST}
                 return render(request, 'pdf_tools/tool_pdf_to_excel.html', context)
             # Further range validation happens in logic function

            # --- Conversion ---
            print(f"Converting {uploaded_file.name} to Excel. Mode: {page_mode}, Pages: '{page_string}', Method: {extraction_method}")
            xlsx_data, output_filename, error_message = convert_pdf_to_excel(
                pdf_file=uploaded_file,
                page_selection_mode=page_mode,
                page_string=page_string,
                extraction_method=extraction_method
            )
            # --- End Conversion ---

            context = { 'page_title': 'PDF to Excel Converter' }

            if xlsx_data and output_filename:
                print("PDF->Excel Conversion successful, storing XLSX in session.")
                xlsx_data_b64 = base64.b64encode(xlsx_data).decode('ascii')
                request.session['p2e_xlsx_b64'] = xlsx_data_b64
                request.session['p2e_xlsx_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_filename'] = uploaded_file.name
                messages.success(request, "Tables extracted successfully to Excel!")
            else:
                print(f"PDF->Excel function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to extract tables from PDF.")

            context['prev_options'] = request.POST
            return render(request, 'pdf_tools/tool_pdf_to_excel.html', context)

    # --- GET Request Handling ---
    else:
        context = {
            'page_title': 'PDF to Excel Converter',
            'conversion_success': request.session.get('p2e_xlsx_b64') is not None,
            'download_filename': request.session.get('p2e_xlsx_filename'),
            'original_filename': None
        }
        return render(request, 'pdf_tools/tool_pdf_to_excel.html', context)
    







# pdf_tools/views.py
# ... (other imports) ...
# --- NEW IMPORT ---
from .pdf_to_pptx_logic import convert_pdf_to_pptx_images
# --- END NEW IMPORT ---
# ...

# --- Existing Views ---
# ...

# --- NEW VIEW for PDF to PowerPoint ---
def pdf_to_pptx_view(request):
    # Clear session data
    if request.method == 'GET' or 'pdffile_p2p' in request.FILES: # Use unique input name
        if 'p2p_pptx_b64' in request.session: del request.session['p2p_pptx_b64']
        if 'p2p_pptx_filename' in request.session: del request.session['p2p_pptx_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_p2p_pptx' in request.POST:
            pptx_data_b64 = request.session.get('p2p_pptx_b64')
            pptx_filename = request.session.get('p2p_pptx_filename', 'converted.pptx')
            if pptx_data_b64:
                try:
                    pptx_data = base64.b64decode(pptx_data_b64.encode('ascii'))
                    # Correct MIME type for .pptx
                    content_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    response = HttpResponse(pptx_data, content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="{pptx_filename}"'
                    # Clean up session
                    if 'p2p_pptx_b64' in request.session: del request.session['p2p_pptx_b64']
                    if 'p2p_pptx_filename' in request.session: del request.session['p2p_pptx_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve generated PowerPoint file.")
            else:
                messages.error(request, "No generated PowerPoint file found to download.")
            return redirect('pdf_tools:pdf_to_pptx')

        # --- Handle Conversion ---
        else:
            uploaded_file = request.FILES.get('pdffile_p2p') # Unique name
            # --- Get Options ---
            dpi = request.POST.get('dpi_preset', '150')
            page_mode = request.POST.get('page_selection_mode', 'all')
            page_string = request.POST.get('specific_pages', '').strip()
            # --- End Get Options ---

            # --- File Validation ---
            if not uploaded_file: messages.error(request, "No PDF file uploaded."); return redirect('pdf_tools:pdf_to_pptx')
            if uploaded_file.size > MAX_UPLOAD_SIZE: messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB."); return redirect('pdf_tools:pdf_to_pptx')
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_PDF_EXTENSIONS: messages.error(request, f"Invalid file type '{ext}'. Only PDF allowed."); return redirect('pdf_tools:pdf_to_pptx')
            if uploaded_file.content_type not in ALLOWED_PDF_MIMES: messages.warning(request, f"File might not be a valid PDF (MIME: {uploaded_file.content_type}).")
            # --- End File Validation ---

            # --- Specific Pages Validation ---
            if page_mode == 'specific' and not page_string:
                 messages.error(request, "Please enter the specific pages or ranges to convert.")
                 context = {'page_title': 'Convert PDF to PowerPoint', 'prev_options': request.POST}
                 return render(request, 'pdf_tools/tool_pdf_to_pptx.html', context)
             # Full range validation happens in logic function

            # --- Conversion ---
            print(f"Converting {uploaded_file.name} to PPTX images. DPI: {dpi}, Mode: {page_mode}, Pages: '{page_string}'")
            pptx_data, output_filename, error_message = convert_pdf_to_pptx_images(
                pdf_file=uploaded_file,
                dpi_str=dpi,
                page_selection_mode=page_mode,
                page_string=page_string
            )
            # --- End Conversion ---

            context = { 'page_title': 'Convert PDF to PowerPoint' }

            if pptx_data and output_filename:
                print("PDF->PPTX Conversion successful, storing PPTX in session.")
                pptx_data_b64 = base64.b64encode(pptx_data).decode('ascii')
                request.session['p2p_pptx_b64'] = pptx_data_b64
                request.session['p2p_pptx_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_filename'] = uploaded_file.name
                messages.success(request, "PDF converted successfully to PowerPoint (as images)!")
            else:
                print(f"PDF->PPTX function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to convert PDF to PowerPoint.")

            context['prev_options'] = request.POST
            return render(request, 'pdf_tools/tool_pdf_to_pptx.html', context)

    # --- GET Request Handling ---
    else:
        context = {
            'page_title': 'Convert PDF to PowerPoint',
            'conversion_success': request.session.get('p2p_pptx_b64') is not None,
            'download_filename': request.session.get('p2p_pptx_filename'),
            'original_filename': None
        }
        return render(request, 'pdf_tools/tool_pdf_to_pptx.html', context)
    






# pdf_tools/views.py
# ... (other imports) ...
# --- NEW IMPORT ---
from .watermark_pdf_logic import add_watermark_to_pdf
# --- END NEW IMPORT ---
# ...
import re

# --- Existing Views ---
# ...

# --- NEW VIEW for Add Watermark ---
def watermark_pdf_view(request):
     # Clear session data
    if request.method == 'GET' or 'pdffile_watermark' in request.FILES:
        if 'watermarked_pdf_b64' in request.session: del request.session['watermarked_pdf_b64']
        if 'watermarked_filename' in request.session: del request.session['watermarked_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_watermarked' in request.POST:
            pdf_data_b64 = request.session.get('watermarked_pdf_b64')
            pdf_filename = request.session.get('watermarked_filename', 'watermarked.pdf')
            if pdf_data_b64:
                try:
                    pdf_data = base64.b64decode(pdf_data_b64.encode('ascii'))
                    response = HttpResponse(pdf_data, content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                    if 'watermarked_pdf_b64' in request.session: del request.session['watermarked_pdf_b64']
                    if 'watermarked_filename' in request.session: del request.session['watermarked_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve watermarked PDF.")
            else:
                messages.error(request, "No watermarked PDF found to download.")
            return redirect('pdf_tools:add_watermark')

        # --- Handle Watermarking ---
        else:
            uploaded_file = request.FILES.get('pdffile_watermark')
            watermark_type = request.POST.get('watermark_type', 'text')
            # Text Options
            text_content = request.POST.get('watermark_text', 'CONFIDENTIAL').strip()
            text_font_size = request.POST.get('font_size', '48')
            text_opacity = request.POST.get('text_opacity', '0.3')
            text_rotation = request.POST.get('rotation', '45')
            text_color = request.POST.get('text_color', '#888888')
            # Image Options
            image_file = request.FILES.get('watermark_image') # Separate file input
            image_opacity = request.POST.get('image_opacity', '0.3')
            image_scale = request.POST.get('image_scale', '80')

            # --- File Validation ---
            if not uploaded_file: messages.error(request, "No PDF file uploaded."); return redirect('pdf_tools:add_watermark')
            if uploaded_file.size > MAX_UPLOAD_SIZE: messages.error(request, f"PDF size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB."); return redirect('pdf_tools:add_watermark')
            # ... (add PDF extension/MIME checks if needed) ...
            if watermark_type == 'image' and not image_file:
                 messages.error(request, "Please upload a watermark image file.")
                 return render(request, 'pdf_tools/tool_watermark_pdf.html', {'page_title': 'Add Watermark to PDF', 'prev_options': request.POST, 'text_input': text_content}) # Re-render with error
            # --- End File Validation ---

             # --- Option Validation ---
            try:
                font_size_int = int(text_font_size) if text_font_size else 48
                opacity_float = float(text_opacity) if text_opacity else 0.3
                rotation_int = int(text_rotation) if text_rotation else 45
                img_opacity_float = float(image_opacity) if image_opacity else 0.3
                img_scale_int = int(image_scale) if image_scale else 80
                # Basic range checks
                if not (0 < font_size_int < 500): raise ValueError("Font size out of range")
                if not (0.0 <= opacity_float <= 1.0): raise ValueError("Text opacity must be between 0.0 and 1.0")
                if not (-360 <= rotation_int <= 360): raise ValueError("Rotation out of range")
                if not (0.0 <= img_opacity_float <= 1.0): raise ValueError("Image opacity must be between 0.0 and 1.0")
                if not (1 <= img_scale_int <= 200): raise ValueError("Image scale out of range (1-200)")
                # Basic hex color validation
                if not re.match(r'^#[0-9a-fA-F]{6}$', text_color): text_color = '#888888' # Default on invalid

            except ValueError as e:
                 messages.error(request, f"Invalid option value entered: {e}")
                 return render(request, 'pdf_tools/tool_watermark_pdf.html', {'page_title': 'Add Watermark to PDF', 'prev_options': request.POST, 'text_input': text_content})
             # --- End Option Validation ---


            # --- Watermarking ---
            print(f"Adding watermark to {uploaded_file.name}. Type: {watermark_type}")
            watermarked_data, output_filename, error_message = add_watermark_to_pdf(
                pdf_file=uploaded_file,
                watermark_type=watermark_type,
                text_content=text_content,
                font_size=font_size_int,
                text_opacity=opacity_float,
                text_rotation=rotation_int,
                text_color=text_color,
                image_file=image_file, # Pass image file object
                image_opacity=img_opacity_float,
                image_scale=img_scale_int
            )
            # --- End Watermarking ---

            context = { 'page_title': 'Add Watermark to PDF' }

            if watermarked_data and output_filename:
                print("Watermarking successful, storing PDF in session.")
                watermarked_pdf_b64 = base64.b64encode(watermarked_data).decode('ascii')
                request.session['watermarked_pdf_b64'] = watermarked_pdf_b64
                request.session['watermarked_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                context['original_filename'] = uploaded_file.name
                messages.success(request, "Watermark added successfully!")
            else:
                print(f"Watermark function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to add watermark to PDF.")

            context['prev_options'] = request.POST # Repopulate options
            context['text_input'] = text_content # Repopulate text
            return render(request, 'pdf_tools/tool_watermark_pdf.html', context)

    # --- GET Request Handling ---
    else:
        context = {
            'page_title': 'Add Watermark to PDF',
            'conversion_success': request.session.get('watermarked_pdf_b64') is not None,
            'download_filename': request.session.get('watermarked_filename'),
            'original_filename': None
        }
        return render(request, 'pdf_tools/tool_watermark_pdf.html', context)
    








# pdf_tools/views.py
# ... (other imports) ...
# --- NEW IMPORT ---
from .protect_pdf_logic import encrypt_pdf, MIN_PASSWORD_LENGTH
# --- END NEW IMPORT ---
# ... (constants etc.) ...

# --- Existing Views ---
# ...

# --- NEW VIEW for Protect PDF ---
def protect_pdf_view(request):
    # Clear session data
    if request.method == 'GET' or 'pdffile_protect' in request.FILES:
        if 'protected_pdf_b64' in request.session: del request.session['protected_pdf_b64']
        if 'protected_filename' in request.session: del request.session['protected_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_protected' in request.POST:
            pdf_data_b64 = request.session.get('protected_pdf_b64')
            pdf_filename = request.session.get('protected_filename', 'protected.pdf')
            if pdf_data_b64:
                try:
                    pdf_data = base64.b64decode(pdf_data_b64.encode('ascii'))
                    response = HttpResponse(pdf_data, content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                    # Clean up session
                    if 'protected_pdf_b64' in request.session: del request.session['protected_pdf_b64']
                    if 'protected_filename' in request.session: del request.session['protected_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve protected PDF.")
            else:
                messages.error(request, "No protected PDF found to download.")
            return redirect('pdf_tools:protect_pdf')

        # --- Handle Encryption ---
        else:
            uploaded_file = request.FILES.get('pdffile_protect') # Unique name
            password = request.POST.get('password', '')
            password_confirm = request.POST.get('password_confirm', '')

            # --- Input Validation ---
            context = { 'page_title': 'Protect PDF (Add Password)' } # Basic context for re-render
            error_found = False
            if not uploaded_file:
                messages.error(request, "No PDF file uploaded."); error_found = True
            else: # Only check file specifics if it exists
                context['original_filename'] = uploaded_file.name # Pass name for potential display
                if uploaded_file.size > MAX_UPLOAD_SIZE:
                    messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB."); error_found = True
                ext = os.path.splitext(uploaded_file.name)[1].lower()
                if ext not in ALLOWED_PDF_EXTENSIONS:
                    messages.error(request, f"Invalid file type '{ext}'. Only PDF allowed."); error_found = True
                if uploaded_file.content_type not in ALLOWED_PDF_MIMES:
                     messages.warning(request, f"File might not be a valid PDF (MIME: {uploaded_file.content_type}).")

            if not password:
                messages.error(request, "Password cannot be empty."); error_found = True
            elif len(password) < MIN_PASSWORD_LENGTH:
                 messages.error(request, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."); error_found = True
            elif password != password_confirm:
                messages.error(request, "Passwords do not match."); error_found = True

            if error_found:
                 return render(request, 'pdf_tools/tool_protect_pdf.html', context)
            # --- End Input Validation ---


            # --- Encryption ---
            print(f"Encrypting {uploaded_file.name}...")
            encrypted_data, output_filename, error_message = encrypt_pdf(
                pdf_file=uploaded_file,
                password=password # Pass the confirmed password
            )
            # --- End Encryption ---


            if encrypted_data and output_filename:
                print("Encryption successful, storing PDF in session.")
                encrypted_data_b64 = base64.b64encode(encrypted_data).decode('ascii')
                request.session['protected_pdf_b64'] = encrypted_data_b64
                request.session['protected_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                messages.success(request, "PDF encrypted successfully!")
            else:
                print(f"Encryption function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to encrypt PDF file.")

            # Re-render same page with results/errors
            return render(request, 'pdf_tools/tool_protect_pdf.html', context)

    # --- GET Request Handling ---
    else:
        context = {
            'page_title': 'Protect PDF (Add Password)',
            'conversion_success': request.session.get('protected_pdf_b64') is not None,
            'download_filename': request.session.get('protected_filename'),
        }
        return render(request, 'pdf_tools/tool_protect_pdf.html', context)
    









# pdf_tools/views.py
# ... (other imports) ...
# --- NEW IMPORT ---
from .unlock_pdf_logic import decrypt_pdf
# --- END NEW IMPORT ---
# ... (constants etc.) ...

# --- Existing Views ---
# ...

# --- NEW VIEW for Unlock PDF ---
def unlock_pdf_view(request):
    # Clear session data
    if request.method == 'GET' or 'pdffile_unlock' in request.FILES:
        if 'unlocked_pdf_b64' in request.session: del request.session['unlocked_pdf_b64']
        if 'unlocked_filename' in request.session: del request.session['unlocked_filename']

    if request.method == 'POST':
        # Handle Download
        if 'download_unlocked' in request.POST:
            pdf_data_b64 = request.session.get('unlocked_pdf_b64')
            pdf_filename = request.session.get('unlocked_filename', 'unlocked.pdf')
            if pdf_data_b64:
                try:
                    pdf_data = base64.b64decode(pdf_data_b64.encode('ascii'))
                    response = HttpResponse(pdf_data, content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                    # Clean up session
                    if 'unlocked_pdf_b64' in request.session: del request.session['unlocked_pdf_b64']
                    if 'unlocked_filename' in request.session: del request.session['unlocked_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve unlocked PDF.")
            else:
                messages.error(request, "No unlocked PDF found to download.")
            return redirect('pdf_tools:unlock_pdf')

        # --- Handle Unlock Attempt ---
        else:
            uploaded_file = request.FILES.get('pdffile_unlock') # Unique name
            password = request.POST.get('password', '') # Password needed to unlock

            # --- Input Validation ---
            context = { 'page_title': 'Unlock PDF (Remove Password)' }
            error_found = False
            if not uploaded_file:
                messages.error(request, "No PDF file uploaded."); error_found = True
            else: # Only check file specifics if it exists
                context['original_filename'] = uploaded_file.name
                if uploaded_file.size > MAX_UPLOAD_SIZE:
                    messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB."); error_found = True
                ext = os.path.splitext(uploaded_file.name)[1].lower()
                if ext not in ALLOWED_PDF_EXTENSIONS:
                    messages.error(request, f"Invalid file type '{ext}'. Only PDF allowed."); error_found = True
                # MIME check less crucial here, PyPDF2 will handle errors

            if not password:
                messages.error(request, "Password is required to unlock the PDF."); error_found = True

            if error_found:
                 return render(request, 'pdf_tools/tool_unlock_pdf.html', context)
            # --- End Input Validation ---

            # --- Decryption ---
            print(f"Attempting to unlock {uploaded_file.name}...")
            unlocked_data, output_filename, error_message = decrypt_pdf(
                pdf_file=uploaded_file,
                password=password
            )
            # --- End Decryption ---

            if unlocked_data and output_filename:
                print("Unlock successful, storing PDF in session.")
                unlocked_data_b64 = base64.b64encode(unlocked_data).decode('ascii')
                request.session['unlocked_pdf_b64'] = unlocked_data_b64
                request.session['unlocked_filename'] = output_filename

                context['conversion_success'] = True
                context['download_filename'] = output_filename
                messages.success(request, "PDF unlocked successfully!")
            else:
                print(f"Unlock function returned error: {error_message}")
                context['conversion_success'] = False
                messages.error(request, error_message or "Failed to unlock PDF file.")

            # Re-render same page with results/errors
            return render(request, 'pdf_tools/tool_unlock_pdf.html', context)

    # --- GET Request Handling ---
    else:
        context = {
            'page_title': 'Unlock PDF (Remove Password)',
            'conversion_success': request.session.get('unlocked_pdf_b64') is not None,
            'download_filename': request.session.get('unlocked_filename'),
        }
        return render(request, 'pdf_tools/tool_unlock_pdf.html', context)