# pdf_tools/pdf_to_png_logic.py
import io
import os
import zipfile
import fitz # PyMuPDF
import re # For parsing page ranges

# DPI presets
DPI_OPTIONS = {
    "72": 72,
    "150": 150, # Default
    "300": 300,
}

def parse_page_ranges(page_string, total_pages):
    """
    Parses a string like '1, 3-5, 8' into a set of 0-based page indices.
    (Copied from split_pdf_logic, keep consistent)
    """
    indices = set()
    if not page_string:
        return None, "Page range string cannot be empty."
    parts = re.split(r'[,\s]+', page_string)
    for part in parts:
        part = part.strip();
        if not part: continue
        if '-' in part:
            try:
                start, end = map(int, part.split('-', 1))
                if start < 1 or end < 1: return None, f"Page numbers must be positive: '{part}'."
                if start > end: return None, f"Invalid range: start > end in '{part}'."
                if start > total_pages or end > total_pages: return None, f"Page number out of bounds (max {total_pages}): '{part}'."
                indices.update(range(start - 1, end))
            except ValueError: return None, f"Invalid range format: '{part}'. Use '3-5'."
        else:
            try:
                page_num = int(part)
                if page_num < 1: return None, f"Page number must be positive: '{part}'."
                if page_num > total_pages: return None, f"Page number out of bounds (max {total_pages}): '{part}'."
                indices.add(page_num - 1)
            except ValueError: return None, f"Invalid page number: '{part}'. Use numbers or '1, 3-5'."
    if not indices: return None, "No valid pages selected."
    return sorted(list(indices)), None

def convert_pdf_to_png_zip(pdf_file, dpi_str='150', page_selection_mode='all', page_string=None):
    """
    Converts selected pages of a PDF to PNG images and returns them in a ZIP archive.

    Args:
        pdf_file: Django UploadedFile object.
        dpi_str (str): Key for DPI_OPTIONS ('72', '150', '300').
        page_selection_mode (str): 'all' or 'specific'.
        page_string (str): Comma/space separated pages/ranges if mode is 'specific'.

    Returns:
        tuple: (bytes: ZIP archive content or None,
                str: output filename or None,
                str: error message or None)
    """
    if not pdf_file:
        return None, None, "No PDF file provided."

    dpi = DPI_OPTIONS.get(dpi_str, 150) # Get DPI value, default 150
    output_zip_buffer = io.BytesIO()
    output_filename_base = "pdf_to_png_images"
    output_zip_filename = f"{output_filename_base}.zip"

    doc = None # Initialize for finally block
    try:
        pdf_file.seek(0)
        # Read PDF data into memory for PyMuPDF
        pdf_data = pdf_file.read()
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        total_pages = len(doc)
        print(f"[PDF->PNG Logic] Opened '{pdf_file.name}', total pages: {total_pages}")

        # Handle encryption (PyMuPDF needs authentication)
        if doc.is_encrypted:
            # PyMuPDF requires password to proceed; cannot try empty like PyPDF2 easily
            doc.close() # Close document
            return None, None, f"File '{pdf_file.name}' is encrypted and password protected."

        # Determine which pages to convert (0-based indices)
        pages_to_convert = []
        if page_selection_mode == 'specific':
            parsed_indices, error = parse_page_ranges(page_string, total_pages)
            if error:
                doc.close()
                return None, None, error
            pages_to_convert = parsed_indices
            print(f"[PDF->PNG Logic] Specific pages selected (0-based): {pages_to_convert}")
        else: # 'all' pages
            pages_to_convert = list(range(total_pages))
            print(f"[PDF->PNG Logic] Converting all {total_pages} pages.")

        if not pages_to_convert:
             doc.close()
             return None, None, "No pages selected or found for conversion."

        # Create ZIP file in memory
        with zipfile.ZipFile(output_zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Determine padding for filenames based on total pages (e.g., 01, 02... or 001, 002...)
            num_digits = len(str(total_pages))
            base_pdf_name = os.path.splitext(pdf_file.name)[0]

            for i in pages_to_convert:
                try:
                    page = doc.load_page(i) # Load the page
                    print(f"[PDF->PNG Logic] Rendering page {i+1} at {dpi} DPI...")
                    # Render page to pixmap (image)
                    # matrix=fitz.Matrix(dpi/72, dpi/72) scales rendering resolution
                    # alpha=True preserves transparency
                    pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=True)

                    # Generate PNG filename within ZIP
                    # Format page number with leading zeros
                    png_filename_in_zip = f"{base_pdf_name}_page_{i+1:0{num_digits}d}.png"

                    # Get PNG image bytes from pixmap
                    png_bytes = pix.tobytes("png")
                    if png_bytes:
                        zipf.writestr(png_filename_in_zip, png_bytes)
                        print(f"[PDF->PNG Logic] Added '{png_filename_in_zip}' to ZIP.")
                    else:
                        print(f"[PDF->PNG Logic] Warning: Failed to get PNG bytes for page {i+1}.")
                        # Optionally add an error file to the zip?
                        # zipf.writestr(f"ERROR_page_{i+1}.txt", f"Failed to convert page {i+1} to PNG.")


                except Exception as page_err:
                     print(f"[PDF->PNG Logic] Error processing page {i+1}: {page_err}")
                     # Optionally add an error file to the zip for this page
                     try:
                        zipf.writestr(f"ERROR_page_{i+1}.txt", f"Failed to convert page {i+1}: {page_err}")
                     except Exception: pass # Ignore error during error reporting
                     continue # Try next page

        # Check if any files were actually added to the zip
        if not zipf.namelist():
            doc.close()
            return None, None, "No pages could be successfully converted and added to the ZIP file."

        output_zip_buffer.seek(0)
        print("[PDF->PNG Logic] ZIP file created successfully.")
        return output_zip_buffer.getvalue(), output_zip_filename, None # No error

    except Exception as e:
        print(f"Error during PDF to PNG conversion process: {e}")
        import traceback
        traceback.print_exc()
        return None, None, f"An unexpected error occurred: {e}"
    finally:
        if doc:
            try: doc.close()
            except Exception: pass
        print("[PDF->PNG Cleanup] Closed PDF document object.")