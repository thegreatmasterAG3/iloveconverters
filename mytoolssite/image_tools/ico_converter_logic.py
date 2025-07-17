# image_tools/ico_converter_logic.py
import io
import os
from PIL import Image

# Standard ICO sizes
ICO_SIZES = [16, 32, 48, 64, 128, 256]

def convert_image_to_ico(image_file, selected_sizes=None):
    """
    Converts an uploaded image file to ICO format, including specified sizes.

    Args:
        image_file: Django UploadedFile object.
        selected_sizes (list[int]): A list of integer sizes (e.g., [16, 32, 48])
                                     to include in the ICO file. Defaults to standard sizes.

    Returns:
        tuple: (bytes: ICO content or None,
                str: output filename or None,
                str: error message or None)
    """
    if not image_file:
        return None, None, "No image file provided."

    # Default sizes if none selected (or invalid input)
    if not selected_sizes or not isinstance(selected_sizes, list):
        selected_sizes = [16, 32, 48] # Sensible defaults

    # Ensure selected sizes are valid and within our standard list for Pillow's format
    valid_selected_sizes = [s for s in selected_sizes if isinstance(s, int) and s in ICO_SIZES]
    if not valid_selected_sizes:
         return None, None, "No valid icon sizes selected. Please choose at least one size (e.g., 16, 32, 48)."

    # Pillow expects sizes as a list of tuples [(size, size)]
    pillow_sizes = [(size, size) for size in valid_selected_sizes]
    print(f"[IMG->ICO Logic] Target ICO sizes: {pillow_sizes}")

    img = None
    output_buffer = io.BytesIO()
    output_filename = "favicon.ico"

    try:
        image_file.seek(0)
        img = Image.open(image_file)
        print(f"[IMG->ICO Logic] Opened '{image_file.name}', mode: {img.mode}")

        # No explicit conversion needed, Pillow handles it during save to ICO
        # It will convert to RGBA internally if needed.

        # Save to ICO format specifying the sizes
        # Pillow handles the resizing for each specified dimension.
        img.save(output_buffer, format='ICO', sizes=pillow_sizes)
        print("[IMG->ICO Logic] Saved to buffer as ICO.")

        output_buffer.seek(0)

        # Generate output filename based on original name
        base_name = os.path.splitext(image_file.name)[0]
        output_filename = f"{base_name}.ico"

        return output_buffer.getvalue(), output_filename, None # Success

    except Exception as e:
        print(f"Error during Image to ICO conversion: {e}")
        import traceback
        traceback.print_exc()
        # Check for specific errors if Pillow raises them (e.g., format not supported)
        if "encoder error" in str(e):
             error_msg = f"Failed to save as ICO. The image format might be unsupported by Pillow's ICO encoder. Try converting to PNG first. Error: {e}"
        else:
             error_msg = f"An unexpected error occurred: {e}"
        return None, None, error_msg
    finally:
        if img:
            try: img.close()
            except Exception: pass
        print("[IMG->ICO Cleanup] Closed image object.")