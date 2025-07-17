# image_tools/watermark_logic.py
import io
import os
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
# Update this path to an accessible font file (TTF/OTF)
try:
    # Common paths - try one that exists or place a font in your static files
    # DEFAULT_FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf' # Linux Example
    DEFAULT_FONT_PATH = 'arial.ttf' # Windows Example (adjust if needed)
    # DEFAULT_FONT_PATH = finders.find('fonts/YourFontFile.ttf') # If using staticfiles finders
    _ = ImageFont.truetype(DEFAULT_FONT_PATH, 10)
    FONT_AVAILABLE = True
    print(f"Watermark Font Loaded: {DEFAULT_FONT_PATH}")
except IOError:
    print(f"WARNING: Default font '{DEFAULT_FONT_PATH}' not found. Text watermarking will fail.")
    DEFAULT_FONT_PATH = None
    FONT_AVAILABLE = False


# Text size presets relative to image height
TEXT_SIZE_PRESETS = {"S": 0.03, "M": 0.05, "L": 0.08}

# --- Helper Functions ---

def hex_to_rgba(hex_color, opacity):
    """Converts #RRGGBB to (R, G, B, A) tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6: return (128, 128, 128, int(opacity * 255))
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    a = int(opacity * 255)
    return (r, g, b, a)

def calculate_position(base_width, base_height, element_width, element_height, position_preset="BR", padding=10):
    """Calculates top-left (x, y) coords for placing element based on preset."""
    if position_preset == "TL": x, y = padding, padding
    elif position_preset == "TR": x, y = base_width - element_width - padding, padding
    elif position_preset == "BL": x, y = padding, base_height - element_height - padding
    elif position_preset == "C": x, y = (base_width - element_width) // 2, (base_height - element_height) // 2
    else: x, y = base_width - element_width - padding, base_height - element_height - padding # Bottom Right default
    return int(x), int(y)

# --- Main Watermark Function ---

def add_watermark(
    base_image_file, watermark_type='text', text_content="Watermark",
    text_color_hex="#808080", text_size_preset="M", watermark_image_file=None,
    image_scale_percent=15, position="BR", opacity=0.5
):
    base_img = None
    watermark_img_opened = None # Renamed to avoid confusion with file input
    watermark_resized = None
    text_layer = None
    final_image = None # The image object that gets saved at the end
    temp_rgb_image = None # For converting RGBA->RGB before JPEG save

    try:
        # --- Load Base Image ---
        base_image_file.seek(0)
        base_img = Image.open(base_image_file).convert("RGBA") # Always work in RGBA
        base_width, base_height = base_img.size
        original_format = base_img.format or 'PNG'
        print(f"[Watermark] Base image opened: {base_width}x{base_height}, Format: {original_format}")

        padding = int(min(base_width, base_height) * 0.02)

        # Start with the base image (as RGBA)
        img_to_process = base_img.copy() # Work on a copy

        # --- Prepare Watermark Element ---
        if watermark_type == 'text' and text_content:
            if not FONT_AVAILABLE: return None, None, "Server font error."
            print(f"[Watermark] Preparing Text: '{text_content}'")
            relative_size = TEXT_SIZE_PRESETS.get(text_size_preset, TEXT_SIZE_PRESETS['M'])
            font_size_px = max(10, int(base_height * relative_size))
            font = ImageFont.truetype(DEFAULT_FONT_PATH, font_size_px)
            rgba_color = hex_to_rgba(text_color_hex, opacity)
            print(f"  Text RGBA: {rgba_color}")

            # Create a transparent layer for the text
            text_layer = Image.new("RGBA", img_to_process.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(text_layer)

            # Get text dimensions
            try:
                 bbox = draw.textbbox((0, 0), text_content, font=font)
                 text_width = bbox[2] - bbox[0]; text_height = bbox[3] - bbox[1]
                 text_draw_x_offset = -bbox[0]; text_draw_y_offset = -bbox[1]
            except AttributeError: # Fallback
                text_width = len(text_content) * font_size_px * 0.6
                text_height = font_size_px
                text_draw_x_offset = 0; text_draw_y_offset = 0
            print(f"  Text Size: {text_width}x{text_height}")

            if position.upper() == "TILE":
                print("  Tiling text...")
                x_step = int(text_width + padding * 4); y_step = int(text_height + padding * 4)
                for y in range(0, base_height + y_step, y_step):
                     for x in range(0, base_width + x_step, x_step):
                         draw.text((x + text_draw_x_offset, y + text_draw_y_offset), text_content, font=font, fill=rgba_color)
            else:
                pos_x, pos_y = calculate_position(base_width, base_height, text_width, text_height, position.upper(), padding)
                print(f"  Position: {pos_x},{pos_y}")
                draw.text((pos_x + text_draw_x_offset, pos_y + text_draw_y_offset), text_content, font=font, fill=rgba_color)

            # Composite the text layer onto the base image copy
            img_to_process = Image.alpha_composite(img_to_process, text_layer)

        elif watermark_type == 'image' and watermark_image_file:
            print("[Watermark] Preparing Image Watermark...")
            watermark_image_file.seek(0)
            watermark_img_opened = Image.open(watermark_image_file).convert("RGBA")
            wm_width, wm_height = watermark_img_opened.size
            print(f"  Watermark Image: {wm_width}x{wm_height}")

            scale_factor = max(5, min(50, image_scale_percent)) / 100.0
            target_wm_width = int(base_width * scale_factor)
            wm_ratio = wm_height / wm_width if wm_width > 0 else 1
            target_wm_height = int(target_wm_width * wm_ratio)
            target_wm_width = max(1, target_wm_width); target_wm_height = max(1, target_wm_height)
            print(f"  Resizing watermark to: {target_wm_width}x{target_wm_height}")
            watermark_resized = watermark_img_opened.resize((target_wm_width, target_wm_height), Image.Resampling.LANCZOS)

            if opacity < 1.0:
                print(f"  Applying opacity: {opacity}")
                try:
                    alpha = watermark_resized.getchannel('A')
                    alpha = alpha.point(lambda p: int(p * opacity))
                    watermark_resized.putalpha(alpha)
                except (ValueError, IndexError): # Handle images without alpha gracefully
                    print("  Warning: Could not apply opacity (maybe no alpha channel).")

            # Paste watermark using its own alpha channel as the mask
            temp_layer = Image.new("RGBA", img_to_process.size, (255, 255, 255, 0))
            if position.upper() == "TILE":
                 print("  Tiling image watermark...")
                 x_step = target_wm_width + padding * 4
                 y_step = target_wm_height + padding * 4
                 for y in range(0, base_height + y_step, y_step):
                      for x in range(0, base_width + x_step, x_step):
                          try:
                              temp_layer.paste(watermark_resized, (x, y), watermark_resized)
                          except ValueError as e: # Pasting outside bounds sometimes errors
                               print(f"  Warning during tile paste: {e}")
                               continue
            else:
                pos_x, pos_y = calculate_position(base_width, base_height, target_wm_width, target_wm_height, position.upper(), padding)
                print(f"  Position: {pos_x},{pos_y}")
                try:
                    temp_layer.paste(watermark_resized, (pos_x, pos_y), watermark_resized)
                except ValueError as e:
                     print(f"  Warning during paste: {e}")


            # Composite the watermark layer onto the base image copy
            img_to_process = Image.alpha_composite(img_to_process, temp_layer)

        else:
             return None, None, "No valid watermark text or image provided/selected."

        # --- Save Final Image ---
        final_image = img_to_process # This is our processed RGBA image
        output_buffer = io.BytesIO()
        save_format = original_format.upper()
        save_kwargs = {}

        if save_format == 'JPG': save_format = 'JPEG' # Pillow uses JPEG

        if save_format == 'JPEG':
             print("[Watermark Save] Converting final RGBA to RGB for JPEG...")
             temp_rgb_image = Image.new("RGB", final_image.size, (255, 255, 255))
             try: temp_rgb_image.paste(final_image, mask=final_image.getchannel('A'))
             except ValueError: temp_rgb_image.paste(final_image) # Fallback
             save_kwargs = {'quality': 95, 'optimize': True}
             temp_rgb_image.save(output_buffer, format="JPEG", **save_kwargs)
             print("[Watermark Save] Saved as JPEG.")
        elif save_format == 'WEBP':
             save_kwargs = {'quality': 90}
             final_image.save(output_buffer, format="WEBP", **save_kwargs)
             print("[Watermark Save] Saved as WEBP.")
        else: # Assume PNG or other formats that support RGBA
             save_format = 'PNG' # Default to PNG if original format dubious
             save_kwargs = {'optimize': True}
             final_image.save(output_buffer, format=save_format, **save_kwargs)
             print(f"[Watermark Save] Saved as {save_format}.")


        base_name = os.path.splitext(base_image_file.name)[0]
        output_extension = save_format.lower()
        if output_extension == 'jpeg': output_extension = 'jpg'
        output_filename = f"{base_name}_watermarked.{output_extension}"

        output_buffer.seek(0)
        print(f"[Watermark Success] Output filename: {output_filename}")
        return output_buffer.getvalue(), output_filename, None

    except Exception as e:
        print(f"Error during watermarking process: {e}")
        import traceback
        traceback.print_exc()
        return None, None, f"An unexpected error occurred: {e}"
    finally:
        # --- Final Cleanup ---
        print("[Watermark Cleanup] Attempting final cleanup...")
        if base_img: 
            try: base_img.close(); print("  Closed base_img.") 
            except Exception: pass
        if watermark_img_opened: 
            try: watermark_img_opened.close(); print("  Closed watermark_img_opened.") 
            except Exception: pass
        if watermark_resized: 
            try: watermark_resized.close(); print("  Closed watermark_resized.") 
            except Exception: pass
        if text_layer: 
            try: text_layer.close(); print("  Closed text_layer.") 
            except Exception: pass
        if temp_rgb_image: 
            try: temp_rgb_image.close(); print("  Closed temp_rgb_image.") 
            except Exception: pass
        # Don't close final_image if it points to base_img or another already closed object
        # Closing img_to_process might be redundant if it's just base_img
        # This cleanup logic is complex because of the potential object reassignments
        # Python's garbage collector should handle most of it if references are cleared.
        # For safety, we closed intermediate objects like watermark_resized and temp_rgb_image inline.
        print("[Watermark Cleanup] Finished cleanup attempt.")