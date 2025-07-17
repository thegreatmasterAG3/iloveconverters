# image_tools/favicon_generator_logic.py
import io
import os
import zipfile
import json
from PIL import Image
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent # For browserconfig.xml

# Standard favicon sizes
ICO_SIZES = [(16, 16), (32, 32), (48, 48)]
PNG_SIZES = [(16, 16), (32, 32)]
APPLE_TOUCH_SIZE = (180, 180)
ANDROID_SIZES = [(192, 192), (512, 512)]

DEFAULT_BG_COLOR = (255, 255, 255, 0) # Default: Transparent RGBA
DEFAULT_BG_COLOR_OPAQUE = (255, 255, 255) # Default: White RGB

# Helper to handle transparency and resize
def prepare_image(img_original, target_size, bg_color_tuple_rgba):
    """Resizes and handles transparency for different formats."""
    img_copy = img_original.copy()

    # --- Handle RGBA Conversion and Background ---
    # If it doesn't have alpha but we need one (e.g. for PNG output preserve transparency)
    if 'A' not in img_copy.getbands() and bg_color_tuple_rgba[3] == 0:
         img_copy = img_copy.convert("RGBA") # Add alpha channel
    # If it has alpha but background isn't transparent (for ICO/JPG bg)
    elif 'A' in img_copy.getbands() and bg_color_tuple_rgba[3] != 0:
        background = Image.new('RGBA', img_copy.size, bg_color_tuple_rgba)
        # Paste using alpha mask
        try: background.paste(img_copy, mask=img_copy.getchannel('A'))
        except ValueError: background.paste(img_copy, (0,0), img_copy) # Fallback paste
        img_copy = background.convert('RGB') # Convert to RGB after applying background
    # If no alpha and solid background needed
    elif 'A' not in img_copy.getbands() and bg_color_tuple_rgba[3] != 0:
         if img_copy.mode != 'RGB': img_copy = img_copy.convert('RGB')
         # If already RGB, background isn't needed unless resizing creates borders
    # If has alpha and transparent background needed (for PNGs)
    elif 'A' in img_copy.getbands() and bg_color_tuple_rgba[3] == 0:
         if img_copy.mode != 'RGBA': img_copy = img_copy.convert("RGBA") # Ensure RGBA

    # Ensure it's not palette mode for resizing quality
    if img_copy.mode == 'P':
        img_copy = img_copy.convert("RGBA" if 'A' in img_copy.getbands() else "RGB")

    # --- Resizing ---
    # Use LANCZOS for high quality downsampling
    # Use BICUBIC or BILINEAR if LANCZOS errors on specific modes/images
    img_copy.thumbnail(target_size, Image.Resampling.LANCZOS)

    # --- Centering / Padding (Optional - adds complexity) ---
    # If you want to ensure the output is exactly target_size, even if aspect ratio
    # was maintained by thumbnail, you could paste it onto a transparent/colored canvas:
    # final_canvas = Image.new('RGBA', target_size, (0,0,0,0)) # Transparent canvas
    # paste_x = (target_size[0] - img_copy.width) // 2
    # paste_y = (target_size[1] - img_copy.height) // 2
    # final_canvas.paste(img_copy, (paste_x, paste_y))
    # return final_canvas

    return img_copy


def generate_favicon_assets(image_file, background_color_hex="#ffffff"):
    """
    Generates a set of favicon files (ICO, PNGs, manifest, etc.) from an input image.

    Args:
        image_file: Django UploadedFile object.
        background_color_hex (str): Hex color code (e.g., '#ffffff') for transparency background.

    Returns:
        tuple: (bytes: ZIP file content or None, str: error message or None)
    """
    if not image_file:
        return None, "No image file provided."

    img_original = None
    zip_buffer = io.BytesIO()

    try:
        image_file.seek(0)
        img_original = Image.open(image_file)
        print(f"[Favicon Gen] Opened '{image_file.name}', Mode: {img_original.mode}, Size: {img_original.size}")

        # --- Parse Background Color ---
        bg_color_hex = background_color_hex.lstrip('#')
        try:
            if len(bg_color_hex) == 6:
                 bg_color_rgb = tuple(int(bg_color_hex[i:i+2], 16) for i in (0, 2, 4))
                 bg_color_rgba = bg_color_rgb + (255,) # Opaque for background fill
            else: # Assume transparent if not 6 hex chars
                 bg_color_rgba = DEFAULT_BG_COLOR # Transparent
                 bg_color_rgb = DEFAULT_BG_COLOR_OPAQUE # White for non-alpha formats
        except ValueError:
             print("[Favicon Gen] Warning: Invalid hex color, using defaults.")
             bg_color_rgba = DEFAULT_BG_COLOR
             bg_color_rgb = DEFAULT_BG_COLOR_OPAQUE

        # --- Create ZIP file ---
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:

            # --- Generate favicon.ico ---
            print("[Favicon Gen] Generating favicon.ico...")
            ico_buffer = io.BytesIO()
            try:
                # Prepare images with solid background if needed for ICO
                ico_imgs = [prepare_image(img_original, size, bg_color_rgba if size[0] <= 32 else bg_color_rgb + (255,) ) for size in ICO_SIZES] # Smaller ICOs can retain transparency
                # Save ICO file with multiple sizes
                ico_imgs[0].save(ico_buffer, format='ICO', sizes=ICO_SIZES)
                ico_buffer.seek(0)
                zipf.writestr("favicon.ico", ico_buffer.read())
                print("[Favicon Gen] favicon.ico added.")
            except Exception as ico_err:
                 print(f"[Favicon Gen] Error generating ICO: {ico_err}") # Log error but continue
                 # Optionally add a message to the user later
            finally:
                 ico_buffer.close()
                 for img in ico_imgs: img.close() # Close temp images

            # --- Generate PNG favicons ---
            for size in PNG_SIZES:
                filename = f"favicon-{size[0]}x{size[1]}.png"
                print(f"[Favicon Gen] Generating {filename}...")
                png_buffer = io.BytesIO()
                img_resized = None
                try:
                    # Prepare with transparent background
                    img_resized = prepare_image(img_original, size, DEFAULT_BG_COLOR)
                    img_resized.save(png_buffer, format='PNG')
                    png_buffer.seek(0)
                    zipf.writestr(filename, png_buffer.read())
                    print(f"[Favicon Gen] {filename} added.")
                except Exception as png_err:
                    print(f"[Favicon Gen] Error generating {filename}: {png_err}")
                finally:
                     png_buffer.close()
                     if img_resized: img_resized.close()

            # --- Generate apple-touch-icon.png ---
            filename_apple = "apple-touch-icon.png"
            print(f"[Favicon Gen] Generating {filename_apple}...")
            apple_buffer = io.BytesIO()
            img_apple = None
            try:
                # Needs opaque background (use selected or default white)
                img_apple = prepare_image(img_original, APPLE_TOUCH_SIZE, bg_color_rgb + (255,))
                # Apple icons should typically be RGB, remove alpha if present
                if img_apple.mode == 'RGBA': img_apple = img_apple.convert('RGB')
                img_apple.save(apple_buffer, format='PNG')
                apple_buffer.seek(0)
                zipf.writestr(filename_apple, apple_buffer.read())
                print(f"[Favicon Gen] {filename_apple} added.")
            except Exception as apple_err:
                 print(f"[Favicon Gen] Error generating {filename_apple}: {apple_err}")
            finally:
                 apple_buffer.close()
                 if img_apple: img_apple.close()

            # --- Generate android-chrome PNGs ---
            for size in ANDROID_SIZES:
                filename = f"android-chrome-{size[0]}x{size[1]}.png"
                print(f"[Favicon Gen] Generating {filename}...")
                android_buffer = io.BytesIO()
                img_android = None
                try:
                    # Prepare with transparent background
                    img_android = prepare_image(img_original, size, DEFAULT_BG_COLOR)
                    img_android.save(android_buffer, format='PNG')
                    android_buffer.seek(0)
                    zipf.writestr(filename, android_buffer.read())
                    print(f"[Favicon Gen] {filename} added.")
                except Exception as android_err:
                    print(f"[Favicon Gen] Error generating {filename}: {android_err}")
                finally:
                     android_buffer.close()
                     if img_android: img_android.close()

            # --- Generate site.webmanifest ---
            print("[Favicon Gen] Generating site.webmanifest...")
            manifest = {
                "name": "Your App Name", # Replace with site name later
                "short_name": "App",    # Replace with short site name
                "icons": [
                    {
                        "src": f"/android-chrome-{ANDROID_SIZES[0][0]}x{ANDROID_SIZES[0][1]}.png", # Relative path
                        "sizes": f"{ANDROID_SIZES[0][0]}x{ANDROID_SIZES[0][1]}",
                        "type": "image/png"
                    },
                    {
                        "src": f"/android-chrome-{ANDROID_SIZES[1][0]}x{ANDROID_SIZES[1][1]}.png", # Relative path
                        "sizes": f"{ANDROID_SIZES[1][0]}x{ANDROID_SIZES[1][1]}",
                        "type": "image/png"
                    }
                ],
                "theme_color": "#ffffff", # Replace later
                "background_color": "#ffffff", # Replace later
                "display": "standalone"
            }
            zipf.writestr("site.webmanifest", json.dumps(manifest, indent=4))
            print("[Favicon Gen] site.webmanifest added.")


            # --- Generate browserconfig.xml ---
            print("[Favicon Gen] Generating browserconfig.xml...")
            try:
                root = Element('browserconfig')
                msapplication = SubElement(root, 'msapplication')
                tile = SubElement(msapplication, 'tile')
                square150 = SubElement(tile, 'square150x150logo', src=f'/android-chrome-{ANDROID_SIZES[0][0]}x{ANDROID_SIZES[0][1]}.png') # Use 192 as base
                tilecolor = SubElement(tile, 'TileColor')
                tilecolor.text = '#ffffff' # Replace later

                xml_buffer = io.BytesIO()
                tree = ElementTree(root)
                indent(tree) # Pretty print
                tree.write(xml_buffer, encoding='utf-8', xml_declaration=True)
                xml_buffer.seek(0)
                zipf.writestr("browserconfig.xml", xml_buffer.read())
                print("[Favicon Gen] browserconfig.xml added.")
            except Exception as xml_err:
                 print(f"[Favicon Gen] Error generating browserconfig.xml: {xml_err}")

        # --- End Zip File ---
        print("[Favicon Gen] ZIP file created successfully.")
        zip_buffer.seek(0)
        return zip_buffer.getvalue(), None # Return ZIP bytes, no error message

    except Exception as e:
        print(f"Error during Favicon generation process: {e}")
        import traceback
        traceback.print_exc()
        return None, f"An unexpected error occurred: {e}"
    finally:
        if img_original:
            try: img_original.close()
            except Exception: pass
        print("[Favicon Gen] Cleanup complete.")

# Helper function for HTML snippets
def get_favicon_html_snippets():
    html = f"""<!-- Standard Favicons -->
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">

<!-- Apple Touch Icon -->
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">

<!-- Web App Manifest -->
<link rel="manifest" href="/site.webmanifest">

<!-- Theme Color (Optional) -->
<!-- <meta name="theme-color" content="#ffffff"> -->

<!-- Microsoft Tiles (Optional) -->
<!-- <meta name="msapplication-TileColor" content="#ffffff"> -->
<!-- <meta name="msapplication-config" content="/browserconfig.xml"> -->"""
    return html