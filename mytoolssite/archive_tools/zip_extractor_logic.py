# archive_tools/zip_extractor_logic.py
import zipfile
import io
import os # Needed for path splitting
import traceback # For detailed error logging

def list_zip_contents(zip_file_obj):
    """
    Reads a ZIP file object and returns a list of its contents (filenames/paths).

    Args:
        zip_file_obj: A file-like object (e.g., Django UploadedFile) for the ZIP archive.

    Returns:
        tuple: (list: List of filenames/paths or None, str: error message or None)
    """
    if not zip_file_obj:
        print("[ZIP List Logic] Error: No file object provided.")
        return None, "No file object provided."

    try:
        # Ensure we are at the start, necessary if the stream was read before
        try:
            zip_file_obj.seek(0)
        except Exception as seek_err:
            # Some stream types might not support seek, log warning but proceed
            print(f"[ZIP List Logic] Warning: Could not seek file object: {seek_err}")

        # Open the ZIP file from the file-like object
        # Using 'with' ensures the zipfile object is closed properly
        with zipfile.ZipFile(zip_file_obj, 'r') as zip_ref:
            # Check if the ZIP file is valid (basic check)
            test_result = zip_ref.testzip()
            if test_result is not None:
                print(f"[ZIP List Logic] Corrupt file detected: {test_result}")
                return None, f"The ZIP file appears to be corrupted or incomplete (Error on file: {test_result})."

            # Get the list of names (files and directories)
            file_list = zip_ref.namelist()
            # Sort alphabetically for consistent display
            file_list.sort()
            print(f"[ZIP List Logic] Found {len(file_list)} items.")
            return file_list, None # Success, no error message

    except zipfile.BadZipFile:
        print("[ZIP List Logic] Invalid ZIP file detected.")
        return None, "The uploaded file is not a valid ZIP archive."
    except Exception as e:
        print(f"[ZIP List Logic] Error reading ZIP file contents: {e}")
        traceback.print_exc() # Log the full traceback
        return None, f"An error occurred while reading the ZIP file: {e}"


def extract_single_file_from_zip(zip_file_path, internal_filename):
    """
    Extracts a single file from a ZIP archive specified by its path.

    Args:
        zip_file_path (str): The full path to the temporarily stored ZIP file.
        internal_filename (str): The path/name of the file *inside* the ZIP archive.

    Returns:
        tuple: (bytes: Extracted file content or None,
                str: original filename part or None,
                str: error message or None)
    """
    if not zip_file_path or not os.path.exists(zip_file_path):
         print(f"[ZIP Extract File] Error: Temporary ZIP path not found or invalid: {zip_file_path}")
         return None, None, "Temporary ZIP archive not found. Please upload again."

    try:
        # Open the ZIP file from the stored path
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Verify file existence within the archive (case-sensitive)
            all_files = zip_ref.namelist()
            if internal_filename not in all_files:
                print(f"[ZIP Extract File] Error: '{internal_filename}' not in archive list: {all_files}")
                # Attempt case-insensitive match as a fallback? Usually not recommended.
                return None, None, f"File '{internal_filename}' not found within the ZIP archive."

            # Check for directory traversal attempts (basic check)
            # normpath converts separators and collapses '..' etc.
            normalized_internal_path = os.path.normpath(internal_filename)
            if normalized_internal_path.startswith("..") or os.path.isabs(normalized_internal_path):
                print(f"[ZIP Extract File] Security Error: Invalid internal path detected: {internal_filename}")
                return None, None, "Invalid internal file path specified."

            # Extract the file content into memory using read()
            file_data = zip_ref.read(internal_filename)
            print(f"[ZIP Extract File] Extracted '{internal_filename}' ({len(file_data)} bytes)")

            # Get only the filename part for download suggestion
            output_filename = os.path.basename(internal_filename)
            # Handle cases where internal_filename might be just a directory name ending in '/'
            if not output_filename and internal_filename.endswith('/'):
                 print("[ZIP Extract File] Error: Attempted to extract a directory entry.")
                 return None, None, "Cannot download a directory, only individual files."

            return file_data, output_filename, None # Success, no error message

    except zipfile.BadZipFile:
        print(f"[ZIP Extract File] Error: The stored archive is invalid: {zip_file_path}")
        return None, None, "The stored archive file is invalid or corrupted."
    except KeyError:
         # This might happen if the filename has unusual encoding issues not handled by namelist() vs read()
         print(f"[ZIP Extract File] Error: KeyError finding '{internal_filename}' in {zip_file_path}")
         return None, None, f"Internal Error: Could not find '{internal_filename}' after listing (KeyError)."
    except Exception as e:
        print(f"Error extracting single file '{internal_filename}' from '{zip_file_path}': {e}")
        traceback.print_exc() # Log the full traceback
        return None, None, f"An error occurred while extracting the file: {e}"