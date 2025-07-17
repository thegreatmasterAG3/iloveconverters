# pdf_tools/pdf_to_word_logic.py
import io
import os
from pdf2docx import Converter # Import the main converter class
import re

def parse_page_ranges_for_pdf2docx(page_string, total_pages):
    """
    Parses a string like '1, 3-5, 8' into start/end page indices (0-based)
    suitable for pdf2docx (which takes start/end, not a list of indices).
    Finds the minimum start and maximum end page from the selection.
    Returns None, None, error if invalid.
    """
    if not page_string:
        return None, None, "Page range string cannot be empty."

    min_start_page_zero_based = total_pages # Initialize high
    max_end_page_zero_based = -1 # Initialize low

    parts = re.split(r'[,\s]+', page_string)
    for part in parts:
        part = part.strip()
        if not part: continue

        current_start = -1
        current_end = -1

        if '-' in part: # Range
            try:
                start, end = map(int, part.split('-', 1))
                if start < 1 or end < 1: return None, None, f"Page numbers must be positive: '{part}'."
                if start > end: return None, None, f"Invalid range: start > end in '{part}'."
                if start > total_pages or end > total_pages: return None, None, f"Page out of bounds (max {total_pages}): '{part}'."
                current_start = start - 1
                current_end = end - 1 # Keep end as inclusive for now
            except ValueError: return None, None, f"Invalid range format: '{part}'."
        else: # Single page
            try:
                page_num = int(part)
                if page_num < 1: return None, None, f"Page number must be positive: '{part}'."
                if page_num > total_pages: return None, None, f"Page out of bounds (max {total_pages}): '{part}'."
                current_start = page_num - 1
                current_end = page_num - 1
            except ValueError: return None, None, f"Invalid page number: '{part}'."

        # Update overall min/max
        if current_start != -1:
            min_start_page_zero_based = min(min_start_page_zero_based, current_start)
        if current_end != -1:
            max_end_page_zero_based = max(max_end_page_zero_based, current_end)

    # Check if any valid pages were found
    if max_end_page_zero_based == -1:
        return None, None, "No valid pages specified in the range."

    # pdf2docx uses start/end (inclusive, 0-based) for the *entire* range to process
    # It doesn't support non-contiguous ranges directly in one go.
    # We return the min start and max end found.
    # Note: This means if user enters "1, 5", pages 1-5 will be processed by pdf2docx.
    # This is a limitation we accept for V1 using this library method.
    print(f"pdf2docx will process pages from index {min_start_page_zero_based} to {max_end_page_zero_based}")
    return min_start_page_zero_based, max_end_page_zero_based, None


def convert_pdf_to_word(pdf_file, page_selection_mode='all', page_string=None):
    """
    Converts an uploaded PDF file to a DOCX file using pdf2docx.

    Args:
        pdf_file: Django UploadedFile object.
        page_selection_mode (str): 'all' or 'specific'.
        page_string (str): Comma/space separated pages/ranges if mode is 'specific'.

    Returns:
        tuple: (bytes: DOCX content or None,
                str: output filename or None,
                str: error message or None)
    """
    if not pdf_file:
        return None, None, "No PDF file provided."

    output_buffer = io.BytesIO()
    output_filename = "converted_document.docx"

    # pdf2docx prefers working with file paths, let's save temporarily
    # (Could also try passing stream directly if library supports it well)
    temp_pdf_path = None
    try:
        # Save uploaded file to a temporary location
        # Using NamedTemporaryFile ensures it gets cleaned up mostly
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            for chunk in pdf_file.chunks():
                temp_pdf.write(chunk)
            temp_pdf_path = temp_pdf.name
        print(f"[PDF->Word Logic] Saved temp PDF to: {temp_pdf_path}")

        # Determine page range for pdf2docx
        start_page_idx = None
        end_page_idx = None
        # First, get total pages *before* parsing range string
        try:
             from PyPDF2 import PdfReader # Use PyPDF2 just for page count and encryption check
             pdf_file.seek(0)
             reader_check = PdfReader(pdf_file)
             if reader_check.is_encrypted:
                 if not reader_check.decrypt(''):
                     raise ValueError(f"Cannot process encrypted file '{pdf_file.name}' without password.")
             total_pages = len(reader_check.pages)
        except Exception as page_count_err:
             print(f"[PDF->Word Logic] Error getting page count: {page_count_err}")
             return None, None, "Could not read the PDF file to determine page count."

        if page_selection_mode == 'specific':
            start_page_idx, end_page_idx, error = parse_page_ranges_for_pdf2docx(page_string, total_pages)
            if error:
                return None, None, error
            # pdf2docx uses start/end parameters which are 0-based *inclusive*
            # Our parser returns max end index, so use end_page_idx directly
            kwargs = {'start': start_page_idx, 'end': end_page_idx}
            print(f"[PDF->Word Logic] Converting pages {start_page_idx+1} to {end_page_idx+1}")

        else: # 'all' pages
            kwargs = {'start': 0, 'end': None} # None means end of document
            print("[PDF->Word Logic] Converting all pages.")


        # --- Use pdf2docx Converter ---
        cv = Converter(temp_pdf_path)
        # Convert to buffer - pass start/end if specific pages needed
        cv.convert(output_buffer, **kwargs)
        cv.close() # Important to close the converter object
        # --- End Conversion ---

        print("[PDF->Word Logic] Conversion successful.")
        output_buffer.seek(0)

        base_name = os.path.splitext(pdf_file.name)[0]
        if page_selection_mode == 'specific':
             output_filename = f"{base_name}_pages_{start_page_idx+1}-{end_page_idx+1}.docx"
        else:
             output_filename = f"{base_name}_converted.docx"

        return output_buffer.getvalue(), output_filename, None

    except Exception as e:
        print(f"Error during PDF to Word conversion: {e}")
        import traceback
        traceback.print_exc()
        # More specific error messages could be added based on common pdf2docx errors
        return None, None, f"An error occurred during conversion: {e}"
    finally:
        # --- Clean up temporary PDF file ---
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
                print(f"[PDF->Word Logic] Deleted temp PDF: {temp_pdf_path}")
            except OSError as e:
                print(f"[PDF->Word Logic] Error deleting temp PDF {temp_pdf_path}: {e}")
        # --- End Cleanup ---