# utility_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .qr_code_logic import generate_qr_code
import base64

def qr_code_view(request):
    # Clear previous QR data from session
    # Use different session keys to avoid clashes
    if request.method == 'GET' or 'qr_data' in request.POST: # Clear if new data submitted
        if 'qr_image_b64' in request.session: del request.session['qr_image_b64']
        if 'qr_filename' in request.session: del request.session['qr_filename']
        if 'qr_format' in request.session: del request.session['qr_format']

    context = {
        'page_title': 'QR Code Generator',
        'data_input': request.POST.get('qr_data', '') if request.method == 'POST' else '', # Repopulate on error
        'prev_options': request.POST if request.method == 'POST' else {}, # Repopulate options
    }

    if request.method == 'POST':
        # Handle Download Request
        if 'download_qr' in request.POST:
            qr_image_b64 = request.session.get('qr_image_b64')
            qr_filename = request.session.get('qr_filename', 'qrcode.png')
            qr_format = request.session.get('qr_format', 'PNG') # Get format for content type

            if qr_image_b64:
                try:
                    qr_data = base64.b64decode(qr_image_b64.encode('ascii'))
                    # Determine content type based on stored format
                    content_type = 'image/png' # Default
                    if qr_format.upper() == 'SVG':
                        content_type = 'image/svg+xml'

                    response = HttpResponse(qr_data, content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="{qr_filename}"'
                    # Clean up session
                    if 'qr_image_b64' in request.session: del request.session['qr_image_b64']
                    if 'qr_filename' in request.session: del request.session['qr_filename']
                    if 'qr_format' in request.session: del request.session['qr_format']
                    return response
                except Exception as e:
                    messages.error(request, "Could not retrieve generated QR Code.")
            else:
                messages.error(request, "No generated QR Code found to download.")
            # Redirect if download fails or no data found
            return redirect('utility_tools:qr_code_generator')

        # --- Handle QR Code Generation ---
        else:
            data_input = request.POST.get('qr_data', '').strip()
            error_correction = request.POST.get('error_correction', 'M')
            size_preset = request.POST.get('size_preset', 'M')
            output_format = request.POST.get('output_format', 'PNG')

            if not data_input:
                messages.error(request, "Please enter text or data to encode.")
                # Re-render form with previous input
                context['prev_options'] = request.POST # Keep options
                return render(request, 'utility_tools/tool_qr_code_generator.html', context)

            # --- Generation ---
            print(f"Generating QR Code. EC: {error_correction}, Size: {size_preset}, Format: {output_format}")
            qr_data, output_filename, error_message = generate_qr_code(
                data=data_input,
                error_correction=error_correction,
                size_preset=size_preset,
                output_format=output_format
            )
            # --- End Generation ---

            if qr_data and output_filename:
                print("QR Code generation successful.")
                qr_image_b64 = base64.b64encode(qr_data).decode('ascii')
                request.session['qr_image_b64'] = qr_image_b64
                request.session['qr_filename'] = output_filename
                request.session['qr_format'] = output_format # Store format for download

                context['generation_success'] = True
                context['download_filename'] = output_filename
                context['qr_image_b64'] = qr_image_b64 # Pass for direct display
                context['qr_format'] = output_format # Pass format for display logic
                messages.success(request, "QR Code generated successfully!")
            else:
                print(f"QR Code generation failed: {error_message}")
                context['generation_success'] = False
                messages.error(request, error_message or "Failed to generate QR Code.")

            # Re-render same page with results/errors
            return render(request, 'utility_tools/tool_qr_code_generator.html', context)

    # --- GET Request Handling ---
    else:
        # Display the form, check if results are in session from previous attempt
        context['generation_success'] = request.session.get('qr_image_b64') is not None
        if context['generation_success']:
            context['download_filename'] = request.session.get('qr_filename')
            context['qr_image_b64'] = request.session.get('qr_image_b64')
            context['qr_format'] = request.session.get('qr_format')

        return render(request, 'utility_tools/tool_qr_code_generator.html', context)
    





# utility_tools/views.py
from django.shortcuts import render
from .qr_code_logic import generate_qr_code
# --- NEW IMPORT ---
from .uuid_generator_logic import generate_uuids
# --- END NEW IMPORT ---
from django.contrib import messages # If using messages



# --- NEW VIEW for UUID Generator ---
def uuid_generator_view(request):
    context = {
        'page_title': 'UUID Generator',
        'generated_uuids': None,
        # Default options for GET request
        'prev_version': 4,
        'prev_quantity': 1,
        'prev_uppercase': False,
        'prev_remove_hyphens': False,
    }

    if request.method == 'POST':
        try:
            version = int(request.POST.get('version', 4))
            quantity = int(request.POST.get('quantity', 1))
            uppercase = request.POST.get('uppercase', 'off') == 'on'
            remove_hyphens = request.POST.get('remove_hyphens', 'off') == 'on'

            # Basic validation in view as well
            if version not in [1, 4]: version = 4
            if quantity < 1: quantity = 1
            if quantity > 1000: # Limit quantity
                quantity = 1000
                messages.warning(request, "Maximum quantity limited to 1000.")

            print(f"Requesting UUIDs: V={version}, Qty={quantity}, Upper={uppercase}, NoHyphens={remove_hyphens}")

            generated_uuids = generate_uuids(
                version=version,
                quantity=quantity,
                uppercase=uppercase,
                remove_hyphens=remove_hyphens
            )

            if generated_uuids is not None:
                context['generated_uuids'] = generated_uuids
                print(f"Generated {len(generated_uuids)} UUIDs successfully.")
            else:
                messages.error(request, "Failed to generate UUIDs. Please check options or try again.")

            # Store submitted options for form repopulation
            context['prev_version'] = version
            context['prev_quantity'] = quantity
            context['prev_uppercase'] = uppercase
            context['prev_remove_hyphens'] = remove_hyphens

        except ValueError:
            messages.error(request, "Invalid quantity entered. Please enter a number.")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")


    # Render for GET or POST
    return render(request, 'utility_tools/tool_uuid_generator.html', context)






# utility_tools/views.py
from django.shortcuts import render
# ... other imports ...
# --- NEW IMPORT ---
from .hash_generator_logic import generate_hash, SUPPORTED_HASH_ALGORITHMS
# --- END NEW IMPORT ---


# ...

# --- NEW VIEW for Hash Generator ---
def hash_generator_view(request):
    context = {
        'page_title': 'Hash Generator (MD5, SHA-1, SHA-256, SHA-512)',
        'text_input': '',
        'selected_algorithm': 'sha256', # Default
        'generated_hash': None,
        'supported_algorithms': SUPPORTED_HASH_ALGORITHMS, # Pass list to template
    }

    if request.method == 'POST':
        text_input = request.POST.get('text_input', '') # Don't strip whitespace here
        selected_algorithm = request.POST.get('hash_algorithm', 'sha256')

        context['text_input'] = text_input
        context['selected_algorithm'] = selected_algorithm

        if selected_algorithm not in SUPPORTED_HASH_ALGORITHMS:
             messages.error(request, "Invalid hash algorithm selected.")
             # Still render the form, but without generating
        elif text_input is not None: # Check if present, even if empty string
            print(f"Generating hash for input with algorithm: {selected_algorithm}")
            generated_hash = generate_hash(text_input, selected_algorithm)
            context['generated_hash'] = generated_hash
            if generated_hash is None and selected_algorithm in SUPPORTED_HASH_ALGORITHMS:
                 # Distinguish between bad algorithm and other errors
                 messages.error(request, "An error occurred during hash generation.")
            elif generated_hash is not None:
                 messages.success(request, f"{selected_algorithm.upper()} hash generated successfully!")

        else:
            # Should not happen if textarea is required, but handle defensively
            messages.info(request, "Please enter some text to hash.")


    # Render for GET or POST
    return render(request, 'utility_tools/tool_hash_generator.html', context)






# utility_tools/views.py
from django.shortcuts import render
from django.contrib import messages
# ... other imports ...
# --- NEW IMPORT ---
from .url_encode_decode_logic import url_process_text
# --- END NEW IMPORT ---


# ...

# --- NEW VIEW for URL Encoder/Decoder ---
def url_encode_decode_view(request):
    context = {
        'page_title': 'URL Encoder / Decoder',
        'text_input': '',
        'processed_text': None, # Result goes here
        'mode_used': None, # Keep track of whether encode or decode was last used
    }

    if request.method == 'POST':
        text_input = request.POST.get('text_input', '') # Don't strip
        # Determine mode from the button clicked (we'll give buttons specific names)
        mode = 'encode' # Default
        if 'decode_submit' in request.POST:
            mode = 'decode'
        elif 'encode_submit' in request.POST:
            mode = 'encode'
        # else: # If neither button name is present (e.g., JS submission), might need hidden input

        context['text_input'] = text_input
        context['mode_used'] = mode

        if text_input is not None: # Check if key exists, even if empty string
            print(f"Processing URL text with mode: {mode}")
            processed_text, error_message = url_process_text(text_input, mode)

            if error_message:
                messages.error(request, error_message)
                context['processed_text'] = None # Clear result on error
            else:
                context['processed_text'] = processed_text
                # Optional success message, might be obvious
                # messages.success(request, f"Text successfully {mode}d!")
        else:
             messages.info(request, "Please enter some text to process.")

    # Render for GET or POST
    return render(request, 'utility_tools/tool_url_encoder_decoder.html', context)






# utility_tools/views.py
from django.shortcuts import render
from django.contrib import messages
# ... other imports ...
# --- NEW IMPORT ---
from .base64_logic import process_base64
# --- END NEW IMPORT ---


# --- NEW VIEW for Base64 ---
def base64_view(request):
    context = {
        'page_title': 'Base64 Encoder / Decoder',
        'text_input': '',
        'processed_text': None,
        'mode_used': None,
    }

    if request.method == 'POST':
        text_input = request.POST.get('text_input', '') # No strip
        # Determine mode from button clicked
        mode = 'encode' # Default
        if 'decode_submit' in request.POST: mode = 'decode'
        elif 'encode_submit' in request.POST: mode = 'encode'

        context['text_input'] = text_input
        context['mode_used'] = mode

        if text_input is not None: # Process even empty string (useful for encode)
            print(f"Processing Base64 with mode: {mode}")
            processed_text, error_message = process_base64(text_input, mode)

            if error_message:
                messages.error(request, error_message)
                context['processed_text'] = None
            else:
                context['processed_text'] = processed_text
                # messages.success(request, f"Text successfully {mode}d!") # Optional

        # No explicit else needed if text_input is just empty

    # Render for GET or POST
    return render(request, 'utility_tools/tool_base64_encoder_decoder.html', context)








# utility_tools/views.py
from django.shortcuts import render
from django.contrib import messages
# ... other imports ...
# --- NEW IMPORT ---
from .unit_converter_logic import convert_units, UNIT_CATEGORIES, ALL_UNITS
# --- END NEW IMPORT ---



# --- NEW VIEW for Unit Converter ---
def unit_converter_view(request):
    context = {
        'page_title': 'Unit Converter',
        'unit_categories': UNIT_CATEGORIES, # Pass categories and units
        'all_units': ALL_UNITS,           # Pass all units for dropdowns
        'input_value': '',
        'from_unit': None, # Store selected units
        'to_unit': None,
        'converted_value': None,
    }

    if request.method == 'POST':
        input_value_str = request.POST.get('input_value', '').strip()
        from_unit = request.POST.get('from_unit')
        to_unit = request.POST.get('to_unit')

        # Store submitted values for repopulation
        context['input_value'] = input_value_str
        context['from_unit'] = from_unit
        context['to_unit'] = to_unit

        print(f"Attempting conversion: {input_value_str} {from_unit} -> {to_unit}")
        converted_value, error_message = convert_units(input_value_str, from_unit, to_unit)

        if error_message:
            messages.error(request, error_message)
            context['converted_value'] = None
        elif converted_value is not None:
            # Format the output nicely (e.g., limited decimal places)
            # This could be a user option later
            context['converted_value'] = f"{converted_value:.4f}".rstrip('0').rstrip('.') # Format to 4 places, remove trailing 0s/.
            print(f"Conversion result: {context['converted_value']}")
            # messages.success(request, "Conversion successful!") # Optional

    # Render for GET or POST
    return render(request, 'utility_tools/tool_unit_converter.html', context)








# utility_tools/views.py
from django.shortcuts import render
from django.contrib import messages
# ... other imports ...
# --- NEW IMPORT ---
from .color_converter_logic import parse_color_string, format_color_outputs
# --- END NEW IMPORT ---

# --- Existing Views ---
# ...

# --- NEW VIEW for Color Converter ---
def color_converter_view(request):
    context = {
        'page_title': 'Color Converter (HEX, RGB, HSL)',
        'color_input': '',
        'color_outputs': None, # Dict to hold results
    }

    if request.method == 'POST':
        color_input = request.POST.get('color_input', '').strip()
        context['color_input'] = color_input # Repopulate input

        if not color_input:
            messages.error(request, "Please enter a color value to convert.")
        else:
            print(f"Parsing color input: {color_input}")
            r, g, b, a = parse_color_string(color_input)

            if r is not None:
                print(f"Parsed RGBA: ({r},{g},{b},{a})")
                outputs = format_color_outputs(r, g, b, a)
                context['color_outputs'] = outputs
                print(f"Formatted outputs: {outputs}")
                # messages.success(request, "Color converted successfully!") # Optional
            else:
                messages.error(request, f"Could not parse color value: '{color_input}'. Try formats like #RRGGBB, rgb(r,g,b), rgba(r,g,b,a).")
                context['color_outputs'] = None

    # Render for GET or POST
    return render(request, 'utility_tools/tool_color_converter.html', context)









# utility_tools/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .qr_code_logic import generate_qr_code
from .barcode_generator_logic import generate_barcode, SUPPORTED_BARCODES, SIZE_PRESETS
import base64
import os
# Removed mimetypes import as we determine type from output format

def barcode_generator_view(request):
    # Clear session data
    if request.method == 'GET' or 'barcode_data' in request.POST:
        # Use more specific session keys
        if 'barcode_result_b64' in request.session: del request.session['barcode_result_b64']
        if 'barcode_result_filename' in request.session: del request.session['barcode_result_filename']
        if 'barcode_result_format' in request.session: del request.session['barcode_result_format']

    context = {
        'page_title': 'Barcode Generator',
        'data_input': request.POST.get('barcode_data', '') if request.method == 'POST' else '',
        'prev_options': request.POST if request.method == 'POST' else {},
        'barcode_types': SUPPORTED_BARCODES.keys(),
        'size_presets': SIZE_PRESETS.keys(),
        'generation_success': False # Default state
    }

    if request.method == 'POST':
        # --- Handle Download Request ---
        if 'download_barcode' in request.POST:
            barcode_data_b64 = request.session.get('barcode_result_b64')
            barcode_filename = request.session.get('barcode_result_filename', 'barcode.png')
            barcode_format = request.session.get('barcode_result_format', 'PNG') # Get stored format

            if barcode_data_b64:
                try:
                    barcode_data = base64.standard_b64decode(barcode_data_b64.encode('ascii')) # Use standard decode

                    # --- Set Correct Content Type ---
                    content_type = 'application/octet-stream' # Default fallback
                    if barcode_format.upper() == 'PNG':
                        content_type = 'image/png'
                    elif barcode_format.upper() == 'SVG':
                        content_type = 'image/svg+xml'
                    # --- End Content Type ---

                    print(f"[Download Barcode] Serving '{barcode_filename}', Type: {content_type}")
                    response = HttpResponse(barcode_data, content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="{barcode_filename}"'

                    # Clean up session ONLY after successful response creation
                    if 'barcode_result_b64' in request.session: del request.session['barcode_result_b64']
                    if 'barcode_result_filename' in request.session: del request.session['barcode_result_filename']
                    if 'barcode_result_format' in request.session: del request.session['barcode_result_format']
                    return response
                except Exception as e:
                    print(f"Error decoding/serving Barcode from session: {e}")
                    messages.error(request, "Could not retrieve generated Barcode.")
            else:
                messages.error(request, "No generated Barcode found to download.")
            return redirect('utility_tools:barcode_generator')

        # --- Handle Generation Request ---
        else:
            # ... (Get data and options as before) ...
            data_input = request.POST.get('barcode_data', '').strip()
            barcode_type = request.POST.get('barcode_type', 'Code128')
            output_format = request.POST.get('output_format', 'PNG')
            include_text = request.POST.get('include_text', 'on') == 'on'
            size_preset = request.POST.get('size_preset', 'M')

            # --- Validation (Keep as before) ---
            if not data_input: # ... etc ...
                messages.error(request, "Please enter data to encode.")
                return render(request, 'utility_tools/tool_barcode_generator.html', context)
            # ... other validations ...

            # --- Generation ---
            print(f"Generating Barcode. Type: {barcode_type}, Format: {output_format}, Text: {include_text}, Size: {size_preset}")
            barcode_data, output_filename, error_message = generate_barcode(
                data=data_input,
                barcode_type_name=barcode_type,
                output_format=output_format,
                include_text=include_text,
                size_preset=size_preset
            )
            # --- End Generation ---

            if barcode_data and output_filename:
                print("Barcode generation successful.")
                # Use standard base64 encoding
                barcode_image_b64 = base64.standard_b64encode(barcode_data).decode('ascii')
                request.session['barcode_result_b64'] = barcode_image_b64
                request.session['barcode_result_filename'] = output_filename
                request.session['barcode_result_format'] = output_format # Store format

                context['generation_success'] = True
                context['download_filename'] = output_filename
                context['barcode_image_b64'] = barcode_image_b64
                context['barcode_format'] = output_format # Pass format for display
                messages.success(request, "Barcode generated successfully!")
            else:
                print(f"Barcode generation failed: {error_message}")
                context['generation_success'] = False
                messages.error(request, error_message or "Failed to generate barcode.")

            return render(request, 'utility_tools/tool_barcode_generator.html', context)

    # --- GET Request Handling ---
    else:
         # Retrieve results from session if needed
        context['generation_success'] = request.session.get('barcode_result_b64') is not None
        if context['generation_success']:
            context['download_filename'] = request.session.get('barcode_result_filename')
            context['barcode_image_b64'] = request.session.get('barcode_result_b64')
            context['barcode_format'] = request.session.get('barcode_result_format')
        return render(request, 'utility_tools/tool_barcode_generator.html', context)
    











# utility_tools/views.py
from django.shortcuts import render
# ... other imports ...
# --- NEW IMPORT ---
from .password_generator_logic import generate_password
# --- END NEW IMPORT ---

# --- qr_code_view ---
# ...

# --- NEW VIEW for Password Generator ---
def password_generator_view(request):
    # Default settings
    default_length = 16
    default_uppercase = True
    default_lowercase = True
    default_numbers = True
    default_symbols = True

    generated_password = None
    error_message = None

    # Get settings from POST or use defaults for GET
    try:
        length = int(request.POST.get('length', default_length))
        length = max(8, min(length, 64)) # Clamp length between 8 and 64
    except ValueError:
        length = default_length

    # Checkboxes return 'on' if checked, None otherwise
    include_uppercase = request.POST.get('include_uppercase', 'on' if default_uppercase else None) == 'on'
    include_lowercase = request.POST.get('include_lowercase', 'on' if default_lowercase else None) == 'on'
    include_numbers = request.POST.get('include_numbers', 'on' if default_numbers else None) == 'on'
    include_symbols = request.POST.get('include_symbols', 'on' if default_symbols else None) == 'on'

    # Only generate on POST request
    if request.method == 'POST':
        if not any([include_uppercase, include_lowercase, include_numbers, include_symbols]):
            error_message = "Please select at least one character type."
        else:
            generated_password = generate_password(
                length=length,
                include_uppercase=include_uppercase,
                include_lowercase=include_lowercase,
                include_numbers=include_numbers,
                include_symbols=include_symbols
            )
            if not generated_password: # Should only happen if logic fails unexpectedly
                 error_message = "Could not generate password."


    context = {
        'page_title': 'Password Generator',
        'generated_password': generated_password,
        'error_message': error_message,
        'current_length': length,
        'include_uppercase': include_uppercase,
        'include_lowercase': include_lowercase,
        'include_numbers': include_numbers,
        'include_symbols': include_symbols,
    }
    return render(request, 'utility_tools/tool_password_generator.html', context)








# utility_tools/views.py
from django.shortcuts import render
from django.http import JsonResponse # For the 'Now' button AJAX later
from .qr_code_logic import generate_qr_code
# --- NEW IMPORT ---
from .timestamp_logic import convert_timestamp
from datetime import datetime, timezone # For 'Now' functionality
# --- END NEW IMPORT ---

# --- qr_code_view ---
# ...

# --- NEW VIEW for Timestamp Converter ---
def timestamp_converter_view(request):
    context = {
        'page_title': 'Unix Timestamp Converter',
        'input_value': '',
        'input_unit': 's', # Default unit
        'results': None,
    }

    if request.method == 'POST':
        input_value = request.POST.get('timestamp_input', '')
        unit = request.POST.get('timestamp_unit', 's')

        context['input_value'] = input_value # Repopulate form
        context['input_unit'] = unit # Repopulate form

        if input_value:
            results = convert_timestamp(input_value, unit)
            context['results'] = results # Pass results (including potential error)
        else:
             context['results'] = {'error': 'Please enter a value to convert.'}

    elif request.method == 'GET':
         # Handle 'now' parameter if provided by JS button
         if request.GET.get('now') == 'true':
             now_ts = int(datetime.now(timezone.utc).timestamp())
             context['input_value'] = str(now_ts)
             # Optionally auto-convert on GET with 'now'?
             # results = convert_timestamp(str(now_ts), 's')
             # context['results'] = results

    return render(request, 'utility_tools/tool_timestamp_converter.html', context)








# utility_tools/views.py
from django.shortcuts import render

# ... (other utility views if any) ...

def gradient_generator_view(request):
    """Displays the CSS Gradient Generator tool page."""
    context = {
        'page_title': 'CSS Gradient Generator'
    }
    # No POST handling needed for V1 as generation is client-side
    return render(request, 'utility_tools/tool_gradient_generator.html', context)






# utility_tools/views.py
from django.shortcuts import render
from django.contrib import messages
from .qr_code_logic import generate_qr_code
# --- NEW IMPORTS ---
from .timezone_converter_logic import convert_timezone, get_available_timezones
from datetime import datetime # Import datetime for default value
# --- END NEW IMPORTS ---

# --- qr_code_view ---
# ...

# --- NEW VIEW for Timezone Converter ---
def timezone_converter_view(request):
    # Get available timezones for dropdowns
    available_tzs = get_available_timezones()

    context = {
        'page_title': 'Time Zone Converter',
        'timezones': available_tzs,
        'source_tz': request.POST.get('source_tz', 'UTC'), # Default source
        'target_tz': request.POST.get('target_tz', 'America/New_York'), # Default target
        # Provide current date/time as default placeholder/value
        # Format MUST match expected input format 'YYYY-MM-DD HH:MM'
        'datetime_input': request.POST.get('datetime_input', datetime.now().strftime('%Y-%m-%d %H:%M')),
        'converted_time_str': None,
        'error_message': None,
    }

    if request.method == 'POST':
        input_dt_str = request.POST.get('datetime_input', '').strip()
        source_tz_str = request.POST.get('source_tz', '')
        target_tz_str = request.POST.get('target_tz', '')

        # Basic validation - more done in logic function
        if not all([input_dt_str, source_tz_str, target_tz_str]):
            messages.error(request, "Please select source/target timezones and enter date/time.")
        else:
            # Perform conversion
            converted_dt, formatted_output, error = convert_timezone(
                input_dt_str=input_dt_str,
                source_tz_str=source_tz_str,
                target_tz_str=target_tz_str
            )

            if error:
                messages.error(request, error)
                context['error_message'] = error
            elif formatted_output:
                messages.success(request, "Time converted successfully!")
                context['converted_time_str'] = formatted_output
            else:
                # Should ideally be caught by error above, but as fallback
                messages.error(request, "An unknown error occurred during conversion.")

    # Always render the template (GET or POST)
    return render(request, 'utility_tools/tool_timezone_converter.html', context)







# utility_tools/views.py
from django.shortcuts import render
from django.contrib import messages
# --- NEW IMPORT ---
from .random_number_logic import generate_random_integers
# --- END NEW IMPORT ---
# ... other imports ...

# --- qr_code_view ---
# ... (keep existing view) ...


# --- NEW VIEW for Random Number Generator ---
def random_number_view(request):
    context = {
        'page_title': 'Random Number Generator',
        'results': None, # Store generated numbers list
        'prev_options': {}, # Store previous input for repopulation
    }

    if request.method == 'POST':
        # Get form data
        min_val_str = request.POST.get('min_value', '').strip()
        max_val_str = request.POST.get('max_value', '').strip()
        count_str = request.POST.get('count', '1').strip() # Default count to 1

        context['prev_options'] = request.POST # Store for repopulation

        # --- Robust Validation ---
        min_val, max_val, count = None, None, None
        try:
            if not min_val_str: raise ValueError("Minimum value is required.")
            min_val = int(min_val_str)

            if not max_val_str: raise ValueError("Maximum value is required.")
            max_val = int(max_val_str)

            if not count_str: raise ValueError("Number of results is required.")
            count = int(count_str)

            if count < 1:
                raise ValueError("Number of results must be at least 1.")
            if count > 10000: # Add a reasonable upper limit
                 raise ValueError("Cannot generate more than 10,000 numbers at once.")
            if min_val > max_val:
                 raise ValueError("Minimum value cannot be greater than Maximum value.")

            # Add reasonable limits on min/max values if desired
            # if min_val < -1_000_000_000 or max_val > 1_000_000_000:
            #    raise ValueError("Minimum/Maximum value out of reasonable range.")

        except ValueError as e:
            messages.error(request, f"Invalid input: {e}")
            # Render form again with error and previous input
            return render(request, 'utility_tools/tool_random_number_generator.html', context)
        # --- End Validation ---

        # --- Generation ---
        results = generate_random_integers(min_val, max_val, count)
        # --- End Generation ---

        if results is not None: # Check if generation was successful
            context['results'] = results
            messages.success(request, f"Generated {count} random number(s).")
        else:
            # Logic function should have printed specifics
            messages.error(request, "Could not generate numbers. Please check input values.")

        # Render the page with results or errors
        return render(request, 'utility_tools/tool_random_number_generator.html', context)

    # --- GET Request Handling ---
    else:
        # Just display the form with default values perhaps
        context['prev_options'] = {'min_value': '1', 'max_value': '100', 'count': '1'} # Set defaults for GET
        return render(request, 'utility_tools/tool_random_number_generator.html', context)
    







# utility_tools/views.py
from django.shortcuts import render
# ... other imports if needed ...



# --- NEW VIEW for Calculator ---
def calculator_view(request):
    """Renders the Calculator tool page."""
    context = {
        'page_title': 'Online Calculator (Simple & Scientific)'
    }
    # No backend calculation needed, just render the template
    return render(request, 'utility_tools/tool_calculator.html', context)
# --- END NEW VIEW ---







# utility_tools/views.py
from django.shortcuts import render
# ... other imports ...
# --- NEW IMPORT ---
from .ip_info_logic import get_client_ip
# --- END NEW IMPORT ---

# --- qr_code_view (keep as before) ---
# ...

# --- NEW VIEW for What's My IP ---
def whats_my_ip_view(request):
    """Displays the user's detected public IP address."""
    client_ip = get_client_ip(request) # Call the logic function
    context = {
        'page_title': "What's My IP Address?",
        'client_ip': client_ip,
    }
    return render(request, 'utility_tools/tool_whats_my_ip.html', context)













# utility_tools/views.py
from django.shortcuts import render
# ... other imports ...

# --- qr_code_view (keep as before) ---
# ...

# --- NEW VIEW for Screen Resolution ---
def screen_resolution_view(request):
    """Displays the screen resolution detection tool page."""
    context = {
        'page_title': 'What Is My Screen Resolution?'
    }
    return render(request, 'utility_tools/tool_screen_resolution.html', context)