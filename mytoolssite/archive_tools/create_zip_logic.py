# archive_tools/create_zip_logic.py
import io
import os
import zipfile
import re # For filename sanitization

# Function to sanitize filename (basic example)
def sanitize_filename(filename):
    # Remove potentially harmful characters or path components
    filename = re.sub(r'[\\/*?:"<>|]', "", filename) # Remove invalid Windows chars
    filename = filename.replace('/', '_').replace('..', '_') # Replace separators
    # Limit length if necessary
    filename = filename[:200] # Limit length
    if not filename:
        filename = "download" # Default if sanitization removed everything
    return filename

def create_zip_archive(input_files, output_filename="archive.zip"):
    """
    Creates a ZIP archive in memory from a list of uploaded files.

    Args:
        input_files: A list of Django UploadedFile objects.
        output_filename (str): The desired name for the output ZIP file.

    Returns:
        tuple: (bytes: ZIP file content or None,
                str: sanitized output filename or None,
                str: error message or None)
    """
    if not input_files:
        return None, None, "No files provided to archive."

    # Sanitize and ensure the output filename ends with .zip
    sanitized_name = sanitize_filename(os.path.splitext(output_filename)[0])
    final_output_filename = f"{sanitized_name}.zip"

    zip_buffer = io.BytesIO()

    try:
        # Use ZIP_DEFLATED for compression (most common)
        # Use allowZip64=True for potentially large archives or many files
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
            print(f"[Create ZIP Logic] Creating '{final_output_filename}' with {len(input_files)} files...")
            for uploaded_file in input_files:
                try:
                    uploaded_file.seek(0) # Go to the start of the file stream
                    # Use the original filename as the name inside the zip
                    # Note: This doesn't handle duplicate filenames well without extra logic
                    zipf.writestr(uploaded_file.name, uploaded_file.read())
                    print(f"[Create ZIP Logic] Added '{uploaded_file.name}'")
                except Exception as write_err:
                    print(f"[Create ZIP Logic] Error writing file '{uploaded_file.name}' to ZIP: {write_err}")
                    # Optionally skip problematic files or fail entirely
                    # return None, None, f"Error adding file '{uploaded_file.name}' to archive."
                    continue # Skip this file

        zip_buffer.seek(0)
        print("[Create ZIP Logic] ZIP creation successful.")
        return zip_buffer.getvalue(), final_output_filename, None # Success

    except Exception as e:
        print(f"Error during ZIP creation process: {e}")
        import traceback
        traceback.print_exc()
        return None, None, f"An unexpected error occurred during ZIP creation: {e}"