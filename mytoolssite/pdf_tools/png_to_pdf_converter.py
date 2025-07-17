# pdf_tools/png_to_pdf_converter.py
import io
import os
from PIL import Image
# Ensure fpdf2 is installed: pip install fpdf2
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    print("WARNING: fpdf2 not installed. PDF generation will fail.")
    FPDF_AVAILABLE = False

# Define page sizes in mm (FPDF default unit)
PAGE_SIZES = {
    "A4": (210, 297),
    "Letter": (215.9, 279.4),
    # Add more here: "Legal": (215.9, 355.6)
}

def convert_pngs_to_pdf(image_files, page_size_str='A4', orientation_pref='Auto', margin_mm=10):
    """
    Converts a list of uploaded PNG image files into a single PDF document using FPDF2.
    Attempts to preserve transparency.

    Args:
        image_files: List of Django UploadedFile objects (validated as PNGs).
        page_size_str (str): 'A4' or 'Letter'.
        orientation_pref (str): 'Auto', 'P', or 'L'.
        margin_mm (int): Margin size in mm.

    Returns:
        tuple: (bytes: PDF content or None, str: output filename or None, str: error message or None)
    """
    if not FPDF_AVAILABLE:
        return None, None, "PDF generation library (fpdf2) is not available on the server."
    if not image_files:
        return None, None, "No PNG files provided."

    page_width_mm, page_height_mm = PAGE_SIZES.get(page_size_str, PAGE_SIZES['A4'])
    pdf = FPDF(orientation='P', unit='mm', format=page_size_str)
    pdf.set_auto_page_break(auto=False, margin=0)
    output_buffer = io.BytesIO()
    output_filename = "converted_pngs.pdf"

    processed_files = [] # Keep track of successfully processed Pillow images for cleanup

    try:
        print(f"[PNG->PDF Logic] Processing {len(image_files)} files...")
        for uploaded_file in image_files:
            img = None # Define img in the loop scope for cleanup
            try:
                uploaded_file.seek(0)
                # Open with Pillow to check validity and get info
                img = Image.open(uploaded_file)
                img.load() # Load image data to catch potential errors early
                print(f"  Opened '{uploaded_file.name}', format: {img.format}, mode: {img.mode}, size: {img.size}")

                # Determine page orientation for this specific image
                img_width_px, img_height_px = img.size
                dpi = img.info.get('dpi', (96, 96))[0] # Try to get DPI, default 96
                img_width_mm = (img_width_px / dpi) * 25.4
                img_height_mm = (img_height_px / dpi) * 25.4

                current_page_width = page_width_mm
                current_page_height = page_height_mm
                orientation = 'P'

                if orientation_pref == 'P': orientation = 'P'
                elif orientation_pref == 'L': orientation = 'L'
                elif orientation_pref == 'Auto':
                    page_aspect = current_page_width / current_page_height
                    img_aspect = img_width_mm / img_height_mm if img_height_mm > 0 else 1
                    if img_aspect > page_aspect: orientation = 'L'
                    else: orientation = 'P'

                if orientation == 'L':
                    current_page_width = page_height_mm
                    current_page_height = page_width_mm

                pdf.add_page(orientation=orientation)

                # Calculate scaling
                max_width = current_page_width - 2 * margin_mm
                max_height = current_page_height - 2 * margin_mm
                if img_width_mm <= 0 or img_height_mm <= 0: continue # Skip zero-size images
                scale_ratio = min(max_width / img_width_mm, max_height / img_height_mm, 1.0)
                scaled_width = img_width_mm * scale_ratio
                scaled_height = img_height_mm * scale_ratio
                pos_x = (current_page_width - scaled_width) / 2
                pos_y = (current_page_height - scaled_height) / 2

                # Add image using fpdf2 - pass the file stream directly
                # fpdf2 handles PNG transparency reasonably well.
                uploaded_file.seek(0) # Rewind the original file stream
                pdf.image(uploaded_file, x=pos_x, y=pos_y, w=scaled_width, h=scaled_height, type='PNG', title=uploaded_file.name)
                print(f"  Added '{uploaded_file.name}' to PDF page.")
                processed_files.append(img) # Add PIL image to list *after* successful use

            except Exception as page_err:
                 print(f"[PNG->PDF Logic] Error processing file '{uploaded_file.name}': {page_err}")
                 # Close the specific image if it was opened
                 if img:
                     try: img.close()
                     except Exception: pass
                 # Continue to next file? Or fail all? Let's continue for now.
                 # Optionally add error indicator to output? For now, just skip.
                 continue # Skip this file

        if not processed_files: # Check if any images were successfully added
            return None, None, "No valid PNG images could be processed."

        # Write the final PDF
        pdf.output(output_buffer) # Writes to the BytesIO buffer
        output_buffer.seek(0)

        base_name = "converted_pngs" # Generic base name
        # Try to get first filename if exists for a slightly better name
        try:
             base_name = os.path.splitext(image_files[0].name)[0]
        except: pass
        output_filename = f"{base_name}.pdf"

        print("[PNG->PDF Logic] PDF generation successful.")
        return output_buffer.getvalue(), output_filename, None # Success

    except Exception as e:
        print(f"Error during PDF creation from PNGs: {e}")
        import traceback
        traceback.print_exc()
        return None, None, f"An unexpected error occurred: {e}"
    finally:
        # Clean up any Pillow image objects we opened successfully
        for img in processed_files:
            try: img.close()
            except Exception: pass
        print("[PNG->PDF Cleanup] Closed processed image objects.")