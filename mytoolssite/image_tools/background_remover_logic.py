# image_tools/background_remover_logic.py
import io
import os
from rembg import new_session, remove # Import new_session too
from PIL import Image

def hex_to_rgb(hex_color):
    """Converts #ffffff hex to (255, 255, 255) tuple."""
    h = hex_color.lstrip('#')
    if len(h) != 6:
        return (255, 255, 255) # Default white on error
    try:
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return (255, 255, 255) # Default white on error

def remove_image_background(
    image_file,
    model_name="u2net", # Default model
    alpha_matting=False,
    bg_mode="transparent", # 'transparent' or 'color'
    bg_color_hex="#FFFFFF" # Default white if color mode selected
):
    """
    Removes the background from an uploaded image file using rembg,
    with options for model, alpha matting, and adding a solid background.

    Args:
        image_file: Django UploadedFile object.
        model_name (str): Name of the rembg model to use (e.g., 'u2net', 'u2netp').
        alpha_matting (bool): Whether to use alpha matting.
        bg_mode (str): 'transparent' or 'color'.
        bg_color_hex (str): Hex color string (e.g., '#ffffff') if bg_mode is 'color'.

    Returns:
        tuple: (bytes: Result PNG content or None,
                str: output filename or None,
                str: error message or None)
    """
    if not image_file:
        return None, None, "No image file provided."

    output_filename = "background_removed.png" # Default (always PNG output)

    # Create a session for the selected model
    # This helps manage model loading if switching models frequently
    try:
        session = new_session(model_name=model_name)
    except Exception as session_err:
         print(f"Error creating rembg session for model '{model_name}': {session_err}")
         return None, None, f"Could not load the selected AI model ({model_name})."

    img_no_bg_obj = None # To hold intermediate PIL image if adding background
    final_buffer = io.BytesIO()

    try:
        image_file.seek(0)
        input_bytes = image_file.read()
        print(f"[Remove BG] Read {len(input_bytes)} bytes from '{image_file.name}'. Model: {model_name}, Alpha Matting: {alpha_matting}, BG Mode: {bg_mode}")

        # --- Step 1: Remove background using rembg ---
        output_bytes_transparent = remove(
            input_bytes,
            alpha_matting=alpha_matting,
            session=session # Use the created session
        )
        print("[Remove BG] rembg processing complete.")

        if not output_bytes_transparent:
            return None, None, "Background removal processing failed (rembg returned empty)."

        # --- Step 2: Optionally add solid background ---
        if bg_mode == "color" and bg_color_hex:
            print(f"[Remove BG] Adding solid background color: {bg_color_hex}")
            rgb_color = hex_to_rgb(bg_color_hex)
            try:
                # Open the transparent result with Pillow
                img_no_bg_obj = Image.open(io.BytesIO(output_bytes_transparent))

                # Ensure it's RGBA before pasting
                if img_no_bg_obj.mode != 'RGBA':
                    img_no_bg_obj = img_no_bg_obj.convert('RGBA')

                # Create solid color background
                background = Image.new('RGB', img_no_bg_obj.size, rgb_color)

                # Paste the image with transparency onto the background
                # The alpha channel of img_no_bg_obj acts as the mask
                background.paste(img_no_bg_obj, (0, 0), img_no_bg_obj)

                # Save the result WITH background to the final buffer (as PNG)
                background.save(final_buffer, format="PNG", optimize=True)
                print("[Remove BG] Saved image with solid background.")

            except Exception as bg_err:
                 print(f"Error adding background color: {bg_err}")
                 # Fallback: return transparent version if adding bg failed?
                 final_buffer.write(output_bytes_transparent)
                 # return None, None, f"Error applying background color: {bg_err}"
        else:
             # If transparent background is requested, just use the direct rembg output
             final_buffer.write(output_bytes_transparent)
             print("[Remove BG] Using transparent background result.")


        # Generate output filename
        base_name = os.path.splitext(image_file.name)[0]
        output_filename = f"{base_name}_no_bg.png" # Always PNG

        final_buffer.seek(0)
        print(f"[Remove BG] Success. Output filename: {output_filename}")
        return final_buffer.getvalue(), output_filename, None # No error

    except ImportError as ie:
        print(f"ImportError during background removal: {ie}")
        return None, None, "Server error: Required library missing."
    except Exception as e:
        print(f"Error during background removal process: {e}")
        import traceback
        traceback.print_exc()
        error_msg = f"An unexpected error occurred: {e}"
        if "download" in str(e).lower():
            error_msg = "Error downloading AI model. Check server connectivity."
        return None, None, error_msg
    finally:
        # Clean up Pillow image if created
        if img_no_bg_obj:
            try: img_no_bg_obj.close()
            except Exception: pass
        # Note: We don't explicitly manage closing the rembg session here,
        # it might be better practice in long-running apps.