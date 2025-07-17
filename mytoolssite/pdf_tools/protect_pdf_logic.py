# pdf_tools/protect_pdf_logic.py
import io
import os
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.errors import DependencyError # To catch potential crypto errors

# Min password length (optional)
MIN_PASSWORD_LENGTH = 6

def encrypt_pdf(pdf_file, password):
    """
    Encrypts an uploaded PDF file with the given password.

    Args:
        pdf_file: Django UploadedFile object.
        password (str): The password to use for encryption.

    Returns:
        tuple: (bytes: Encrypted PDF content or None,
                str: output filename or None,
                str: error message or None)
    """
    if not pdf_file:
        return None, None, "No PDF file provided."
    if not password or len(password) < MIN_PASSWORD_LENGTH:
         return None, None, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."

    output_buffer = io.BytesIO()
    output_filename = "protected_document.pdf"

    try:
        pdf_file.seek(0)
        pdf_reader = PdfReader(pdf_file)

        # Check if already encrypted (cannot easily re-encrypt)
        if pdf_reader.is_encrypted:
            return None, None, "The uploaded PDF is already encrypted. Cannot re-encrypt."

        pdf_writer = PdfWriter()

        # Add all pages from reader to writer
        # Method 1: Loop through pages (maybe slightly safer if reader modifies state?)
        # for page in pdf_reader.pages:
        #    pdf_writer.add_page(page)

        # Method 2: Append directly (more concise)
        pdf_writer.append_pages_from_reader(pdf_reader)

        print(f"[Protect PDF] Encrypting '{pdf_file.name}'...")
        # Encrypt the writer object - uses default algorithm (AES-128 or 256)
        pdf_writer.encrypt(password)

        # Write the encrypted PDF to the buffer
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)

        base_name = os.path.splitext(pdf_file.name)[0]
        output_filename = f"{base_name}_protected.pdf"

        print("[Protect PDF] Encryption successful.")
        return output_buffer.getvalue(), output_filename, None # Success

    except DependencyError as crypto_err:
         # This error occurs if PyPDF2's crypto requirements aren't met
         print(f"Cryptography library missing for PyPDF2: {crypto_err}")
         import traceback; traceback.print_exc()
         return None, None, "Server error: A required library for encryption is missing. Please contact support."
    except Exception as e:
        print(f"Error during PDF encryption process: {e}")
        import traceback
        traceback.print_exc()
        return None, None, f"An unexpected error occurred during encryption: {e}"
    # No finally block needed as stream/writer are handled in memory or closed by write