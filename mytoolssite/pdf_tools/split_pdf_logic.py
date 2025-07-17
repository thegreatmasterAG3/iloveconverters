# pdf_tools/split_pdf_logic.py
import io
import os
from PyPDF2 import PdfReader, PdfWriter

def split_pdf_by_range(pdf_file, start_page, end_page):
    """
    Extracts a range of pages from an uploaded PDF file object.

    Args:
        pdf_file: A Django UploadedFile object (validated as PDF).
        start_page (int): The starting page number (1-based index).
        end_page (int): The ending page number (1-based index).

    Returns:
        tuple: (bytes: Extracted PDF content or None,
                str: output filename or None,
                str: error message or None)
    """
    if not pdf_file:
        return None, None, "No PDF file provided."

    pdf_writer = PdfWriter()
    output_buffer = io.BytesIO()
    output_filename = "split_document.pdf" # Default

    try:
        pdf_file.seek(0)
        pdf_reader = PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)
        print(f"[Split PDF Logic] Opened '{pdf_file.name}', total pages: {total_pages}")

        # --- Basic Validation (More robust validation in view is better) ---
        if start_page < 1:
            start_page = 1
        if end_page > total_pages:
            end_page = total_pages
        if start_page > end_page:
            return None, None, f"Invalid range: Start page ({start_page}) cannot be greater than end page ({end_page})."
        # --- End Basic Validation ---

        # Handle encryption (attempt with empty password)
        if pdf_reader.is_encrypted:
            try:
                if pdf_reader.decrypt("") == 0:
                     return None, None, f"File '{pdf_file.name}' is encrypted and could not be decrypted."
            except Exception as decrypt_err:
                 return None, None, f"Error decrypting file '{pdf_file.name}': {decrypt_err}"

        print(f"[Split PDF Logic] Extracting pages from {start_page} to {end_page}")
        # PyPDF2 uses 0-based index, user input is 1-based
        for i in range(start_page - 1, end_page):
            try:
                page = pdf_reader.pages[i]
                pdf_writer.add_page(page)
            except IndexError:
                 # Should not happen with validation, but as a fallback
                 print(f"[Split PDF Logic] Warning: Page index {i} out of bounds. Skipping.")
                 continue

        if len(pdf_writer.pages) == 0:
             return None, None, "No pages were extracted based on the provided range."

        # Write the new PDF to the buffer
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)

        # Generate output filename
        base_name = os.path.splitext(pdf_file.name)[0]
        output_filename = f"{base_name}_pages_{start_page}-{end_page}.pdf"

        print("[Split PDF Logic] Split successful.")
        return output_buffer.getvalue(), output_filename, None # No error

    except Exception as e:
        print(f"Error during PDF splitting process: {e}")
        import traceback
        traceback.print_exc()
        return None, None, f"An unexpected error occurred during splitting: {e}"
    # No finally needed as PyPDF2 handles closing internally with stream input