# image_tools/rotate_flip_image_logic.py
import io
import os
from PIL import Image, ImageOps # Import ImageOps for flipping

DEFAULT_RESAMPLE_FILTER = Image.Resampling.BICUBIC # Good quality for rotation

def parse_hex_color(hex_str, default=(255, 255, 255)):
    """ Parses #RRGGBB string to RGB tuple """
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 6:
        try:
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            return default
    return default # Return default if format is wrong

def rotate_flip_image(
    image_file,
    rotation_angle=0, # Can be 90, 180, 270 or custom float
    flip_horizontal=False,
    flip_vertical=False,
    background_color_hex="#ffffff",
    output_format='ORIGINAL',
    jpeg_quality=90
):
    """
    Rotates and/or flips an image with specified options.

    Args:
        image_file: Django UploadedFile object.
        rotation_angle (float): Angle in degrees (90, 180, 270 preferred for no expansion).
        flip_horizontal (bool): Apply horizontal flip.
        flip_vertical (bool): Apply vertical flip.
        background_color_hex (str): Hex color for background if rotation expands canvas.
        output_format (str): 'ORIGINAL', 'JPEG', 'PNG', 'WEBP'.
        jpeg_quality (int): Quality for JPEG/WEBP output.

    Returns:
        tuple: (bytes: Result image content or None, str: output filename or None, str: error message or None)
    """
    if not image_file:
        return None, None, "No image file provided."

    img = None
    img_processed = None
    try:
        image_file.seek(0)
        img = Image.open(image_file)
        original_format = img.format.upper() if img.format else 'PNG'
        original_mode = img.mode
        print(f"[Rotate/Flip Start] Original: {image_file.name}, Format: {original_format}, Mode: {original_mode}")

        # --- Apply Flips First (using ImageOps) ---
        img_processed = img # Start with original
        if flip_horizontal:
            print("[Rotate/Flip] Applying horizontal flip.")
            img_processed = ImageOps.mirror(img_processed)
        if flip_vertical:
            print("[Rotate/Flip] Applying vertical flip.")
            img_processed = ImageOps.flip(img_processed)

        # --- Apply Rotation ---
        if rotation_angle != 0:
            # Pillow rotates counter-clockwise
            angle_to_rotate = float(rotation_angle) * -1 # Convert to float and negate for Pillow
            print(f"[Rotate/Flip] Applying rotation: {angle_to_rotate} degrees CCW (User requested {rotation_angle})")

            # Check if expansion is needed (non-90 degree increments)
            expand = True # Default to expanding for arbitrary angles
            resample_filter = DEFAULT_RESAMPLE_FILTER
            fillcolor = None

            # Optimize for 90/180/270 degree rotations (lossless if possible)
            if angle_to_rotate % 90 == 0:
                expand = False # No expansion needed
                resample_filter = Image.Resampling.NEAREST # Use NEAREST for lossless 90-degree turns

            # For arbitrary angles, set background color
            if expand:
                fillcolor = parse_hex_color(background_color_hex)
                print(f"[Rotate/Flip] Using expand=True, fillcolor={fillcolor}")


            # Perform rotation. Need to ensure the image object is kept open.
            # If flips happened, img_processed is the flipped one. Otherwise it's the original.
            rotated_temp = img_processed.rotate(
                angle_to_rotate,
                resample=resample_filter,
                expand=expand,
                fillcolor=fillcolor
            )
            # If we created a new object (due to flips or expand), close the previous one
            if img_processed is not img and img_processed is not rotated_temp:
                img_processed.close()
            img_processed = rotated_temp # Update reference

        print(f"[Rotate/Flip] Processed image mode: {img_processed.mode}")

        # --- Determine final output format ---
        final_format = output_format.upper()
        if final_format == 'ORIGINAL': final_format = original_format
        if final_format == 'JPG': final_format = 'JPEG'

        # --- Handle Color Mode / Transparency for Output ---
        final_image_to_save = img_processed
        needs_rgb_conversion = False
        if final_format == 'JPEG':
            # Check the *processed* image's mode
            if img_processed.mode == 'RGBA' or 'A' in img_processed.getbands():
                 needs_rgb_conversion = True
            elif img_processed.mode == 'P': # Palette mode might have transparency
                try:
                    if 'transparency' in img_processed.info:
                        needs_rgb_conversion = True
                except Exception: pass # Ignore if info doesn't exist
            elif img_processed.mode != 'RGB': # Convert L etc.
                 needs_rgb_conversion = True

        if needs_rgb_conversion:
            print(f"[Rotate/Flip Convert] Converting final image mode ({img_processed.mode}) to RGB for {final_format} output.")
            background = Image.new('RGB', img_processed.size, parse_hex_color(background_color_hex)) # Use selected bg color
            try: background.paste(img_processed, mask=img_processed.getchannel('A'))
            except ValueError: background.paste(img_processed, (0,0), img_processed)
            final_image_to_save = background
            # Close the intermediate processed image if it's different
            if img_processed is not img and img_processed is not final_image_to_save:
                 img_processed.close()


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

        print(f"[Rotate/Flip Save] Saving final image ({final_image_to_save.mode}) as {final_format} with options: {save_kwargs}")
        final_image_to_save.save(output_buffer, format=final_format, **save_kwargs)

        # --- Construct output filename ---
        base_name = os.path.splitext(image_file.name)[0]
        output_extension = final_format.lower()
        if output_extension == 'jpeg': output_extension = 'jpg'
        output_filename = f"{base_name}_rotated.{output_extension}"

        output_buffer.seek(0)
        print(f"[Rotate/Flip Success] Output filename: {output_filename}")
        return output_buffer.getvalue(), output_filename, None

    except Exception as e:
        print(f"Error during image rotation/flip: {e}")
        import traceback
        traceback.print_exc()
        return None, None, f"An unexpected error occurred: {e}"
    finally:
        # Final cleanup
        print("[Rotate/Flip Cleanup] Attempting final cleanup...")
        if img:
            try: img.close(); print("  Closed img.")
            except Exception: pass
        if img_processed and img_processed is not img:
             try: img_processed.close(); print("  Closed img_processed.")
             except Exception: pass
        if final_image_to_save and final_image_to_save is not img_processed and final_image_to_save is not img:
             try: final_image_to_save.close(); print("  Closed final_image_to_save.")
             except Exception: pass