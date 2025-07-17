# pdf_tools/rotate_pdf_logic.py
import io
import os
from PyPDF2 import PdfReader, PdfWriter
import re # For parsing page ranges

def parse_page_ranges(page_string, total_pages):
    """
    Parses a string like '1, 3-5, 8' into a set of 0-based page indices.
    Validates against total_pages.
    """
    indices = set()
    if not page_string:
        return None, "Page range string cannot be empty."

    parts = re.split(r'[,\s]+', page_string) # Split by comma or space
    for part in parts:
        part = part.strip()
        if not part: continue

        if '-' in part: # It's a range
            try:
                start, end = map(int, part.split('-', 1))
                if start < 1 or end < 1:
                    return None, f"Page numbers must be positive in range '{part}'."
                if start > end:
                    return None, f"Invalid range: Start page > end page in '{part}'."
                if start > total_pages or end > total_pages:
                    return None, f"Page number out of bounds (max {total_pages}) in range '{part}'."
                # Add all pages in the range (0-based index)
                indices.update(range(start - 1, end))
            except ValueError:
                return None, f"Invalid page range format: '{part}'. Use numbers like '3-5'."
        else: # It's a single page
            try:
                page_num = int(part)
                if page_num < 1:
                    return None, f"Page number must be positive: '{part}'."
                if page_num > total_pages:
                    return None, f"Page number out of bounds (max {total_pages}): '{part}'."
                indices.add(page_num - 1) # Add 0-based index
            except ValueError:
                return None, f"Invalid page number: '{part}'. Use numbers or ranges like '1, 3-5'."

    if not indices:
        return None, "No valid pages selected."

    return sorted(list(indices)), None # Return sorted list of 0-based indices

def rotate_pdf_pages(pdf_file, angle, page_selection_mode='all', page_string=None):
    """
    Rotates selected pages in a PDF file.

    Args:
        pdf_file: Django UploadedFile object.
        angle (int): Rotation angle (90, 180, 270).
        page_selection_mode (str): 'all' or 'specific'.
        page_string (str): Comma/space separated pages/ranges like "1, 3-5" if mode is 'specific'.

    Returns:
        tuple: (bytes: Rotated PDF content or None,
                str: output filename or None,
                str: error message or None)
    """
    if not pdf_file:
        return None, None, "No PDF file provided."
    if angle not in [90, 180, 270]:
        return None, None, "Invalid rotation angle specified."

    output_buffer = io.BytesIO()
    output_filename = "rotated_document.pdf"

    try:
        pdf_file.seek(0)
        pdf_reader = PdfReader(pdf_file)
        pdf_writer = PdfWriter()
        total_pages = len(pdf_reader.pages)
        print(f"[Rotate PDF] Opened '{pdf_file.name}', total pages: {total_pages}")

        # Handle encryption
        if pdf_reader.is_encrypted:
            try:
                if pdf_reader.decrypt("") == 0:
                    return None, None, f"File '{pdf_file.name}' is encrypted and cannot be processed."
            except Exception as decrypt_err:
                return None, None, f"Error decrypting file '{pdf_file.name}': {decrypt_err}"

        # Determine which pages to rotate (0-based indices)
        pages_to_rotate = []
        if page_selection_mode == 'specific':
            parsed_indices, error = parse_page_ranges(page_string, total_pages)
            if error:
                return None, None, error
            pages_to_rotate = parsed_indices
            print(f"[Rotate PDF] Specific pages selected (0-based): {pages_to_rotate}")
        else: # 'all' pages
            pages_to_rotate = list(range(total_pages))
            print("[Rotate PDF] Rotating all pages.")

        # Process pages
        for i in range(total_pages):
            page = pdf_reader.pages[i]
            if i in pages_to_rotate:
                print(f"[Rotate PDF] Rotating page {i+1} by {angle} degrees.")
                page.rotate(angle) # Rotate the specific page object
            pdf_writer.add_page(page) # Add the (potentially rotated) page to the writer

        # Write the modified PDF
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)

        base_name = os.path.splitext(pdf_file.name)[0]
        output_filename = f"{base_name}_rotated.pdf"

        print("[Rotate PDF] Rotation successful.")
        return output_buffer.getvalue(), output_filename, None

    except Exception as e:
        print(f"Error during PDF rotation process: {e}")
        import traceback
        traceback.print_exc()
        return None, None, f"An unexpected error occurred during rotation: {e}"