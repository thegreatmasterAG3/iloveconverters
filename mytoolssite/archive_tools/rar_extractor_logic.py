# archive_tools/rar_extractor_logic.py
import os
import io
import rarfile # Requires 'unrar' command-line tool to be installed
import traceback
import tempfile

# rarfile.UNRAR_TOOL = r"C:\Users\krish\Downloads\winrar-x64-711\UnRAR.exe"

# --- Configure rarfile if unrar executable is not in PATH ---
# Example (adjust path as needed for your server environment):
# rarfile.UNRAR_TOOL = "/usr/local/bin/unrar"
# rarfile.PATH_SEP = '/' # Use '/' for Linux/macOS, might need '\\' for Windows

def list_rar_contents(rar_file_obj):
    """
    Reads a RAR file object and returns a list of its contents.

    Args:
        rar_file_obj: A file-like object for the RAR archive.

    Returns:
        tuple: (list: List of filenames/paths or None, str: error message or None)
    """
    if not rar_file_obj:
        return None, "No file object provided."

    # rarfile often works better with a filename path than a stream
    # So, we save the upload to a temporary file first.
    temp_rar_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".rar", prefix="rarextract_") as temp_file:
            rar_file_obj.seek(0)
            for chunk in rar_file_obj.chunks():
                temp_file.write(chunk)
            temp_rar_path = temp_file.name
        print(f"[RAR List Logic] Saved upload to temp path: {temp_rar_path}")

        # Check if rarfile thinks it's a RAR file
        if not rarfile.is_rarfile(temp_rar_path):
             os.remove(temp_rar_path) # Clean up temp file
             print("[RAR List Logic] File is not a valid RAR archive.")
             return None, "Uploaded file is not a valid RAR archive."

        with rarfile.RarFile(temp_rar_path, 'r') as rar_ref:
            # Check for encryption (basic check, might need password later)
            # rarfile doesn't have a simple is_encrypted property like zipfile.
            # Trying to list might fail on some encrypted headers.
            # We'll rely on the namelist() call failing or extract failing later.

            file_list = rar_ref.namelist()
            file_list.sort()
            print(f"[RAR List Logic] Found {len(file_list)} items.")
            # NOTE: We return the temp_rar_path so the view can store it in session
            return file_list, temp_rar_path, None # Success

    except rarfile.BadRarFile as e:
        print(f"[RAR List Logic] BadRarFile error: {e}")
        if temp_rar_path and os.path.exists(temp_rar_path): os.remove(temp_rar_path)
        return None, None, f"Invalid or corrupted RAR archive: {e}"
    except rarfile.NeedFirstVolume:
        print("[RAR List Logic] Multi-volume RAR not supported.")
        if temp_rar_path and os.path.exists(temp_rar_path): os.remove(temp_rar_path)
        return None, None, "Multi-volume RAR archives are not supported by this tool."
    except rarfile.NoRarEntry as e: # Might indicate encryption issues on listing
         print(f"[RAR List Logic] NoRarEntry error (check encryption?): {e}")
         if temp_rar_path and os.path.exists(temp_rar_path): os.remove(temp_rar_path)
         return None, None, f"Could not read entries. Is the archive password protected or corrupted?"
    except FileNotFoundError:
         # This can happen if the 'unrar' command is not found
         print("[RAR List Logic] 'unrar' command likely not found or rarfile misconfigured.")
         if temp_rar_path and os.path.exists(temp_rar_path): os.remove(temp_rar_path)
         return None, None, "Server configuration error: Cannot find 'unrar' tool. Please contact admin."
    except Exception as e:
        print(f"Error reading RAR file contents: {e}")
        traceback.print_exc()
        if temp_rar_path and os.path.exists(temp_rar_path): os.remove(temp_rar_path)
        return None, None, f"An error occurred while reading the RAR file: {e}"
    # Do NOT delete temp_rar_path here on success, the view needs it.


def extract_single_file_from_rar(rar_file_path, internal_filename):
    """
    Extracts a single file from a RAR archive path using the rarfile library.

    Args:
        rar_file_path (str): The full path to the temporarily stored RAR file.
        internal_filename (str): The path/name of the file *inside* the RAR archive.

    Returns:
        tuple: (bytes: Extracted file content or None, str: original filename or None, str: error message or None)
    """
    if not rar_file_path or not os.path.exists(rar_file_path):
         return None, None, "Temporary RAR archive not found. Please upload again."

    try:
        with rarfile.RarFile(rar_file_path, 'r') as rar_ref:
            # Check if the requested file exists (case-sensitive check)
            # Need to normalize paths for comparison if needed, rarfile usually uses '/'
            normalized_internal_path = internal_filename.replace('\\', '/')
            if normalized_internal_path not in rar_ref.namelist():
                print(f"[RAR Extract File] Error: '{normalized_internal_path}' not in archive.")
                return None, None, f"File '{internal_filename}' not found within the RAR archive."

             # Get info object to check if it's a directory
            info = rar_ref.getinfo(normalized_internal_path)
            if info.is_dir():
                print(f"[RAR Extract File] Error: Attempted to extract a directory: {normalized_internal_path}")
                return None, None, "Cannot download a directory, only individual files."

            # Extract the file content into memory using read()
            file_data = rar_ref.read(normalized_internal_path)
            print(f"[RAR Extract File] Extracted '{normalized_internal_path}' ({len(file_data)} bytes)")

            output_filename = os.path.basename(normalized_internal_path)
            return file_data, output_filename, None # Success

    except rarfile.BadRarFile as e:
        print(f"[RAR Extract File] BadRarFile error: {e}")
        return None, None, f"The stored archive file is invalid or corrupted: {e}"
    except rarfile.NoRarEntry as e:
         print(f"[RAR Extract File] NoRarEntry error (check encryption?): {e}")
         return None, None, f"Could not extract entry '{internal_filename}'. Is the archive password protected or corrupted?"
    except FileNotFoundError:
         print("[RAR Extract File] 'unrar' command likely not found or rarfile misconfigured.")
         return None, None, "Server configuration error: Cannot find 'unrar' tool."
    except Exception as e:
        print(f"Error extracting single file '{internal_filename}' from '{rar_file_path}': {e}")
        traceback.print_exc()
        return None, None, f"An error occurred while extracting the file: {e}"