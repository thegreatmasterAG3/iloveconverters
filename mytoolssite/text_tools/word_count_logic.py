# text_tools/word_count_logic.py
import re

def calculate_text_stats(text):
    """
    Calculates various statistics for a given block of text.

    Args:
        text (str): The input text string.

    Returns:
        dict: A dictionary containing counts for words, characters (with/without spaces),
              sentences, and paragraphs, or None if input is empty/invalid.
    """
    if not text or not isinstance(text, str):
        return None

    text = text.strip() # Remove leading/trailing whitespace
    if not text:
        return {
            'word_count': 0,
            'char_count_spaces': 0,
            'char_count_no_spaces': 0,
            'sentence_count': 0,
            'paragraph_count': 0,
        }

    # Word Count: Split by whitespace
    words = text.split()
    word_count = len(words)

    # Character Count (with spaces)
    char_count_spaces = len(text)

    # Character Count (without spaces)
    char_count_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\r", ""))

    # Sentence Count (Approximate: counts '.', '!', '?')
    # This is a basic approximation and might not be perfect for all cases (e.g., Mr. Smith)
    # Using regex to find sentence-ending punctuation followed by space or end of string
    sentences = re.split(r'[.!?]\s+', text)
    # Filter out empty strings that might result from multiple terminators
    sentence_count = len([s for s in sentences if s.strip()])
    # Handle case where text might not end with punctuation
    if sentence_count == 0 and len(text) > 0:
        sentence_count = 1

    # Paragraph Count (Approximate: counts double line breaks or more)
    # Normalize line breaks first (replace \r\n with \n)
    normalized_text = text.replace('\r\n', '\n')
    # Split by two or more newlines, filter empty paragraphs
    paragraphs = re.split(r'\n{2,}', normalized_text)
    paragraph_count = len([p for p in paragraphs if p.strip()])
    # Handle case of single paragraph with no double line breaks
    if paragraph_count == 0 and len(text) > 0:
        paragraph_count = 1


    return {
        'word_count': word_count,
        'char_count_spaces': char_count_spaces,
        'char_count_no_spaces': char_count_no_spaces,
        'sentence_count': sentence_count,
        'paragraph_count': paragraph_count,
    }