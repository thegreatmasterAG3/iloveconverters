# image_tools/webp_to_jpg_converter.py
import io
import os
from PIL import Image

def convert_webp_to_jpg(webp_file, background_color=(255, 255, 255), quality=90):
    """
    Converts an uploaded WebP file object to JPG format.

    Args:
        webp_file: A Django UploadedFile object (validated as WebP).
        background_color (tuple): RGB tuple for background if WebP has transparency.
        quality (int): The quality setting for the output JPG (1-95).

    Returns:
        tuple: (bytes: JPG content or None,
                str: output filename or None,
                str: error message or None)
    """
    if not webp_file:
        return None, None, "No WebP file provided."

    img = None
    img_rgb = None
    try:
        webp_file.seek(0)
        img = Image.open(webp_file)
        # Ensure the format is indeed WebP after opening
        if img.format != 'WEBP':
             print(f"[WebP->JPG Convert] Warning: Input file format is not WEBP, it is {img.format}. Attempting conversion anyway.")
             # Allow conversion attempt from other formats if Pillow opened it

        print(f"[WebP->JPG Convert] Opened {webp_file.name}, mode: {img.mode}")

        # Handle transparency by creating a background and pasting onto it
        # Also convert other non-RGB modes
        if img.mode == 'RGBA' or 'A' in img.getbands():
            print(f"[WebP->JPG Convert] Handling transparency with background: {background_color}")
            # Create background image of the same size
            background = Image.new('RGB', img.size, background_color)
            # Paste the image onto the background using the alpha channel as mask if possible
            try:
                background.paste(img, mask=img.getchannel('A'))
            except ValueError: # Fallback if mask paste fails
                 background.paste(img, (0,0), img)
            img_rgb = background # Use the composed image
        elif img.mode != 'RGB':
            print(f"[WebP->JPG Convert] Converting mode {img.mode} to RGB")
            img_rgb = img.convert('RGB')
        else:
            img_rgb = img # Already RGB or equivalent

        # Save to an in-memory buffer as JPEG
        jpg_buffer = io.BytesIO()
        save_kwargs = {"format": "JPEG", "quality": quality, "optimize": True}
        print(f"[WebP->JPG Convert] Saving with options: {save_kwargs}")
        img_rgb.save(jpg_buffer, **save_kwargs)
        print("[WebP->JPG Convert] Saved to buffer.")

        # Construct output filename
        base_name = os.path.splitext(webp_file.name)[0]
        output_filename = f"{base_name}_converted.jpg"

        jpg_buffer.seek(0)
        print(f"[WebP->JPG Success] Output filename: {output_filename}")
        return jpg_buffer.getvalue(), output_filename, None

    except Exception as e:
        error_msg = f"An error occurred during conversion: {e}"
        if "cannot identify image file" in str(e) or "decoder webp not available" in str(e):
             print(f"Error: WebP format possibly not supported by Pillow installation or invalid file: {e}")
             error_msg = "Cannot process WebP file. Ensure it's valid and WebP support is installed."
        else:
            print(f"Error during WebP to JPG conversion: {e}")
            import traceback
            traceback.print_exc()

        return None, None, error_msg
    finally:
        if img:
            try: img.close()
            except Exception: pass
        # Close img_rgb only if it's a different object than img
        if img_rgb and img_rgb is not img:
             try: img_rgb.close()
             except Exception: pass
        print("[WebP->JPG Cleanup] Closed image objects.")