# image_tools/jpg_to_webp_converter.py
import io
import os
import zipfile
from PIL import Image

def convert_jpg_to_webp(image_files, quality=80, lossless=False):
    """
    Converts one or more JPG files to WebP format.

    Args:
        image_files: A list of Django UploadedFile objects (validated as JPG).
        quality (int): WebP quality setting (1-100) for lossy mode.
        lossless (bool): Whether to use lossless compression.

    Returns:
        tuple: (bytes: WebP image content or ZIP content or None,
                str: output filename (.webp or .zip) or None,
                str: error message or None,
                bool: True if output is ZIP, False otherwise)
    """
    if not image_files:
        return None, None, "No JPG files provided.", False

    output_files_data = {} # Store filename: bytes
    errors = []

    try:
        print(f"[JPG->WebP Logic] Processing {len(image_files)} files. Quality={quality}, Lossless={lossless}")
        for i, uploaded_file in enumerate(image_files):
            img = None # Define here for finally block
            try:
                uploaded_file.seek(0)
                img = Image.open(uploaded_file)
                # JPG is typically RGB or Grayscale (L). WebP supports these.
                # If somehow it's CMYK, convert it.
                if img.mode not in ['RGB', 'L']:
                    print(f"  Converting '{uploaded_file.name}' from {img.mode} to RGB...")
                    img = img.convert('RGB')

                print(f"  Processing '{uploaded_file.name}'...")

                output_buffer = io.BytesIO()
                save_kwargs = {
                    "format": "WEBP",
                    "quality": quality,
                    "lossless": lossless,
                    # "method": 4 # Optional: 0 (fast) to 6 (slowest/best)
                }
                if lossless:
                    # Quality is ignored in lossless mode by Pillow's WebP save
                    del save_kwargs['quality']
                    print(f"  Saving as Lossless WebP")
                else:
                     print(f"  Saving as Lossy WebP, Quality={quality}")

                img.save(output_buffer, **save_kwargs)

                # Store result
                base_name = os.path.splitext(uploaded_file.name)[0]
                output_filename = f"{base_name}.webp"
                output_files_data[output_filename] = output_buffer.getvalue()
                print(f"  Generated '{output_filename}'.")

            except Exception as e:
                print(f"Error converting file '{uploaded_file.name}': {e}")
                errors.append(f"Could not convert '{uploaded_file.name}': {e}")
                # Continue processing other files
            finally:
                 if img:
                     try: img.close()
                     except Exception: pass

        if not output_files_data: # No files converted successfully
            return None, None, errors[0] if errors else "No images could be converted.", False

        # --- Package results ---
        if len(output_files_data) == 1:
            # Single file success
            filename, data = list(output_files_data.items())[0]
            print(f"[JPG->WebP Logic] Returning single file: {filename}")
            return data, filename, errors[0] if errors else None, False # Return single file data
        else:
            # Multiple files success -> Create ZIP
            print(f"[JPG->WebP Logic] Creating ZIP for {len(output_files_data)} files.")
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename, data in output_files_data.items():
                    zipf.writestr(filename, data)

            zip_buffer.seek(0)
            zip_filename = "converted_webp_images.zip"
            print(f"[JPG->WebP Logic] Returning ZIP file: {zip_filename}")
            return zip_buffer.getvalue(), zip_filename, errors[0] if errors else None, True # Return ZIP data


    except Exception as e:
        print(f"Error during JPG to WebP batch conversion: {e}")
        import traceback
        traceback.print_exc()
        return None, None, f"An unexpected error occurred during conversion: {e}", False