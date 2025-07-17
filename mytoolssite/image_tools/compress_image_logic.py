# image_tools/compress_image_logic.py
import io
import os
from PIL import Image

def compress_image_file(image_file, quality=75):
    """
    Compresses an uploaded image file (JPG, PNG, WEBP).
    Keeps the original format. Applies quality setting mainly for JPG/WEBP.

    Args:
        image_file: Django UploadedFile object.
        quality (int): Target quality for lossy formats (1-95).

    Returns:
        tuple: (bytes: Compressed image content or None, str: output filename or None) on success,
               or (None, None) on error.
    """
    if not image_file:
        return None, None

    img = None
    try:
        image_file.seek(0)
        img = Image.open(image_file)
        original_format = img.format.upper() if img.format else 'PNG' # Guess PNG if unknown
        print(f"[Compress Start] Original: {image_file.name}, Format: {original_format}, Mode: {img.mode}")

        # Determine final output format (same as original)
        final_format = original_format
        if final_format == 'JPG': final_format = 'JPEG' # Pillow uses JPEG

        # Prepare output buffer and save options
        output_buffer = io.BytesIO()
        save_kwargs = {}
        needs_rgb_conversion = False

        if final_format == 'JPEG':
            save_kwargs['quality'] = quality
            save_kwargs['optimize'] = True
            if img.mode == 'RGBA' or 'A' in img.getbands():
                 needs_rgb_conversion = True
        elif final_format == 'PNG':
            save_kwargs['optimize'] = True
            # Could add compress_level based on an input 'effort' slider later
            # save_kwargs['compress_level'] = 6 # Example default
        elif final_format == 'WEBP':
             save_kwargs['quality'] = quality
             # save_kwargs['lossless'] = False # Default is lossy, use quality

        # Handle potential transparency before saving to non-alpha formats
        final_image_to_save = img
        if needs_rgb_conversion:
            print("[Compress Convert] Converting image to RGB for JPEG output...")
            background = Image.new('RGB', img.size, (255, 255, 255))
            try: background.paste(img, mask=img.getchannel('A'))
            except ValueError: background.paste(img, (0,0), img)
            final_image_to_save = background

        print(f"[Compress Save] Saving final image ({final_image_to_save.mode}) as {final_format} with options: {save_kwargs}")
        final_image_to_save.save(output_buffer, format=final_format, **save_kwargs)

        # Construct output filename
        base_name = os.path.splitext(image_file.name)[0]
        output_extension = final_format.lower()
        if output_extension == 'jpeg': output_extension = 'jpg'
        output_filename = f"{base_name}_compressed.{output_extension}"

        output_buffer.seek(0)
        print(f"[Compress Success] Output filename: {output_filename}, Original Size: {image_file.size}, Compressed Size: {output_buffer.getbuffer().nbytes}")
        return output_buffer.getvalue(), output_filename

    except Exception as e:
        print(f"Error during image compression: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    finally:
        # Cleanup
        if img:
            try: img.close()
            except Exception: pass
        # Only close final_image_to_save if it's a different object (the background)
        if final_image_to_save and final_image_to_save is not img:
             try: final_image_to_save.close()
             except Exception: pass
        print("[Compress Cleanup] Closed image objects.")