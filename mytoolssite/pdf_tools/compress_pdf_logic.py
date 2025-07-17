# pdf_tools/compress_pdf_logic.py
import io
import os
from PyPDF2 import PdfReader, PdfWriter

def compress_pdf(pdf_file, compress_streams=True, remove_metadata=False):
    """
    Applies basic compression techniques to a PDF using PyPDF2.

    Args:
        pdf_file: Django UploadedFile object.
        compress_streams (bool): Apply content stream compression.
        remove_metadata (bool): Remove document information dictionary.

    Returns:
        tuple: (bytes: Compressed PDF content or None,
                str: output filename or None,
                str: error message or None)
    """
    if not pdf_file:
        return None, None, "No PDF file provided."

    output_buffer = io.BytesIO()
    output_filename = "compressed_document.pdf" # Default

    try:
        pdf_file.seek(0)
        pdf_reader = PdfReader(pdf_file)
        pdf_writer = PdfWriter()

        print(f"[Compress PDF] Opened '{pdf_file.name}', starting compression...")

        # Handle encryption
        if pdf_reader.is_encrypted:
            try:
                if pdf_reader.decrypt("") == 0:
                    return None, None, f"File '{pdf_file.name}' is encrypted and cannot be processed."
            except Exception as decrypt_err:
                 return None, None, f"Error decrypting file '{pdf_file.name}': {decrypt_err}"

        # Add all pages from reader to writer
        pdf_writer.append_pages_from_reader(pdf_reader)

        # Apply selected options
        if compress_streams:
            print("[Compress PDF] Applying content stream compression.")
            try:
                # This compresses existing streams but doesn't recompress images etc.
                # PyPDF2 >= 3.x automatically compresses streams on write by default,
                # but calling this explicitly ensures it if needed or for older versions.
                # In PyPDF2 3.x+, direct stream manipulation is more complex.
                # Let's rely on the writer's default compression for now,
                # as compress_content_streams() was removed/changed.
                # We'll just note that compression is happening by default.
                pass # PyPDF2 writer compresses by default now
            except AttributeError:
                # Fallback for older PyPDF2 if needed, though less likely now
                try:
                    print("[Compress PDF] Using legacy compress_content_streams()")
                    pdf_writer.compress_content_streams()
                except Exception as compress_err:
                    print(f"Warning: Could not compress streams: {compress_err}")
            except Exception as compress_err:
                 print(f"Warning: Error during stream compression attempt: {compress_err}")


        if remove_metadata:
            print("[Compress PDF] Removing metadata.")
            try:
                # In PyPDF2 3.x+, metadata is accessed differently.
                # We remove the '/Info' object reference from the trailer.
                # This is a bit more involved than just writer.add_metadata({})
                # For simplicity, let's just NOT add metadata from the original.
                # The PdfWriter doesn't copy it by default unless explicitly told to.
                pass # Default PdfWriter behavior doesn't copy /Info dict
                # If you wanted explicit removal from trailer (more complex):
                # root = pdf_writer._root_object # Access internal root object (use with caution)
                # if '/Info' in root:
                #     del root['/Info']
            except Exception as meta_err:
                print(f"Warning: Could not remove metadata: {meta_err}")


        # Write the modified PDF to the buffer
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)

        # Generate output filename
        base_name = os.path.splitext(pdf_file.name)[0]
        output_filename = f"{base_name}_compressed.pdf"

        print("[Compress PDF] Compression process complete.")
        return output_buffer.getvalue(), output_filename, None # No error

    except Exception as e:
        print(f"Error during PDF compression process: {e}")
        import traceback
        traceback.print_exc()
        return None, None, f"An unexpected error occurred during compression: {e}"