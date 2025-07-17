# pdf_tools/jpg_to_pdf_converter.py
import io
from PIL import Image # Only Pillow is needed now

def convert_images_to_pdf_pillow(image_files, page_size_str='A4', orientation_pref='Auto', margin_mm=10):
    """
    Converts a list of uploaded image file objects (JPGs) into a
    single PDF document using Pillow.
    NOTE: This version currently IGNORES page_size, orientation, and margin options
          for simplicity to ensure basic PDF generation works.

    Args:
        image_files: A list of Django UploadedFile objects (validated as JPGs).
        page_size_str (str): Currently ignored.
        orientation_pref (str): Currently ignored.
        margin_mm (int): Currently ignored.

    Returns:
        bytes: The generated PDF content as bytes, or None if an error occurs.
    """
    if not image_files:
        print("No image files received by converter.")
        return None

    opened_images = []
    try:
        # First, open all images and convert to RGB if necessary
        print(f"Processing {len(image_files)} files...")
        for i, uploaded_file in enumerate(image_files):
            print(f"Processing file {i+1}: {uploaded_file.name}")
            uploaded_file.seek(0) # Rewind file pointer
            try:
                img = Image.open(uploaded_file)
                print(f"  Opened {uploaded_file.name}, mode: {img.mode}")

                # Ensure image is in RGB format - crucial for Pillow's PDF saving
                if img.mode == 'RGBA':
                    print(f"  Converting {uploaded_file.name} from RGBA to RGB...")
                    # Create a white background image
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    # Paste the RGBA image onto the white background
                    # Use alpha channel (index 3) as mask
                    background.paste(img, mask=img.getchannel('A') if 'A' in img.getbands() else None)
                    opened_images.append(background)
                    img.close() # Close original RGBA image
                elif img.mode != 'RGB':
                    print(f"  Converting {uploaded_file.name} from {img.mode} to RGB...")
                    rgb_img = img.convert('RGB')
                    opened_images.append(rgb_img)
                    img.close() # Close original non-RGB image
                else:
                    opened_images.append(img) # Already RGB

            except Exception as e:
                print(f"Error opening/processing image {uploaded_file.name} with Pillow: {e}")
                # Clean up already opened images if one fails
                for opened_img in opened_images:
                    opened_img.close()
                return None # Indicate failure

        if not opened_images:
            print("No valid images could be opened/processed.")
            return None # No valid images opened

        # Use the first image as the base for saving
        first_image = opened_images[0]
        other_images = opened_images[1:]

        # Save to an in-memory BytesIO buffer
        pdf_buffer = io.BytesIO()
        print("Saving images to PDF buffer...")

        # Save the first image, and append the rest
        first_image.save(
            pdf_buffer,
            format="PDF",
            resolution=100.0, # Default resolution
            save_all=True, # Important for appending
            append_images=other_images # List of other Pillow image objects
        )
        print("PDF buffer populated.")

        # Clean up Pillow image objects
        for opened_img in opened_images:
            opened_img.close()
        print("Closed Pillow image objects.")

        pdf_buffer.seek(0) # Rewind buffer
        pdf_bytes = pdf_buffer.getvalue()
        print(f"Generated PDF bytes length: {len(pdf_bytes)}")
        return pdf_bytes # Return PDF bytes

    except Exception as e:
        print(f"Error during PDF creation with Pillow: {e}")
        import traceback
        traceback.print_exc()
        # Clean up any remaining opened images in case of error during save
        for opened_img in opened_images:
            try:
                opened_img.close()
            except Exception: pass
        return None
    # No 'finally' needed as opened_images cleanup happens on success or exception