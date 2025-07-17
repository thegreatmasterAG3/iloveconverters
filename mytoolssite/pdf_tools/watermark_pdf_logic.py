# pdf_tools/watermark_pdf_logic.py
import io
import os
import math
import re
import tempfile # Need tempfile if using path approach
# Ensure libraries are installed: pip install pypdf2 reportlab Pillow
try:
    from PyPDF2 import PdfReader, PdfWriter
    PYPDF2_AVAILABLE = True
except ImportError:
    print("WARNING: PyPDF2 not found. PDF merging/reading may fail.")
    PYPDF2_AVAILABLE = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm, inch # Use units for clarity
    from reportlab.lib.colors import Color
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase.ttfonts import TTFont # For custom fonts later
    from reportlab.pdfbase import pdfmetrics
    REPORTLAB_AVAILABLE = True
except ImportError:
    print("WARNING: reportlab not found. Text watermark generation will fail.")
    REPORTLAB_AVAILABLE = False

try:
    from PIL import Image as PILImage
    PILLOW_AVAILABLE = True
except ImportError:
     print("WARNING: Pillow not found. Image processing/info will fail.")
     PILLOW_AVAILABLE = False


def create_text_watermark_pdf(text, page_width_pt, page_height_pt, font_size=48, opacity=0.3, rotation=45, color_hex='#888888'):
    """ Creates a temporary PDF page containing only the rotated text watermark. """
    if not REPORTLAB_AVAILABLE: return None # Check dependency

    packet = io.BytesIO()
    # Use Point (pt) as unit since page dimensions are in points
    can = canvas.Canvas(packet, pagesize=(page_width_pt, page_height_pt))

    # Convert hex to RGB (0-1 range for reportlab)
    try:
        hex_c = color_hex.lstrip('#')
        if len(hex_c) != 6: raise ValueError("Invalid hex color format")
        r = int(hex_c[0:2], 16) / 255.0
        g = int(hex_c[2:4], 16) / 255.0
        b = int(hex_c[4:6], 16) / 255.0
        fill_color = Color(r, g, b, alpha=opacity)
    except Exception as color_err:
        print(f"Warning: Invalid color hex '{color_hex}', using default gray. Error: {color_err}")
        fill_color = Color(0.5, 0.5, 0.5, alpha=opacity) # Default gray on error

    can.setFillColor(fill_color)
    # Use standard PDF fonts available in ReportLab
    # Could add logic later to register/use custom TTF fonts if needed
    font_name = 'Helvetica'
    can.setFont(font_name, font_size)

    # Center and rotate
    can.translate(page_width_pt / 2, page_height_pt / 2) # Move origin to center
    can.rotate(rotation) # Rotate
    # Adjust position slightly based on font metrics if needed, center is usually good enough
    can.drawCentredString(0, 0, text) # Draw centered at the new origin (0,0)

    can.save()
    packet.seek(0)
    # Return a PdfReader object for the watermark page
    try:
        return PdfReader(packet)
    except Exception as e:
        print(f"Error creating PdfReader from text watermark canvas: {e}")
        return None


def create_image_watermark_pdf(image_file, page_width_pt, page_height_pt, opacity=0.3, scale_percent=80):
    """ Creates a temporary PDF page containing only the scaled/transparent image watermark. """
    if not REPORTLAB_AVAILABLE or not PILLOW_AVAILABLE: return None # Check dependencies

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width_pt, page_height_pt))
    img_pil = None
    img_buffer = None

    try:
        image_file.seek(0)
        # Read image data into a buffer first
        img_buffer = io.BytesIO(image_file.read())
        img_buffer.seek(0)

        # Use Pillow to get image info from the buffer
        img_pil = PILImage.open(img_buffer)
        img_pil.load() # Ensure image data is loaded
        img_width_px, img_height_px = img_pil.size

        # Calculate dimensions in points (standard PDF unit, 72 points per inch)
        # Use Pillow's DPI info if available, otherwise default to 72
        dpi_x, dpi_y = img_pil.info.get('dpi', (72, 72))
        if dpi_x <= 0: dpi_x = 72 # Sanity check DPI
        if dpi_y <= 0: dpi_y = 72
        img_width_pt = (img_width_px / dpi_x) * 72
        img_height_pt = (img_height_px / dpi_y) * 72

        # Calculate available area based on scale percentage
        max_width_pt = page_width_pt * (scale_percent / 100.0)
        max_height_pt = page_height_pt * (scale_percent / 100.0)

        # Calculate scaling factor to fit within bounds while maintaining aspect ratio
        scale = 1.0
        if img_width_pt > 0 and img_height_pt > 0:
            scale = min(max_width_pt / img_width_pt, max_height_pt / img_height_pt)
        # Don't scale up image watermark by default, maybe add option later
        scale = min(scale, 1.0)

        final_width_pt = img_width_pt * scale
        final_height_pt = img_height_pt * scale

        # Center position
        pos_x = (page_width_pt - final_width_pt) / 2
        pos_y = (page_height_pt - final_height_pt) / 2

        # Set transparency/alpha for the whole canvas state
        can.setFillAlpha(opacity)
        # Note: setFillAlpha affects subsequent drawing. If you draw text AFTER image,
        # you might need to reset alpha with can.setFillAlpha(1.0)

        # Use ImageReader with the buffer (rewind first!)
        img_buffer.seek(0)
        img_rl = ImageReader(img_buffer) # Pass the buffer

        # Draw image, mask='auto' attempts to use PNG alpha channel
        can.drawImage(img_rl, pos_x, pos_y, width=final_width_pt, height=final_height_pt, mask='auto', preserveAspectRatio=True)
        print("[Watermark Logic] Drew image watermark to canvas.")

    except Exception as img_err:
        print(f"[Watermark Logic] Error processing image watermark: {img_err}")
        import traceback
        traceback.print_exc()
        return None # Indicate failure
    finally:
        # Clean up PIL image and buffer
        if img_pil:
            try: img_pil.close()
            except Exception: pass
        if img_buffer:
            try: img_buffer.close()
            except Exception: pass

    can.save()
    packet.seek(0)
    # Return PdfReader object
    try:
        watermark_pdf = PdfReader(packet)
        print("[Watermark Logic] Created image watermark PDF page.")
        return watermark_pdf
    except Exception as reader_err:
        print(f"[Watermark Logic] Error reading generated watermark PDF: {reader_err}")
        return None


def add_watermark_to_pdf(pdf_file, watermark_type='text',
                         text_content="CONFIDENTIAL", font_size=48, text_opacity=0.3, text_rotation=45, text_color='#888888',
                         image_file=None, image_opacity=0.3, image_scale=80):
    """
    Adds a text or image watermark to each page of a PDF.

    Returns:
        tuple: (bytes: Watermarked PDF or None, str: output filename or None, str: error msg or None)
    """
    if not PYPDF2_AVAILABLE:
        return None, None, "Server configuration error: PDF manipulation library (PyPDF2) missing."
    if not pdf_file:
        return None, None, "No PDF file provided."
    if watermark_type == 'image' and not image_file:
        return None, None, "No watermark image file provided."

    output_buffer = io.BytesIO()
    output_filename = "watermarked_document.pdf"
    pdf_reader = None
    watermark_pdf_reader = None # To hold the generated watermark page

    try:
        pdf_file.seek(0)
        pdf_reader = PdfReader(pdf_file)
        pdf_writer = PdfWriter()
        total_pages = len(pdf_reader.pages)
        print(f"[Watermark Logic] Opened '{pdf_file.name}', pages: {total_pages}")

        if pdf_reader.is_encrypted:
             return None, None, "Cannot watermark encrypted PDF files."

        # --- Create the watermark page (once) ---
        first_page = pdf_reader.pages[0]
        # Use CropBox or MediaBox? MediaBox is the physical page size.
        # CropBox is the visible area, usually same but can differ. Use MediaBox for safety.
        media_box = first_page.mediabox
        width_pt = float(media_box.width)
        height_pt = float(media_box.height)
        print(f"[Watermark Logic] PDF Page Size (points): {width_pt} x {height_pt}")

        if watermark_type == 'text':
            watermark_pdf_reader = create_text_watermark_pdf(
                text=text_content,
                page_width_pt=width_pt,
                page_height_pt=height_pt,
                font_size=font_size,
                opacity=text_opacity,
                rotation=text_rotation,
                color_hex=text_color
            )
            if not watermark_pdf_reader: raise ValueError("Failed to create text watermark PDF.")
        elif watermark_type == 'image':
             watermark_pdf_reader = create_image_watermark_pdf(
                 image_file=image_file,
                 page_width_pt=width_pt,
                 page_height_pt=height_pt,
                 opacity=image_opacity,
                 scale_percent=image_scale
             )
             if not watermark_pdf_reader: raise ValueError("Failed to create image watermark PDF.")
        else:
            return None, None, "Invalid watermark type specified."

        watermark_page = watermark_pdf_reader.pages[0]
        print("[Watermark Logic] Watermark page created.")

        # --- Merge watermark onto each page ---
        for i in range(total_pages):
            try:
                page = pdf_reader.pages[i]
                # Merge watermark UNDER the existing content
                # Need PyPDF2 >= 3.0 for this simple merge
                page.merge_page(watermark_page) # Defaults to overlaying (last on top)
                # To place UNDER (more like a watermark), you might need more complex layer manipulation
                # or create a new page and add watermark then original content.
                # For simplicity V1, let's overlay. User can adjust opacity.
                pdf_writer.add_page(page)
                print(f"[Watermark Logic] Merged watermark onto page {i+1}")
            except Exception as merge_err:
                 print(f"[Watermark Logic] Error merging watermark on page {i+1}: {merge_err}")
                 # Add original page without watermark on error?
                 pdf_writer.add_page(pdf_reader.pages[i])


        # Write the final PDF
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)

        base_name = os.path.splitext(pdf_file.name)[0]
        output_filename = f"{base_name}_watermarked.pdf"

        print("[Watermark Logic] Watermarking successful.")
        return output_buffer.getvalue(), output_filename, None

    except Exception as e:
        print(f"Error during PDF watermarking process: {e}")
        import traceback
        traceback.print_exc()
        return None, None, f"An unexpected error occurred: {e}"
    # No specific cleanup needed for PyPDF2 writer/reader from streams