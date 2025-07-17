# pdf_tools/merge_pdf_logic.py
import io
import os
from PyPDF2 import PdfReader, PdfWriter # Updated import for PyPDF2 v3+

def merge_pdf_files(pdf_files):
    """
    Merges multiple uploaded PDF file objects into a single PDF document.

    Args:
        pdf_files: A list of Django UploadedFile objects (validated as PDFs).

    Returns:
        tuple: (bytes: Merged PDF content or None, str: output filename or None) on success,
               or (None, None) on error.
    """
    if not pdf_files or len(pdf_files) < 2:
        print("[Merge PDF Logic] Error: Less than two files provided.")
        return None, "merged_document.pdf" # Return default name even on error? Or None?

    pdf_writer = PdfWriter()

    try:
        print(f"[Merge PDF Logic] Starting merge for {len(pdf_files)} files.")
        for uploaded_file in pdf_files:
            try:
                # Important: PyPDF2 needs the stream/file object directly
                uploaded_file.seek(0) # Go to the start of the file stream
                pdf_reader = PdfReader(uploaded_file)
                if pdf_reader.is_encrypted:
                    # Attempt to decrypt with empty password - might fail
                    try:
                       if pdf_reader.decrypt("") == 0: # 0 means decryption failed
                            print(f"[Merge PDF Logic] Error: File '{uploaded_file.name}' is encrypted and cannot be decrypted.")
                            # Consider how to handle this - skip file or fail entirely? Let's fail for now.
                            # To skip: uncomment 'continue' and remove 'return None, None'
                            # continue
                            return None, "merged_document.pdf" # Fail if any file is encrypted and fails decrypt
                    except Exception as decrypt_err:
                        print(f"[Merge PDF Logic] Error decrypting file '{uploaded_file.name}': {decrypt_err}")
                        return None, "merged_document.pdf"

                # Add all pages from the current reader to the writer
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
                print(f"[Merge PDF Logic] Added {len(pdf_reader.pages)} pages from '{uploaded_file.name}'.")

            except Exception as read_err:
                print(f"[Merge PDF Logic] Error reading PDF file '{uploaded_file.name}': {read_err}")
                # Decide if one bad file should stop the whole process
                return None, "merged_document.pdf" # Fail merge if any file is invalid

        # Write the merged PDF to an in-memory buffer
        output_buffer = io.BytesIO()
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)

        print("[Merge PDF Logic] Merge successful.")
        return output_buffer.getvalue(), "merged_document.pdf"

    except Exception as e:
        print(f"Error during PDF merging process: {e}")
        import traceback
        traceback.print_exc()
        return None, "merged_document.pdf"
    finally:
        # No specific cleanup needed for PdfWriter/Reader objects usually,
        # but ensure input file streams are handled correctly by Django/view.
        pass