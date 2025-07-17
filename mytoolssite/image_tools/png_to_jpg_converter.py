# image_tools/png_to_jpg_converter.py
import io
from PIL import Image

def convert_png_to_jpg(png_file, background_color=(255, 255, 255), quality=95):
    """
    Converts an uploaded PNG file object to JPG format.

    Args:
        png_file: A Django UploadedFile object (validated as PNG).
        background_color (tuple): RGB tuple for background if PNG has transparency.
        quality (int): The quality setting for the output JPG (1-95).

    Returns:
        bytes: The generated JPG content as bytes, or None if an error occurs.
    """
    try:
        png_file.seek(0) # Ensure we're at the start
        img = Image.open(png_file)

        # Handle transparency by creating a background and pasting onto it
        if img.mode == 'RGBA' or 'A' in img.getbands():
            # Create background image of the same size
            background = Image.new('RGB', img.size, background_color)
            # Paste the RGBA image onto the background using the alpha channel as mask
            try: # Use alpha channel if available
                background.paste(img, mask=img.getchannel('A'))
            except ValueError: # Fallback if mask paste fails (e.g., maybe alpha isn't quite right)
                 background.paste(img, (0,0), img) # Simple paste without mask
            img_rgb = background
            img.close() # Close original
        # Convert other modes (like P with palette transparency) to RGB first
        elif img.mode != 'RGB':
            img_rgb = img.convert('RGB')
            img.close() # Close original
        else:
            img_rgb = img # Already RGB

        # Save to an in-memory buffer as JPEG
        jpg_buffer = io.BytesIO()
        img_rgb.save(jpg_buffer, format="JPEG", quality=quality, optimize=True) # Add optimize
        img_rgb.close() # Close the RGB image object

        jpg_buffer.seek(0)
        return jpg_buffer.getvalue()

    except Exception as e:
        print(f"Error during PNG to JPG conversion: {e}")
        import traceback
        traceback.print_exc()
        return None