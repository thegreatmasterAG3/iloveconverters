# pdf_tools/pdf_to_excel_logic.py
import io
import os
import re
import pandas as pd
# Ensure tabula is installed: pip install tabula-py pandas openpyxl
# Ensure JAVA is installed and in PATH
try:
    import tabula
    TABULA_AVAILABLE = True
except ImportError:
    print("WARNING: tabula-py not installed or Java not found. PDF to Excel will fail.")
    TABULA_AVAILABLE = False
except Exception as e: # Catch potential Java related errors on import
    print(f"WARNING: Error importing tabula-py (likely Java issue): {e}")
    TABULA_AVAILABLE = False


def parse_page_ranges_for_tabula(page_string, total_pages):
    """
    Parses a string like '1, 3-5, 8' into a format suitable for tabula-py's 'pages' argument.
    Can be 'all', a list of 1-based page numbers, or a string like '1,3-5'.
    Returns the processed string/list or None and error message.
    """
    if not page_string:
        return None, "Page range string cannot be empty."

    # Basic validation for allowed characters
    if not re.match(r'^[0-9,\-\s]+$', page_string):
        return None, "Invalid characters found. Use numbers, commas, hyphens, spaces."

    # Further validation could be done here (like ensuring ranges are valid),
    # but tabula handles some validation internally. Let's pass the string for now.
    # We *should* check if page numbers exceed total_pages, but tabula might ignore them.
    # For simplicity in V1, pass the raw validated string.
    print(f"Using page string for tabula: '{page_string}'")
    return page_string, None


def convert_pdf_to_excel(pdf_file, page_selection_mode='all', page_string=None, extraction_method='lattice'):
    """
    Extracts tables from PDF and saves them to an Excel file using tabula-py.

    Args:
        pdf_file: Django UploadedFile object.
        page_selection_mode (str): 'all' or 'specific'.
        page_string (str): Comma/space separated pages/ranges if mode is 'specific'.
        extraction_method (str): 'lattice' or 'stream'.

    Returns:
        tuple: (bytes: Excel (.xlsx) content or None,
                str: output filename or None,
                str: error message or None)
    """
    if not TABULA_AVAILABLE:
        return None, None, "Server configuration error: PDF table extraction library (tabula-py / Java) not available."
    if not pdf_file:
        return None, None, "No PDF file provided."

    output_buffer = io.BytesIO()
    output_filename = "extracted_tables.xlsx"

    # tabula-py works best with file paths
    temp_pdf_path = None
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            for chunk in pdf_file.chunks():
                temp_pdf.write(chunk)
            temp_pdf_path = temp_pdf.name
        print(f"[PDF->Excel Logic] Saved temp PDF to: {temp_pdf_path}")

        # Determine pages argument for tabula
        pages_arg = 'all'
        if page_selection_mode == 'specific':
             # Validate/process page string (basic validation here, tabula does more)
             try:
                 from PyPDF2 import PdfReader # Use for quick page count check
                 pdf_file.seek(0)
                 reader_check = PdfReader(pdf_file)
                 # Cannot easily check encryption here before tabula runs
                 total_pages = len(reader_check.pages)
             except Exception as e:
                 print(f"Could not get page count via PyPDF2: {e}")
                 total_pages = None # Can't validate range fully

             processed_page_string, error = parse_page_ranges_for_tabula(page_string, total_pages)
             if error:
                 return None, None, error
             pages_arg = processed_page_string # Use the comma-separated string/list
        print(f"[PDF->Excel Logic] Using pages='{pages_arg}' and method='{extraction_method}'")

        # --- Use tabula-py to read tables ---
        # lattice=True is equivalent to method='lattice'
        # stream=True is equivalent to method='stream'
        use_lattice = extraction_method == 'lattice'
        dfs = tabula.read_pdf(temp_pdf_path, pages=pages_arg, lattice=use_lattice, stream=(not use_lattice), multiple_tables=True, pandas_options={'header': None})
        # --- End Table Extraction ---

        if not dfs: # Check if the list of dataframes is empty
             print("[PDF->Excel Logic] No tables found by tabula.")
             return None, None, "No tables were detected in the selected pages using the chosen method. Try the other method?"

        print(f"[PDF->Excel Logic] Extracted {len(dfs)} tables. Writing to Excel...")

        # --- Write DataFrames to Excel using pandas ---
        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
            for i, df in enumerate(dfs):
                # Use a generic sheet name
                # Improve sheet naming later if possible (e.g., Page X - Table Y)
                sheet_name = f'Table_{i+1}'
                # Write dataframe to a sheet, without index and header
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
        # --- End Excel Writing ---

        output_buffer.seek(0)

        base_name = os.path.splitext(pdf_file.name)[0]
        output_filename = f"{base_name}_tables.xlsx"

        print("[PDF->Excel Logic] Excel file created successfully.")
        return output_buffer.getvalue(), output_filename, None

    # Handle potential Java not found error specifically if possible
    except FileNotFoundError as e:
         if 'java' in str(e).lower():
             print(f"[PDF->Excel Logic] Error: Java runtime not found or not in PATH.")
             return None, None, "Server configuration error: Java runtime is required but not found."
         else:
              # Handle other FileNotFoundError (e.g., temp file issue)
              print(f"Error during PDF to Excel conversion (FileNotFound): {e}")
              import traceback; traceback.print_exc()
              return None, None, f"An error occurred (File Not Found): {e}"
    except Exception as e:
        print(f"Error during PDF to Excel conversion process: {e}")
        import traceback
        traceback.print_exc()
        # Provide specific feedback for common tabula issues if possible
        error_msg = f"An error occurred during table extraction: {e}. Ensure the PDF is not scanned (image-based) and Java is installed."
        return None, None, error_msg
    finally:
        # Clean up temporary PDF file
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
                print(f"[PDF->Excel Logic] Deleted temp PDF: {temp_pdf_path}")
            except OSError as e:
                print(f"[PDF->Excel Logic] Error deleting temp PDF {temp_pdf_path}: {e}")