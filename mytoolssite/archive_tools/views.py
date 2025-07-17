# archive_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse # Not needed for download yet
from django.contrib import messages
from .zip_lister_logic import list_zip_contents # Import the logic
import os

MAX_UPLOAD_SIZE = 100 * 1024 * 1024 # ZIP files can be large, adjust as needed (100MB)
ALLOWED_ZIP_EXTENSIONS = ['.zip']
ALLOWED_ZIP_MIMES = ['application/zip', 'application/x-zip-compressed']

def zip_list_view(request):
    context = {
        'page_title': 'ZIP File Viewer / Lister',
        'zip_contents': None,
        'original_filename': None,
    }

    if request.method == 'POST':
        uploaded_file = request.FILES.get('zipfile') # Unique name

        # --- Validation ---
        if not uploaded_file:
            messages.error(request, "No ZIP file uploaded.")
            return render(request, 'archive_tools/tool_zip_lister.html', context) # Re-render form

        if uploaded_file.size > MAX_UPLOAD_SIZE:
             messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
             return render(request, 'archive_tools/tool_zip_lister.html', context)

        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in ALLOWED_ZIP_EXTENSIONS:
            messages.error(request, f"Invalid file type '{ext}'. Only ZIP files allowed.")
            return render(request, 'archive_tools/tool_zip_lister.html', context)

        # Check MIME type (can be less reliable for ZIP)
        if uploaded_file.content_type not in ALLOWED_ZIP_MIMES:
             # Allow 'application/octet-stream' as it's a common generic type
             if uploaded_file.content_type != 'application/octet-stream':
                 messages.warning(request, f"File might not be a valid ZIP (MIME type: {uploaded_file.content_type}). Trying anyway.")
        # --- End Validation ---

        # --- List Contents ---
        print(f"Listing contents of {uploaded_file.name}")
        zip_contents, error_message = list_zip_contents(uploaded_file)
        # --- End Listing ---

        context['original_filename'] = uploaded_file.name # Keep filename for display

        if error_message:
            print(f"ZIP Lister function returned error: {error_message}")
            messages.error(request, error_message)
            context['zip_contents'] = None
        elif zip_contents is not None: # Check explicitly for None vs empty list
            print("ZIP Lister successful.")
            context['zip_contents'] = zip_contents
            messages.success(request, f"Contents of '{uploaded_file.name}' listed successfully!")
        else: # Should ideally have error_message if None, but handle just in case
            messages.error(request, "Failed to list contents of the ZIP file.")
            context['zip_contents'] = None


    # Render for GET or POST (to show results or initial form)
    return render(request, 'archive_tools/tool_zip_lister.html', context)





# archive_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.conf import settings # To potentially define temp dir location
import tempfile # For temporary file handling
import mimetypes # For guessing download MIME type
import urllib.parse # For encoding filenames in URLs
from .zip_extractor_logic import list_zip_contents, extract_single_file_from_zip # Import BOTH logic functions
import os
import base64

MAX_UPLOAD_SIZE = 100 * 1024 * 1024
ALLOWED_ZIP_EXTENSIONS = ['.zip']
ALLOWED_ZIP_MIMES = ['application/zip', 'application/x-zip-compressed']

# --- UPDATED zip_extractor_view ---
def zip_extractor_view(request):
    # Clear session data on GET or new file upload
    if request.method == 'GET' or 'zipfile_extract' in request.FILES:
        # Clean up previous temp file if its path is in session
        old_temp_path = request.session.pop('temp_zip_path', None)
        if old_temp_path and os.path.exists(old_temp_path):
            try:
                os.remove(old_temp_path)
                print(f"[Cleanup] Removed old temp ZIP: {old_temp_path}")
            except OSError as e:
                print(f"[Cleanup] Error removing old temp ZIP {old_temp_path}: {e}")
        # Clear other session keys
        request.session.pop('zip_file_list', None)
        request.session.pop('zip_original_filename', None)

    context = { 'page_title': 'ZIP Extractor' }

    if request.method == 'POST':
        uploaded_file = request.FILES.get('zipfile_extract')

        # --- File Validation (same as before) ---
        if not uploaded_file: # ... etc ...
            messages.error(request, "No ZIP file uploaded.")
            return render(request, 'archive_tools/tool_zip_extractor.html', context)
        if uploaded_file.size > MAX_UPLOAD_SIZE: # ... etc ...
             messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
             return render(request, 'archive_tools/tool_zip_extractor.html', context)
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in ALLOWED_ZIP_EXTENSIONS: # ... etc ...
            messages.error(request, f"Invalid file type '{ext}'. Only ZIP allowed.")
            return render(request, 'archive_tools/tool_zip_extractor.html', context)
        # --- End File Validation ---

        temp_zip_path = None
        try:
            # --- Save Uploaded File Temporarily ---
            # delete=False is important so the file persists after the 'with' block
            # We need to manage deletion ourselves now.
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip", prefix="zipextract_") as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_zip_path = temp_file.name # Get the full path
            print(f"[ZIP Extract View] Saved uploaded file to temporary path: {temp_zip_path}")
            # --- End Save File ---

            # --- List Contents (using the temporary file path) ---
            # Reopen the temp file for reading by the logic function
            with open(temp_zip_path, 'rb') as temp_file_read:
                file_list, error_message = list_zip_contents(temp_file_read)
            # --- End Listing ---

            if file_list is not None:
                print("Listing successful, storing info in session.")
                # Store temp path and file list in session
                request.session['temp_zip_path'] = temp_zip_path
                request.session['zip_file_list'] = file_list
                request.session['zip_original_filename'] = uploaded_file.name

                context['file_list'] = file_list
                context['original_filename'] = uploaded_file.name
                context['extraction_done'] = True # Flag to show results
                messages.success(request, f"Successfully listed {len(file_list)} items. Click filename to download.")
            else:
                print(f"Listing failed: {error_message}")
                context['file_list'] = None
                context['extraction_done'] = True # Still show results section for error
                messages.error(request, error_message or "Failed to list ZIP contents.")
                # Clean up temp file if listing failed right away
                if temp_zip_path and os.path.exists(temp_zip_path):
                    os.remove(temp_zip_path)

            return render(request, 'archive_tools/tool_zip_extractor.html', context)

        except Exception as e:
            print(f"Error during file saving or listing: {e}")
            messages.error(request, f"An error occurred processing the file: {e}")
            # Clean up temp file if error occurred during saving/listing
            if temp_zip_path and os.path.exists(temp_zip_path):
                 try: os.remove(temp_zip_path)
                 except OSError: pass
            return render(request, 'archive_tools/tool_zip_extractor.html', context)

    # --- GET Request Handling ---
    else:
        # Check if results are in session from a previous POST
        if 'temp_zip_path' in request.session and 'zip_file_list' in request.session:
             context['file_list'] = request.session.get('zip_file_list')
             context['original_filename'] = request.session.get('zip_original_filename')
             context['extraction_done'] = True
        return render(request, 'archive_tools/tool_zip_extractor.html', context)


# --- NEW VIEW for Downloading Single Entry ---
def download_zip_entry_view(request, internal_path):
    """Handles download request for a specific file inside the temp ZIP."""
    temp_zip_path = request.session.get('temp_zip_path')
    original_zip_filename = request.session.get('zip_original_filename', 'archive.zip') # Get original name for context

    if not temp_zip_path:
        messages.error(request, "Session expired or invalid. Please upload the ZIP file again.")
        return redirect('archive_tools:zip_extractor')

    # Basic security check: ensure the path seems like a temp file we created
    # A more robust check would validate against a known temp directory from settings
    temp_dir = tempfile.gettempdir()
    if not os.path.abspath(temp_zip_path).startswith(os.path.abspath(temp_dir)):
         messages.error(request, "Invalid temporary file path.")
         return redirect('archive_tools:zip_extractor')

    if not os.path.exists(temp_zip_path):
         messages.error(request, "Temporary ZIP file not found (might have expired). Please upload again.")
         # Clean up session keys if file is missing
         request.session.pop('temp_zip_path', None)
         request.session.pop('zip_file_list', None)
         request.session.pop('zip_original_filename', None)
         return redirect('archive_tools:zip_extractor')

    # Decode the internal path from URL (might contain spaces, special chars)
    # Although <path:> converter handles slashes, manual decoding might be needed
    # depending on how it was encoded in the template. Let's assume direct use for now.
    decoded_internal_path = urllib.parse.unquote(internal_path)

    print(f"Attempting to extract '{decoded_internal_path}' from '{temp_zip_path}'")

    file_data, output_filename, error_message = extract_single_file_from_zip(
        zip_file_path=temp_zip_path,
        internal_filename=decoded_internal_path
    )

    if file_data and output_filename:
        # Guess MIME type for download
        content_type, _ = mimetypes.guess_type(output_filename)
        if not content_type:
            content_type = 'application/octet-stream' # Default binary type

        response = HttpResponse(file_data, content_type=content_type)
        try:
            # Try to encode filename properly for header
            output_filename.encode('ascii')
            file_expr = f'filename="{output_filename}"'
        except UnicodeEncodeError:
            # Handle non-ASCII filenames using RFC 5987 encoding
            encoded_fn = urllib.parse.quote(output_filename)
            file_expr = f"filename*=utf-8''{encoded_fn}"

        response['Content-Disposition'] = f'attachment; {file_expr}'
        print(f"Serving file '{output_filename}' with type '{content_type}'")

        # --- Cleanup Decision ---
        # Option 1: Delete immediately (user can't download another file from same zip)
        # try:
        #     os.remove(temp_zip_path)
        #     request.session.pop('temp_zip_path', None)
        #     request.session.pop('zip_file_list', None)
        #     request.session.pop('zip_original_filename', None)
        #     print(f"Deleted temp file {temp_zip_path} after download.")
        # except OSError as e:
        #     print(f"Error deleting temp file {temp_zip_path} after download: {e}")

        # Option 2: Leave cleanup to session expiry / GET request cleanup / scheduled task
        # (Simpler for now, but leaves temp files longer)

        return response
    else:
        messages.error(request, error_message or "Failed to extract the selected file.")
        # Redirect back to the extractor page, keeping the session data
        return redirect('archive_tools:zip_extractor')
    










# archive_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .zip_extractor_logic import list_zip_contents, extract_single_file_from_zip
# --- NEW IMPORT ---
from .create_zip_logic import create_zip_archive
# --- END NEW IMPORT ---
# ... other imports (os, base64, tempfile, mimetypes, urllib.parse) ...
import os
import base64
import tempfile # Still needed for zip extractor download
import mimetypes
import urllib.parse

MAX_UPLOAD_SIZE = 100 * 1024 * 1024 # Limit total size for zip creation
ALLOWED_ZIP_EXTENSIONS = ['.zip']
ALLOWED_ZIP_MIMES = ['application/zip', 'application/x-zip-compressed']

# --- zip_extractor_view ---
# ...
# --- download_zip_entry_view ---
# ...

# --- NEW VIEW for Create ZIP ---
def create_zip_view(request):
    # Clear previous data
    if request.method == 'GET' or 'files_to_zip' in request.FILES:
        if 'created_zip_b64' in request.session: del request.session['created_zip_b64']
        if 'created_zip_filename' in request.session: del request.session['created_zip_filename']

    context = {
        'page_title': 'Create ZIP Archive',
        'prev_output_filename': request.POST.get('output_filename', 'archive') if request.method == 'POST' else 'archive', # Repopulate
    }

    if request.method == 'POST':
        # Handle Download Request
        if 'download_created_zip' in request.POST:
            zip_data_b64 = request.session.get('created_zip_b64')
            zip_filename = request.session.get('created_zip_filename', 'archive.zip')
            if zip_data_b64:
                try:
                    zip_data = base64.b64decode(zip_data_b64.encode('ascii'))
                    response = HttpResponse(zip_data, content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                    # Clean up session
                    if 'created_zip_b64' in request.session: del request.session['created_zip_b64']
                    if 'created_zip_filename' in request.session: del request.session['created_zip_filename']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve generated ZIP file.")
            else:
                messages.error(request, "No generated ZIP file found to download.")
            return redirect('archive_tools:create_zip')

        # --- Handle ZIP Creation ---
        else:
            uploaded_files = request.FILES.getlist('files_to_zip') # Unique name, multiple files
            output_filename_req = request.POST.get('output_filename', 'archive').strip()

            # --- Validation ---
            if not uploaded_files:
                messages.error(request, "No files selected to archive.")
                return render(request, 'archive_tools/tool_create_zip.html', context)

            total_size = 0
            for file in uploaded_files:
                total_size += file.size
                if total_size > MAX_UPLOAD_SIZE:
                     messages.error(request, f"Total file size exceeds {MAX_UPLOAD_SIZE // (1024*1024)} MB limit.")
                     return render(request, 'archive_tools/tool_create_zip.html', context)
            # No specific file type validation needed - accept anything
            # --- End Validation ---

            # --- Archive Creation ---
            print(f"Creating ZIP archive '{output_filename_req}.zip' with {len(uploaded_files)} files...")
            zip_data, final_output_filename, error_message = create_zip_archive(
                input_files=uploaded_files,
                output_filename=output_filename_req # Logic function adds .zip
            )
            # --- End Archive Creation ---

            if zip_data and final_output_filename:
                print("ZIP creation successful, storing in session.")
                zip_data_b64 = base64.b64encode(zip_data).decode('ascii')
                request.session['created_zip_b64'] = zip_data_b64
                request.session['created_zip_filename'] = final_output_filename

                context['creation_success'] = True
                context['download_filename'] = final_output_filename
                # Pass original filenames maybe?
                context['original_filenames'] = [f.name for f in uploaded_files]
                messages.success(request, "ZIP archive created successfully!")
            else:
                print(f"ZIP creation failed: {error_message}")
                context['creation_success'] = False
                messages.error(request, error_message or "Failed to create ZIP archive.")

            # Re-render same page
            return render(request, 'archive_tools/tool_create_zip.html', context)

    # --- GET Request Handling ---
    else:
        # Check if results are in session from previous attempt
        context['creation_success'] = request.session.get('created_zip_b64') is not None
        if context['creation_success']:
            context['download_filename'] = request.session.get('created_zip_filename')
            # No need to pass list of original filenames on GET

        return render(request, 'archive_tools/tool_create_zip.html', context)
    








# archive_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.conf import settings
import tempfile
import mimetypes
import urllib.parse
from .zip_extractor_logic import list_zip_contents, extract_single_file_from_zip
from .create_zip_logic import create_zip_archive
# --- NEW IMPORTS ---
from .rar_extractor_logic import list_rar_contents, extract_single_file_from_rar
# --- END NEW IMPORTS ---
import os
import base64

MAX_UPLOAD_SIZE_ZIP = 100 * 1024 * 1024
MAX_UPLOAD_SIZE_RAR = 100 * 1024 * 1024 # Separate limit if needed
ALLOWED_ZIP_EXTENSIONS = ['.zip']
ALLOWED_ZIP_MIMES = ['application/zip', 'application/x-zip-compressed']
ALLOWED_RAR_EXTENSIONS = ['.rar']
ALLOWED_RAR_MIMES = ['application/vnd.rar', 'application/x-rar-compressed', 'application/octet-stream'] # Octet-stream is common

# --- zip_extractor_view ---
# ...
# --- download_zip_entry_view ---
# ...
# --- create_zip_view ---
# ...

# --- NEW VIEW for RAR Extractor ---
def rar_extractor_view(request):
    # Clear previous session data
    if request.method == 'GET' or 'rarfile_extract' in request.FILES:
        old_temp_path = request.session.pop('temp_rar_path', None)
        if old_temp_path and os.path.exists(old_temp_path):
            try: os.remove(old_temp_path); print(f"[Cleanup] Removed old temp RAR: {old_temp_path}")
            except OSError as e: print(f"[Cleanup] Error removing old temp RAR {old_temp_path}: {e}")
        request.session.pop('rar_file_list', None)
        request.session.pop('rar_original_filename', None)

    context = { 'page_title': 'RAR Extractor (List Contents)' }

    if request.method == 'POST':
        uploaded_file = request.FILES.get('rarfile_extract') # Unique name

        # --- File Validation ---
        if not uploaded_file:
            messages.error(request, "No RAR file uploaded.")
            return render(request, 'archive_tools/tool_rar_extractor.html', context)
        if uploaded_file.size > MAX_UPLOAD_SIZE_RAR:
             messages.error(request, f"File size exceeds {MAX_UPLOAD_SIZE_RAR // (1024*1024)} MB.")
             return render(request, 'archive_tools/tool_rar_extractor.html', context)
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in ALLOWED_RAR_EXTENSIONS:
            messages.error(request, f"Invalid file type '{ext}'. Only RAR files allowed.")
            return render(request, 'archive_tools/tool_rar_extractor.html', context)
        # MIME type check can be less reliable for RAR
        if uploaded_file.content_type not in ALLOWED_RAR_MIMES:
             messages.warning(request, f"File type might be incorrect (MIME: {uploaded_file.content_type}). Trying anyway.")
        # --- End File Validation ---

        # --- List Contents (Logic now saves temp file) ---
        print(f"Listing contents for {uploaded_file.name}")
        file_list, temp_rar_path, error_message = list_rar_contents(uploaded_file)
        # --- End Listing ---

        context['original_filename'] = uploaded_file.name
        context['extraction_done'] = True # Mark that processing occurred

        if file_list is not None and temp_rar_path:
            print("RAR Listing successful, storing info in session.")
            request.session['temp_rar_path'] = temp_rar_path # Store path from logic function
            request.session['rar_file_list'] = file_list
            request.session['rar_original_filename'] = uploaded_file.name
            context['file_list'] = file_list
            messages.success(request, f"Successfully listed {len(file_list)} items. Click filename to download.")
        else:
            print(f"RAR Listing failed: {error_message}")
            context['file_list'] = None
            messages.error(request, error_message or "Failed to list contents of the RAR file.")
            # Temp file cleanup should have happened in logic function on error

        return render(request, 'archive_tools/tool_rar_extractor.html', context)

    # --- GET Request Handling ---
    else:
        # Check if results are in session from a previous POST
        if 'temp_rar_path' in request.session and 'rar_file_list' in request.session:
             context['file_list'] = request.session.get('rar_file_list')
             context['original_filename'] = request.session.get('rar_original_filename')
             context['extraction_done'] = True
        return render(request, 'archive_tools/tool_rar_extractor.html', context)


# --- NEW VIEW for Downloading Single RAR Entry ---
def download_rar_entry_view(request, internal_path):
    """Handles download request for a specific file inside the temp RAR."""
    temp_rar_path = request.session.get('temp_rar_path')
    original_rar_filename = request.session.get('rar_original_filename', 'archive.rar')

    if not temp_rar_path:
        messages.error(request, "Session expired or invalid. Please upload the RAR file again.")
        return redirect('archive_tools:rar_extractor')

    # Security check (as before)
    temp_dir = tempfile.gettempdir()
    if not os.path.abspath(temp_rar_path).startswith(os.path.abspath(temp_dir)):
         messages.error(request, "Invalid temporary file path.")
         return redirect('archive_tools:rar_extractor')

    if not os.path.exists(temp_rar_path):
         messages.error(request, "Temporary RAR file not found. Please upload again.")
         request.session.pop('temp_rar_path', None)
         request.session.pop('rar_file_list', None)
         request.session.pop('rar_original_filename', None)
         return redirect('archive_tools:rar_extractor')

    # Decode path
    decoded_internal_path = urllib.parse.unquote(internal_path)

    print(f"Attempting to extract '{decoded_internal_path}' from '{temp_rar_path}'")

    file_data, output_filename, error_message = extract_single_file_from_rar(
        rar_file_path=temp_rar_path,
        internal_filename=decoded_internal_path
    )

    if file_data and output_filename:
        content_type, _ = mimetypes.guess_type(output_filename)
        if not content_type: content_type = 'application/octet-stream'

        response = HttpResponse(file_data, content_type=content_type)
        try:
            output_filename.encode('ascii')
            file_expr = f'filename="{output_filename}"'
        except UnicodeEncodeError:
            encoded_fn = urllib.parse.quote(output_filename)
            file_expr = f"filename*=utf-8''{encoded_fn}"
        response['Content-Disposition'] = f'attachment; {file_expr}'

        # Cleanup decision (Leave for now - cleanup happens on next upload/GET)
        print(f"Serving file '{output_filename}' with type '{content_type}'")
        return response
    else:
        messages.error(request, error_message or "Failed to extract the selected file.")
        return redirect('archive_tools:rar_extractor')