# utility_tools/barcode_generator_logic.py
import io
import os
import barcode # Main library
# Removed: from barcode.writer import ImageWriter, SVGWriter # Not needed this way

# Keep SIZE_PRESETS and SUPPORTED_BARCODES as before
SIZE_PRESETS = { "S": {"module_width": 0.25, "module_height": 8.0, "font_size": 8, "text_distance": 3.0, "quiet_zone": 3.0}, "M": {"module_width": 0.33, "module_height": 12.0, "font_size": 10, "text_distance": 4.0, "quiet_zone": 5.0}, "L": {"module_width": 0.4, "module_height": 15.0, "font_size": 12, "text_distance": 5.0, "quiet_zone": 6.5}, }
DEFAULT_SIZE_PRESET = SIZE_PRESETS['M']
SUPPORTED_BARCODES = { "Code128": "code128", "Code39": "code39", "EAN-13": "ean13", "UPC-A": "upca" }
ERROR_CORRECTION_MAP = {} # Keep initialization

def generate_barcode(data, barcode_type_name='Code128', output_format='PNG',
                     include_text=True, size_preset='M'):
    """
    Generates a barcode image from text data.
    """
    if not data:
        return None, None, "Input data cannot be empty."

    barcode_class_name = SUPPORTED_BARCODES.get(barcode_type_name)
    if not barcode_class_name:
        return None, None, f"Unsupported barcode type: {barcode_type_name}"

    try:
        # Import necessary parts (can stay inside or move outside if preferred now)
        import qrcode # Although not used here, maybe keep if other funcs use it
        from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H # Actually not used here
        ERROR_CORRECTION_MAP.update({ "L": ERROR_CORRECT_L, "M": ERROR_CORRECT_M, "Q": ERROR_CORRECT_Q, "H": ERROR_CORRECT_H }) # Not used for barcode

        BarcodeClass = barcode.get_barcode_class(barcode_class_name)
        print(f"[Barcode Gen] Using class: {BarcodeClass}")

        # Handle Code39 checksum logic (same as before)
        add_checksum_code39 = True
        if barcode_class_name == 'code39' and add_checksum_code39:
            valid_chars = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%")
            if not set(data).issubset(valid_chars):
                 print("[Barcode Gen] Invalid chars for Code39 with checksum. Disabling checksum.")
                 add_checksum_code39 = False

        # Instantiate barcode object
        if barcode_class_name == 'code39':
            barcode_obj = BarcodeClass(data, add_checksum=add_checksum_code39)
        else:
            barcode_obj = BarcodeClass(data)

        # Get size options
        size_options = SIZE_PRESETS.get(size_preset, DEFAULT_SIZE_PRESET)

        # Prepare writer options dictionary
        writer_options = {
            "module_width": size_options["module_width"],
            "module_height": size_options["module_height"],
            "font_size": size_options["font_size"],
            "text_distance": size_options["text_distance"],
            "quiet_zone": size_options["quiet_zone"],
            "write_text": include_text,
            # Specify format for PNG writer if needed (often inferred)
            # "format": "PNG" # Only needed if default isn't PNG for ImageWriter
        }
        # SVG writer options are slightly different if needed later (e.g., xml_declaration)

        output_buffer = io.BytesIO()
        # Determine output filename extension
        file_ext = 'svg' if output_format.upper() == 'SVG' else 'png'
        output_filename = f"{barcode_class_name}_{size_preset}.{file_ext}"

        print(f"[Barcode Gen] Generating {barcode_type_name} for '{data}'. Format: {output_format}, Options: {writer_options}")

        # --- FIX: Pass options directly, don't pass 'writer=' ---
        # The library selects the writer based on filename extension or format option
        # If saving to buffer, we need to tell it the format. Add 'format' to writer_options.
        if output_format.upper() == 'SVG':
             writer_options['format'] = 'SVG'
             # writer_options['xml_declaration'] = False # Example SVG option
        else: # PNG
             writer_options['format'] = 'PNG'

        barcode_obj.write(output_buffer, options=writer_options)
        # --- END FIX ---

        output_buffer.seek(0)
        print(f"[Barcode Gen] Saved as {output_format}.")
        return output_buffer.getvalue(), output_filename, None # Success

    # --- Keep Exception Handling as before ---
    except barcode.errors.IllegalCharacterError as e:
        print(f"[Barcode Gen] Illegal Character Error: {e}")
        return None, None, f"Invalid character in data for {barcode_type_name}: {e}"
    except barcode.errors.NumberOfDigitsError as e:
         print(f"[Barcode Gen] Incorrect Number of Digits: {e}")
         return None, None, f"Incorrect number of digits for {barcode_type_name}: {e}"
    except Exception as e:
        print(f"Error during Barcode generation process: {e}")
        import traceback
        traceback.print_exc()
        if isinstance(e, ImportError):
             return None, None, "Server error: Required barcode library is missing or has issues."
        return None, None, f"An unexpected error occurred: {e}"