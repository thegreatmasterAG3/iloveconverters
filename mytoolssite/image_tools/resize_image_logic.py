# image_tools/resize_image_logic.py
import io
import os
from PIL import Image

DEFAULT_RESAMPLE_FILTER = Image.Resampling.LANCZOS

def resize_image(
    image_file,
    resize_mode='pixels',
    target_width=None,
    target_height=None,
    percentage=100,
    maintain_aspect_ratio=True,
    output_format='JPEG',
    jpeg_quality=90,
):
    if not image_file:
        return None, None

    img_original = None
    img_resized = None
    img_final = None # This will hold the image we actually save

    try:
        image_file.seek(0)
        img_original = Image.open(image_file)
        original_width, original_height = img_original.size
        original_format = img_original.format.upper() if img_original.format else 'PNG'
        print(f"[Resize Start] Original: {original_width}x{original_height}, Format: {original_format}, Mode: {img_original.mode}")

        # --- Determine target dimensions ---
        new_width = original_width
        new_height = original_height
        # ... (pixel/percentage/aspect ratio calculation logic identical to previous versions) ...
        if resize_mode == 'pixels':
            if target_width is None and target_height is None: raise ValueError("Width or Height required.")
            w = target_width if target_width is not None else original_width
            h = target_height if target_height is not None else original_height
            if maintain_aspect_ratio:
                 if target_width is not None and target_height is None:
                    ratio = original_height / original_width; new_width = w; new_height = int(round(new_width * ratio))
                 elif target_height is not None and target_width is None:
                    ratio = original_width / original_height; new_height = h; new_width = int(round(new_height * ratio))
                 elif target_width is not None and target_height is not None:
                     original_ratio = original_width / original_height; target_ratio = w / h
                     if original_ratio > target_ratio: new_width = w; new_height = int(round(new_width / original_ratio))
                     else: new_height = h; new_width = int(round(new_height * original_ratio))
            else: new_width = w; new_height = h
        elif resize_mode == 'percentage':
             if percentage is None or not (0 < percentage): raise ValueError("Invalid percentage.")
             scale = percentage / 100.0; new_width = int(round(original_width * scale)); new_height = int(round(original_height * scale))

        new_width = max(1, new_width)
        new_height = max(1, new_height)
        print(f"[Resize Calc] New Dims: {new_width}x{new_height}")


        # --- Perform resizing (only if dimensions changed) ---
        if new_width == original_width and new_height == original_height:
            print("[Resize Skip] Dimensions unchanged.")
            img_resized = img_original # Use original if no resize needed
        else:
            print("[Resize Execute] Resizing image...")
            img_resized = img_original.resize((new_width, new_height), resample=DEFAULT_RESAMPLE_FILTER)
            print(f"[Resize Result] Resized image mode: {img_resized.mode}")


        # --- Determine final output format ---
        final_format = output_format.upper()
        if final_format == 'ORIGINAL': final_format = original_format
        if final_format == 'JPG': final_format = 'JPEG'


        # --- Handle Color Mode / Transparency based on FINAL format ---
        img_final = img_resized

        if final_format == 'JPEG':
            if img_resized.mode == 'RGBA' or 'A' in img_resized.getbands():
                print("[Resize Convert] Converting RGBA/Alpha to RGB for JPEG...")
                background = Image.new('RGB', img_resized.size, (255, 255, 255))
                try: background.paste(img_resized, mask=img_resized.getchannel('A'))
                except ValueError: background.paste(img_resized, (0,0), img_resized)
                img_final = background
            elif img_resized.mode != 'RGB':
                print(f"[Resize Convert] Converting {img_resized.mode} to RGB for JPEG...")
                img_final = img_resized.convert('RGB')


        # --- Prepare for saving ---
        output_buffer = io.BytesIO()
        save_kwargs = {}
        if final_format == 'JPEG':
            save_kwargs['quality'] = jpeg_quality
            save_kwargs['optimize'] = True
        elif final_format == 'PNG':
            save_kwargs['optimize'] = True
        elif final_format == 'WEBP':
            save_kwargs['quality'] = jpeg_quality


        print(f"[Resize Save] Saving final image ({img_final.mode}) as {final_format} with options: {save_kwargs}")
        img_final.save(output_buffer, format=final_format, **save_kwargs)


        # --- Construct output filename ---
        base_name = os.path.splitext(image_file.name)[0]
        output_extension = final_format.lower()
        if output_extension == 'jpeg': output_extension = 'jpg'
        output_filename = f"{base_name}_resized.{output_extension}"

        output_buffer.seek(0)
        print(f"[Resize Success] Output filename: {output_filename}")
        return output_buffer.getvalue(), output_filename

    except Exception as e:
        print(f"[Resize Error] Error during image resizing: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    finally:
        # --- Simpler Cleanup ---
        print("[Resize Cleanup] Attempting final cleanup...")
        if img_original:
            try:
                img_original.close()
                print("  Closed img_original.")
            except Exception as e:
                print(f"  Error closing img_original (ignoring): {e}")
        if img_resized:
             try:
                 if img_resized is not img_original: # Check identity
                     img_resized.close()
                     print("  Closed img_resized.")
                 else:
                      print("  img_resized is same as img_original (already closed or handled).")
             except Exception as e:
                 print(f"  Error closing img_resized (ignoring): {e}")
        if img_final:
             try:
                 if img_final is not img_original and img_final is not img_resized: # Check identity
                     img_final.close()
                     print("  Closed img_final.")
                 else:
                      print("  img_final is same as previous (already closed or handled).")
             except Exception as e:
                 print(f"  Error closing img_final (ignoring): {e}")