from django.shortcuts import render
from .word_count_logic import calculate_text_stats # Import the logic

def word_count_view(request):
    context = {
        'page_title': 'Word Counter',
        'text_input': '', # Store input text for repopulation
        'stats': None,    # Store results dictionary
    }

    if request.method == 'POST':
        text_input = request.POST.get('text_input', '')
        context['text_input'] = text_input # Store for repopulation

        if text_input:
            print("Calculating stats...")
            stats = calculate_text_stats(text_input)
            context['stats'] = stats
            print(f"Stats calculated: {stats}")
        else:
            # Optionally show a message if submitted empty
            # from django.contrib import messages
            # messages.info(request, "Please enter some text to count.")
            context['stats'] = calculate_text_stats('') # Get zero stats

    # For GET or after POST, render the page
    return render(request, 'text_tools/tool_word_counter.html', context)






# text_tools/views.py
from django.shortcuts import render
from .word_count_logic import calculate_text_stats
# --- NEW IMPORT ---
from .case_converter_logic import convert_case
# --- END NEW IMPORT ---


# --- NEW VIEW for Case Converter ---
def case_converter_view(request):
    context = {
        'page_title': 'Case Converter',
        'text_input': '',
        'converted_text': '',
        'selected_case': 'lower', # Default selected case
    }

    if request.method == 'POST':
        text_input = request.POST.get('text_input', '').strip()
        case_type = request.POST.get('case_type', 'lower') # Get selected case type

        context['text_input'] = text_input # Repopulate input
        context['selected_case'] = case_type # Remember selected option

        if text_input:
            print(f"Converting case to: {case_type}")
            converted_text = convert_case(text_input, case_type)
            context['converted_text'] = converted_text
            print("Conversion complete.")
        else:
            context['converted_text'] = '' # Clear output if input is empty

    # Render for GET or POST
    return render(request, 'text_tools/tool_case_converter.html', context)






# text_tools/views.py
from django.shortcuts import render
from .word_count_logic import calculate_text_stats
from .case_converter_logic import convert_case
# --- NEW IMPORT ---
from .lorem_ipsum_logic import generate_lorem_ipsum
# --- END NEW IMPORT ---



# --- NEW VIEW for Lorem Ipsum ---
def lorem_ipsum_view(request):
    context = {
        'page_title': 'Lorem Ipsum Generator',
        'generated_text': '',
        # Default options for GET request or initial load
        'prev_count': 5,
        'prev_unit': 'p',
        'prev_start_with_lorem': True,
    }

    if request.method == 'POST':
        try:
            count = int(request.POST.get('count', 5))
            count = max(1, count) # Ensure at least 1
        except ValueError:
            count = 5 # Default on error

        unit = request.POST.get('unit', 'p')
        if unit not in ['p', 's', 'w']:
            unit = 'p' # Default

        start_with_lorem = request.POST.get('start_with_lorem', 'off') == 'on'

        print(f"Requesting Lorem Ipsum: Count={count}, Unit={unit}, Start Standard={start_with_lorem}")

        generated_text = generate_lorem_ipsum(
            count=count,
            unit=unit,
            start_with_lorem=start_with_lorem
        )

        context['generated_text'] = generated_text
        # Store submitted options to repopulate form
        context['prev_count'] = count
        context['prev_unit'] = unit
        context['prev_start_with_lorem'] = start_with_lorem

        if not generated_text:
             from django.contrib import messages # Import if not already done
             messages.error(request, "Could not generate Lorem Ipsum text.")

    # Render for GET or POST
    return render(request, 'text_tools/tool_lorem_ipsum.html', context)





# text_tools/views.py
from django.shortcuts import render
from .word_count_logic import calculate_text_stats
from .case_converter_logic import convert_case
# --- NEW IMPORT ---
from .reverse_text_logic import reverse_text_logic
# --- END NEW IMPORT ---


# --- NEW VIEW for Reverse Text ---
def reverse_text_view(request):
    context = {
        'page_title': 'Reverse Text',
        'text_input': '',
        'reversed_text': '',
        'selected_mode': 'string', # Default mode
    }

    if request.method == 'POST':
        text_input = request.POST.get('text_input', '').strip()
        reverse_mode = request.POST.get('reverse_mode', 'string') # Get selected mode

        context['text_input'] = text_input
        context['selected_mode'] = reverse_mode

        if text_input:
            print(f"Reversing text with mode: {reverse_mode}")
            reversed_text = reverse_text_logic(text_input, reverse_mode)
            context['reversed_text'] = reversed_text
            print("Reversal complete.")
        else:
            context['reversed_text'] = ''

    # Render for GET or POST
    return render(request, 'text_tools/tool_reverse_text.html', context)







# text_tools/views.py
from django.shortcuts import render
from .word_count_logic import calculate_text_stats
# --- NEW IMPORT ---
from .line_break_remover_logic import process_line_breaks
# --- END NEW IMPORT ---

# --- word_count_view (Keep as before) ---
# ...

# --- NEW VIEW for Remove Line Breaks ---
def remove_line_breaks_view(request):
    context = {
        'page_title': 'Remove Line Breaks',
        'text_input': '',
        'processed_text': None, # To store the result
        'selected_mode': 'remove_all' # Default mode
    }

    if request.method == 'POST':
        text_input = request.POST.get('text_input', '')
        selected_mode = request.POST.get('processing_mode', 'remove_all')

        context['text_input'] = text_input # Repopulate input
        context['selected_mode'] = selected_mode # Keep selected option

        if text_input:
            print(f"Processing line breaks. Mode: {selected_mode}")
            processed_text = process_line_breaks(text_input, selected_mode)
            context['processed_text'] = processed_text
            print("Processing complete.")
        else:
             # Optionally show message or just show empty output
             context['processed_text'] = "" # Show empty output for empty input

    # Render the page for GET or after POST
    return render(request, 'text_tools/tool_remove_line_breaks.html', context)








# text_tools/views.py
from django.shortcuts import render
from .word_count_logic import calculate_text_stats
# --- NEW IMPORT ---
from .text_cleaner_logic import clean_text_data
# --- END NEW IMPORT ---

# --- word_count_view (keep as before) ---
# ...

# --- NEW VIEW for Text Cleaner ---
def text_cleaner_view(request):
    context = {
        'page_title': 'Text Cleaner',
        'text_input': '',
        'cleaned_text': '',
        'options': {}, # To store checked options for template
        'cleaning_done': False
    }

    if request.method == 'POST':
        text_input = request.POST.get('text_input', '')
        context['text_input'] = text_input

        # Get selected options from checkboxes
        options = {
            'remove_extra_spaces': request.POST.get('remove_extra_spaces') == 'on',
            'remove_all_line_breaks': request.POST.get('remove_all_line_breaks') == 'on',
            'remove_empty_lines': request.POST.get('remove_empty_lines') == 'on',
            'remove_html': request.POST.get('remove_html') == 'on',
            'trim_lines': request.POST.get('trim_lines') == 'on',
        }
        context['options'] = options # Pass selected options back

        if text_input:
            cleaned_text = clean_text_data(text_input, options)
            context['cleaned_text'] = cleaned_text
            context['cleaning_done'] = True # Flag to show output area
        else:
            # Handle empty input submission if needed
            pass

    # For GET or after POST, render the page
    return render(request, 'text_tools/tool_text_cleaner.html', context)








# text_tools/views.py
from django.shortcuts import render
from .word_count_logic import calculate_text_stats
# --- NEW IMPORT ---
from .text_compare_logic import generate_side_by_side_diff
# --- END NEW IMPORT ---

# --- word_count_view ---
# ...

# --- NEW VIEW for Text Compare ---
def text_compare_view(request):
    context = {
        'page_title': 'Text Compare (Diff Tool)',
        'text_a': '',
        'text_b': '',
        'diff_result': None,
        'options': {'ignore_whitespace': False, 'ignore_case': False} # Default options
    }

    if request.method == 'POST':
        text_a = request.POST.get('text_a', '')
        text_b = request.POST.get('text_b', '')
        ignore_whitespace_opt = request.POST.get('ignore_whitespace') == 'on'
        ignore_case_opt = request.POST.get('ignore_case') == 'on'

        # Store submitted text and options for repopulating form
        context['text_a'] = text_a
        context['text_b'] = text_b
        context['options'] = {
            'ignore_whitespace': ignore_whitespace_opt,
            'ignore_case': ignore_case_opt
        }

        print(f"Comparing texts. Ignore Whitespace: {ignore_whitespace_opt}, Ignore Case: {ignore_case_opt}")
        # --- Generate Diff ---
        diff_data = generate_side_by_side_diff(
            text_a,
            text_b,
            ignore_whitespace=ignore_whitespace_opt,
            ignore_case=ignore_case_opt
        )
        # --- End Diff ---

        if diff_data is not None:
            print(f"Diff generated with {len(diff_data)} rows.")
            context['diff_result'] = diff_data
        else:
            # Should only happen if inputs were None, but good practice
             print("Diff generation failed (inputs might be invalid).")
             # messages.error(request, "Could not generate comparison.") # Optional

    # Render page for GET or after POST
    return render(request, 'text_tools/tool_text_compare.html', context)





# text_tools/views.py
from django.shortcuts import render
# ... other imports if needed ...
from .word_count_logic import calculate_text_stats

# --- word_count_view (Keep as before) ---
# ...

# --- NEW VIEW for Markdown Previewer ---
def markdown_previewer_view(request):
    """Displays the Markdown Previewer tool page."""
    context = {
        'page_title': 'Markdown Previewer'
    }
    # No data processing needed on the backend for this tool
    return render(request, 'text_tools/tool_markdown_previewer.html', context)





# text_tools/views.py
from django.shortcuts import render
from .word_count_logic import calculate_text_stats



# --- NEW VIEW for Slug Generator ---
def slug_generator_view(request):
    """Renders the template for the Slug Generator tool."""
    context = {
        'page_title': 'Slug Generator'
    }
    return render(request, 'text_tools/tool_slug_generator.html', context)
# --- END NEW VIEW ---





# text_tools/views.py
from django.shortcuts import render
from .word_count_logic import calculate_text_stats
# --- NEW IMPORT ---
from .json_formatter_logic import format_json_string
# --- END NEW IMPORT ---

# --- word_count_view (Keep as before) ---
# ...

# --- NEW VIEW for JSON Formatter ---
def json_formatter_view(request):
    context = {
        'page_title': 'JSON Formatter & Validator',
        'input_text': '',
        'formatted_json': None,
        'error_message': None,
        'prev_options': {} # Store previous options
    }

    if request.method == 'POST':
        input_text = request.POST.get('json_input', '')
        indent_style = request.POST.get('indent_style', '4') # Get indent option
        sort_keys_opt = request.POST.get('sort_keys', 'off') == 'on' # Get sort option

        context['input_text'] = input_text # Keep input for display
        context['prev_options'] = request.POST # Keep selected options

        if input_text:
            print(f"Formatting JSON. Indent: {indent_style}, Sort Keys: {sort_keys_opt}")
            formatted_json, error_message = format_json_string(
                input_json_str=input_text,
                indent_style=indent_style,
                sort_keys=sort_keys_opt
            )
            context['formatted_json'] = formatted_json
            context['error_message'] = error_message
            if error_message:
                print(f"Formatting error: {error_message}")
            else:
                 print("Formatting successful.")
        else:
            context['error_message'] = "Please paste or type JSON data into the input area."

    return render(request, 'text_tools/tool_json_formatter.html', context)









# text_tools/views.py
from django.shortcuts import render
import re # For cleaning binary input


# --- NEW VIEW for Binary Converter ---
def binary_converter_view(request):
    context = {
        'page_title': 'Binary Converter',
        'input_data': '',
        'output_data': '',
        'conversion_mode': 'text_to_binary', # Default mode
        'error': None
    }

    if request.method == 'POST':
        input_data = request.POST.get('input_data', '').strip()
        conversion_mode = request.POST.get('conversion_mode', 'text_to_binary')

        context['input_data'] = input_data # Repopulate input
        context['conversion_mode'] = conversion_mode # Keep selected mode

        if not input_data:
            context['error'] = "Please enter some text or binary code to convert."
        else:
            try:
                if conversion_mode == 'text_to_binary':
                    print("[Bin Convert] Converting Text to Binary")
                    # 1. Encode text to bytes using UTF-8
                    byte_array = input_data.encode('utf-8')
                    # 2. Convert each byte to its 8-bit binary representation, join with spaces
                    binary_list = [format(byte, '08b') for byte in byte_array]
                    context['output_data'] = ' '.join(binary_list)
                    print("[Bin Convert] Text to Binary Success")

                elif conversion_mode == 'binary_to_text':
                    print("[Bin Convert] Converting Binary to Text")
                    # 1. Clean input: remove anything not 0, 1, or space. Remove excess spaces.
                    cleaned_binary = re.sub(r'[^\s01]+', '', input_data) # Remove invalid chars
                    cleaned_binary = re.sub(r'\s+', ' ', cleaned_binary).strip() # Normalize spaces

                    # 2. Split into potential byte strings
                    binary_chunks = cleaned_binary.split(' ')

                    byte_list = []
                    for chunk in binary_chunks:
                        if len(chunk) == 8 and all(c in '01' for c in chunk):
                            # Convert 8-bit binary string to integer, then to byte
                            byte_val = int(chunk, 2)
                            byte_list.append(byte_val)
                        elif chunk: # If chunk exists but isn't valid 8-bit binary
                            raise ValueError(f"Invalid binary sequence found: '{chunk}'. Please use space-separated 8-bit groups (e.g., 01001000 01101001).")

                    if not byte_list:
                         raise ValueError("No valid 8-bit binary sequences found in input.")

                    # 3. Create bytes object and decode using UTF-8
                    byte_data = bytes(byte_list)
                    context['output_data'] = byte_data.decode('utf-8', errors='replace') # Replace invalid UTF-8 chars
                    print("[Bin Convert] Binary to Text Success")

                else:
                    context['error'] = "Invalid conversion mode selected."

            except ValueError as ve:
                 print(f"[Bin Convert] ValueError: {ve}")
                 context['error'] = str(ve) # Show specific validation error
            except UnicodeDecodeError:
                 print("[Bin Convert] UnicodeDecodeError")
                 context['error'] = "The binary sequence could not be decoded back to valid text (UTF-8). It might be incomplete or represent different data."
            except Exception as e:
                print(f"[Bin Convert] General Error: {e}")
                context['error'] = "An unexpected error occurred during conversion."
                import traceback
                traceback.print_exc()

    # For GET or POST, render the page
    return render(request, 'text_tools/tool_binary_converter.html', context)