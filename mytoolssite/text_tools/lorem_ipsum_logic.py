# text_tools/lorem_ipsum_logic.py
from lorem_text import lorem
import random
import re

def generate_lorem_ipsum(count=5, unit='p', start_with_lorem=True):
    """
    Generates Lorem Ipsum placeholder text.

    Args:
        count (int): The number of units to generate.
        unit (str): 'p' for paragraphs, 's' for sentences, 'w' for words.
        start_with_lorem (bool): Whether to force starting with 'Lorem ipsum...'

    Returns:
        str: The generated Lorem Ipsum text, or an empty string on error.
    """
    try:
        count = max(1, int(count))
        if unit not in ['p', 's', 'w']: unit = 'p'

        print(f"[Lorem Gen] Generating {count} unit(s) of type '{unit}', Start standard: {start_with_lorem}")

        # --- Revised Library Usage: Call in Loop ---
        text_parts = []
        if unit == 'p':
            for _ in range(count):
                # Call paragraph() repeatedly to get desired number
                text_parts.append(lorem.paragraph())
            text = "\n\n".join(text_parts) # Join with double newline

        elif unit == 's':
            # Generate enough paragraphs to likely contain enough sentences
            # Estimate ~5 sentences per paragraph on average? Adjust as needed.
            required_paragraphs = max(1, (count // 5) + 1)
            base_text = "\n\n".join([lorem.paragraph() for _ in range(required_paragraphs)])
            sentences = re.split(r'(?<=[.!?])\s+', base_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            text_parts = sentences[:count] # Take the required number
            text = " ".join(text_parts)
            if text and text[-1] not in '.!?': text += '.'

        elif unit == 'w':
            # Generate words one by one or in small chunks
            # This might be less efficient than the previous attempt if words() existed with count
            for _ in range(count):
                 # Call words(1) if it exists, otherwise generate single word text
                 try:
                     text_parts.append(lorem.words(1)) # Assuming words(1) works
                 except (AttributeError, TypeError):
                      # Fallback: generate a short sentence and take first word? Less ideal.
                      # Or just append 'lorem ' repeatedly?
                      text_parts.append(random.choice(['lorem', 'ipsum', 'dolor', 'sit', 'amet'])) # Very basic fallback
            text = " ".join(text_parts)

        else:
            text = ""

        # --- Handle Start Phrase (Same logic as before) ---
        if start_with_lorem and text and not text.lower().strip().startswith("lorem ipsum"):
            standard_start = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            if unit == 'p' and text_parts:
                 first_para_sentences = re.split(r'(?<=[.!?])\s+', text_parts[0], maxsplit=1)
                 if len(first_para_sentences) > 1: text_parts[0] = standard_start + first_para_sentences[1]
                 else: text_parts[0] = standard_start
                 text = "\n\n".join(text_parts)
            elif unit == 's' and text_parts:
                 text_parts[0] = standard_start
                 text = " ".join(text_parts)
            elif unit == 'w':
                 if count > 6:
                     if len(text_parts) >= 6: text = standard_start + " ".join(text_parts[6:])
                     else: text = standard_start + text
                 else: text = " ".join(standard_start.split()[:count])
            else: text = standard_start
        elif not start_with_lorem:
             pass # Return generated text as is


        print("[Lorem Gen] Generation complete.")
        return text.strip()

    except Exception as e:
        print(f"Error generating Lorem Ipsum: {e}")
        import traceback
        traceback.print_exc()
        return ""