# pdf_tools/pdf_to_jpg_logic.py
import io
import os
import zipfile
import fitz # PyMuPDF
import re
from PIL import Image # To save pixmap as JPG with quality settings

# DPI presets
DPI_OPTIONS = { "72": 72, "150": 150, "300": 300 }

def parse_page_ranges(page_string, total_pages):
    # (Same function as used in split_pdf_logic)
    indices = set()
    if not page_string: return None, "Page range string cannot be empty."
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


def convert_pdf_to_jpg_zip(pdf_file, dpi_str='150', quality=85, page_selection_mode='all', page_string=None):
    """
    Converts selected pages of a PDF to JPG images and returns them in a ZIP archive.

    Args:
        pdf_file: Django UploadedFile object.
        dpi_str (str): Key for DPI_OPTIONS ('72', '150', '300').
        quality (int): JPG quality setting (1-95).
        page_selection_mode (str): 'all' or 'specific'.
        page_string (str): Comma/space separated pages/ranges if mode is 'specific'.

    Returns:
        tuple: (bytes: ZIP archive content or None,
                str: output filename or None,
                str: error message or None)
    """
    if not pdf_file:
        return None, None, "No PDF file provided."

    dpi = DPI_OPTIONS.get(dpi_str, 150)
    output_zip_buffer = io.BytesIO()
    output_filename_base = "pdf_to_jpg_images"
    output_zip_filename = f"{output_filename_base}.zip"

    doc = None
    try:
        pdf_file.seek(0)
        pdf_data = pdf_file.read()
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        total_pages = len(doc)
        print(f"[PDF->JPG Logic] Opened '{pdf_file.name}', total pages: {total_pages}")

        if doc.is_encrypted:
            doc.close()
            return None, None, f"File '{pdf_file.name}' is encrypted and password protected."

        pages_to_convert = []
        if page_selection_mode == 'specific':
            parsed_indices, error = parse_page_ranges(page_string, total_pages)
            if error:
                doc.close()
                return None, None, error
            pages_to_convert = parsed_indices
            print(f"[PDF->JPG Logic] Specific pages selected (0-based): {pages_to_convert}")
        else:
            pages_to_convert = list(range(total_pages))
            print(f"[PDF->JPG Logic] Converting all {total_pages} pages.")

        if not pages_to_convert:
             doc.close()
             return None, None, "No pages selected or found for conversion."

        with zipfile.ZipFile(output_zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            num_digits = len(str(total_pages))
            base_pdf_name = os.path.splitext(pdf_file.name)[0]

            for i in pages_to_convert:
                try:
                    page = doc.load_page(i)
                    print(f"[PDF->JPG Logic] Rendering page {i+1} at {dpi} DPI...")
                    # Render to pixmap. Alpha=False since JPG doesn't support it.
                    pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=False)

                    # Generate JPG filename within ZIP
                    jpg_filename_in_zip = f"{base_pdf_name}_page_{i+1:0{num_digits}d}.jpg"

                    # Convert pixmap bytes to PIL Image to save as JPG with quality
                    # pix.samples contains the raw pixel data (e.g., RGB bytes)
                    # Need to know the mode (e.g., RGB, CMYK) - get_pixmap default is RGB if alpha=False
                    if pix.samples:
                        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        img_byte_arr = io.BytesIO()
                        pil_img.save(img_byte_arr, format="JPEG", quality=quality, optimize=True)
                        jpg_bytes = img_byte_arr.getvalue()
                        zipf.writestr(jpg_filename_in_zip, jpg_bytes)
                        print(f"[PDF->JPG Logic] Added '{jpg_filename_in_zip}' to ZIP.")
                        pil_img.close() # Close PIL image
                        img_byte_arr.close()
                    else:
                        print(f"[PDF->JPG Logic] Warning: Failed to get pixel data for page {i+1}.")
                        # zipf.writestr(f"ERROR_page_{i+1}.txt", f"Failed to convert page {i+1} to JPG.")

                except Exception as page_err:
                     print(f"[PDF->JPG Logic] Error processing page {i+1}: {page_err}")
                     try: zipf.writestr(f"ERROR_page_{i+1}.txt", f"Failed to convert page {i+1}: {page_err}")
                     except Exception: pass
                     continue

        if not zipf.namelist():
            doc.close()
            return None, None, "No pages could be successfully converted to JPG."

        output_zip_buffer.seek(0)
        print("[PDF->JPG Logic] ZIP file created successfully.")
        return output_zip_buffer.getvalue(), output_zip_filename, None

    except Exception as e:
        print(f"Error during PDF to JPG conversion process: {e}")
        import traceback
        traceback.print_exc()
        return None, None, f"An unexpected error occurred: {e}"
    finally:
        if doc:
            try: doc.close()
            except Exception: pass
        print("[PDF->JPG Cleanup] Closed PDF document object.")