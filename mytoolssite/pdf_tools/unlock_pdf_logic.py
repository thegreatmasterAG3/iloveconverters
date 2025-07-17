# pdf_tools/unlock_pdf_logic.py
import io
import os
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.errors import DependencyError, FileNotDecryptedError

def decrypt_pdf(pdf_file, password):
    """
    Attempts to decrypt an uploaded PDF file with the given password.

    Args:
        pdf_file: Django UploadedFile object.
        password (str): The password to attempt decryption with.

    Returns:
        tuple: (bytes: Decrypted PDF content or None,
                str: output filename or None,
                str: error message or None)
    """
    if not pdf_file:
        return None, None, "No PDF file provided."
    if not password:
         return None, None, "Password is required to attempt unlocking."

    output_buffer = io.BytesIO()
    output_filename = "unlocked_document.pdf"
    pdf_reader = None # Initialize for potential error context

    try:
        pdf_file.seek(0)
        pdf_reader = PdfReader(pdf_file)

        # 1. Check if actually encrypted
        if not pdf_reader.is_encrypted:
            print("[Unlock PDF] File is not encrypted.")
            return None, None, "The provided PDF file is not password protected."

        # 2. Attempt decryption
        print(f"[Unlock PDF] Attempting decryption for '{pdf_file.name}'...")
        try:
            # decrypt() returns 1 for user password, 2 for owner password, 0 for failure
            decrypt_status = pdf_reader.decrypt(password)
            if decrypt_status <= 0: # Changed from == 0 to <= 0 for safety
                 print("[Unlock PDF] Decryption failed: Incorrect password.")
                 return None, None, "Incorrect password provided. Unable to unlock the PDF."
            else:
                 print(f"[Unlock PDF] Decryption successful (Status: {decrypt_status}).")
        except FileNotDecryptedError:
             print("[Unlock PDF] Decryption failed: Incorrect password (FileNotDecryptedError).")
             return None, None, "Incorrect password provided. Unable to unlock the PDF."
        except NotImplementedError as ni_err: # Handles unsupported encryption types
             print(f"[Unlock PDF] Unsupported encryption: {ni_err}")
             return None, None, f"Cannot unlock PDF: Unsupported encryption type ({ni_err})."


        # 3. Create new PDF without encryption
        pdf_writer = PdfWriter()
        # Append pages from the *decrypted* reader object
        pdf_writer.append_pages_from_reader(pdf_reader)

        # Write the decrypted PDF to the buffer (NO encrypt call)
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)

        base_name = os.path.splitext(pdf_file.name)[0]
        output_filename = f"{base_name}_unlocked.pdf"

        print("[Unlock PDF] Unlocked PDF created successfully.")
        return output_buffer.getvalue(), output_filename, None # Success

    except DependencyError as crypto_err:
         print(f"Cryptography library missing for PyPDF2: {crypto_err}")
         return None, None, "Server error: A required library for decryption is missing."
    except Exception as e:
        print(f"Error during PDF unlocking process: {e}")
        import traceback
        traceback.print_exc()
        # Check if it's likely a password issue even if not caught above
        if isinstance(e, FileNotDecryptedError) or 'password' in str(e).lower():
             return None, None, "Incorrect password or decryption failed."
        # Check if it's an invalid PDF file
        if 'Invalid PDF file' in str(e) or 'PdfReadError' in repr(e):
             return None, None, "Invalid or corrupted PDF file provided."
        return None, None, f"An unexpected error occurred: {e}"