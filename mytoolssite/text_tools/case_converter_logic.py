# text_tools/case_converter_logic.py
import re
import titlecase # Requires: pip install titlecase

def convert_case(text, case_type='lower'):
    """
    Converts the case of the input text based on the specified type.

    Args:
        text (str): The input text.
        case_type (str): 'upper', 'lower', 'sentence', 'title'.

    Returns:
        str: The text converted to the specified case.
    """
    if not text or not isinstance(text, str):
        return ""

    text = text.strip() # Start with trimmed text

    try:
        if case_type == 'upper':
            return text.upper()
        elif case_type == 'lower':
            return text.lower()
        elif case_type == 'sentence':
            # Capitalize the first letter of each sentence.
            # Split into sentences (basic split on ., !, ?)
            # This is a simple approach, more robust sentence tokenization exists.
            sentences = re.split(r'(?<=[.!?])\s+', text) # Split after terminator + space
            processed_sentences = []
            for sentence in sentences:
                if sentence:
                    # Capitalize first letter, lowercase rest (of the first part)
                    processed_sentences.append(sentence[0].upper() + sentence[1:].lower())
            # Rejoin, trying to preserve original spacing pattern somewhat
            # Find original terminators + spacing
            terminators = re.findall(r'[.!?]\s+', text)
            # Interleave sentences and terminators
            output = ""
            num_parts = min(len(processed_sentences), len(terminators))
            for i in range(num_parts):
                output += processed_sentences[i] + terminators[i]
            # Add any remaining sentence part (if text didn't end with punctuation)
            if len(processed_sentences) > len(terminators):
                output += processed_sentences[-1]
            # If no sentences were found but text exists, capitalize first letter
            elif not output and text:
                 output = text[0].upper() + text[1:].lower()
            return output

        elif case_type == 'title':
            # Use the titlecase library for better handling of small words etc.
            return titlecase.titlecase(text)

        # Add other cases like 'alternate', 'inverse' here if needed later

        else: # Default or unknown type, return lowercase
            return text.lower()

    except Exception as e:
        print(f"Error during case conversion (type: {case_type}): {e}")
        return text # Return original text on error