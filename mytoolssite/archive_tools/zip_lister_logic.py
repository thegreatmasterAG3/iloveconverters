# archive_tools/zip_lister_logic.py
import io
import zipfile
from django.core.files.uploadedfile import UploadedFile

def list_zip_contents(zip_uploaded_file: UploadedFile):
    """
    Reads an uploaded ZIP file and lists its contents.

    Args:
        zip_uploaded_file: A Django UploadedFile object (validated as ZIP).

    Returns:
        tuple: (list: List of dicts [{'name': str, 'size': int}] or None,
                str: Error message or None)
    """
    if not zip_uploaded_file:
        return None, "No ZIP file provided."

    contents = []
    try:
        # PyPDF2 preferred reading from stream/bytes
        zip_uploaded_file.seek(0)
        # Read into memory buffer IF necessary, else pass stream directly if supported
        # zip_data = io.BytesIO(zip_uploaded_file.read())
        # zip_file = zipfile.ZipFile(zip_data, 'r')

        # Open directly from the stream-like object Django provides
        zip_file = zipfile.ZipFile(zip_uploaded_file, 'r')

        print(f"[ZIP Lister] Opened '{zip_uploaded_file.name}'.")

        # Check for encryption (basic check)
        # Note: More robust check might involve trying to read a file
        is_encrypted = False
        for info in zip_file.infolist():
             # Check flag bit 0 for encryption
             if info.flag_bits & 0x1:
                 is_encrypted = True
                 break
        if is_encrypted:
             print(f"[ZIP Lister] File '{zip_uploaded_file.name}' appears to be password protected.")
             return None, "Password protected ZIP files are not supported by the lister."

        # List contents
        for info in zip_file.infolist():
            # Basic security check: Skip entries with '..' or starting with '/'
            if '..' in info.filename or info.filename.startswith('/'):
                print(f"[ZIP Lister] Skipping potentially unsafe path: {info.filename}")
                continue
            contents.append({
                'name': info.filename,
                'size': info.file_size,
                'is_dir': info.is_dir(), # Check if it's a directory entry
            })

        print(f"[ZIP Lister] Found {len(contents)} items.")
        zip_file.close() # Close the zipfile object
        return contents, None # Success

    except zipfile.BadZipFile:
        print(f"[ZIP Lister] Error: Bad ZIP file '{zip_uploaded_file.name}'.")
        return None, "Invalid or corrupted ZIP file."
    except Exception as e:
        print(f"Error listing ZIP contents: {e}")
        import traceback
        traceback.print_exc()
        # Ensure file is closed if opened
        if 'zip_file' in locals() and zip_file:
             try: zip_file.close()
             except Exception: pass
        return None, f"An error occurred while reading the ZIP file: {e}"