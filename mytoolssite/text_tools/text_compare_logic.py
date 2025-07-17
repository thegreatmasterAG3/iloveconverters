# text_tools/text_compare_logic.py
import difflib
import re

def generate_side_by_side_diff(text_a, text_b, ignore_whitespace=False, ignore_case=False):
    """
    Generates data structure for a side-by-side HTML diff view.

    Args:
        text_a (str): The first text input.
        text_b (str): The second text input.
        ignore_whitespace (bool): Ignore changes only in whitespace.
        ignore_case (bool): Perform case-insensitive comparison.

    Returns:
        list: A list of tuples, where each tuple represents a row:
              (line_num_a, line_text_a, line_num_b, line_text_b, change_type)
              change_type can be 'equal', 'replace', 'delete', 'insert', 'empty'
              line_text_a/b contain HTML with <ins>/<del> tags for word diffs.
        Or None if inputs are invalid.
    """
    if text_a is None or text_b is None:
        return None

    # Normalize line endings and split into lines
    a_lines = text_a.replace('\r\n', '\n').splitlines()
    b_lines = text_b.replace('\r\n', '\n').splitlines()

    # Apply options
    if ignore_case:
        a_lines_cmp = [line.lower() for line in a_lines]
        b_lines_cmp = [line.lower() for line in b_lines]
    else:
        a_lines_cmp = a_lines
        b_lines_cmp = b_lines

    if ignore_whitespace:
        # Collapse multiple whitespace chars and strip ends for comparison
        whitespace_regex = re.compile(r'\s+')
        a_lines_cmp = [whitespace_regex.sub(' ', line).strip() for line in a_lines_cmp]
        b_lines_cmp = [whitespace_regex.sub(' ', line).strip() for line in b_lines_cmp]

    # Use difflib's SequenceMatcher
    # We use the comparison lines for finding matches, but display original lines
    diff_matcher = difflib.SequenceMatcher(None, a_lines_cmp, b_lines_cmp)
    diff_result = []
    line_num_a = 1
    line_num_b = 1

    for tag, i1, i2, j1, j2 in diff_matcher.get_opcodes():
        # --- Helper to highlight word differences within a line pair ---
        def highlight_word_diffs(line1, line2):
            highlighted1 = []
            highlighted2 = []
            # Prepare words for comparison based on options
            words1_cmp = line1.lower() if ignore_case else line1
            words2_cmp = line2.lower() if ignore_case else line2
            if ignore_whitespace:
                 words1_cmp = whitespace_regex.sub(' ', words1_cmp).strip()
                 words2_cmp = whitespace_regex.sub(' ', words2_cmp).strip()

            # Use SequenceMatcher on words within the line
            word_matcher = difflib.SequenceMatcher(None, words1_cmp.split(), words2_cmp.split())
            # Get original words to display
            original_words1 = line1.split()
            original_words2 = line2.split()
            # Track original word indices
            idx1, idx2 = 0, 0

            for word_tag, w_i1, w_i2, w_j1, w_j2 in word_matcher.get_opcodes():
                if word_tag == 'equal':
                    highlighted1.extend(original_words1[idx1:idx1 + (w_i2 - w_i1)])
                    highlighted2.extend(original_words2[idx2:idx2 + (w_j2 - w_j1)])
                    idx1 += (w_i2 - w_i1)
                    idx2 += (w_j2 - w_j1)
                else: # replace, delete, insert
                    if w_i1 != w_i2: # If words exist in A
                        highlighted1.append('<del>')
                        highlighted1.extend(original_words1[idx1:idx1 + (w_i2 - w_i1)])
                        highlighted1.append('</del>')
                        idx1 += (w_i2 - w_i1)
                    if w_j1 != w_j2: # If words exist in B
                        highlighted2.append('<ins>')
                        highlighted2.extend(original_words2[idx2:idx2 + (w_j2 - w_j1)])
                        highlighted2.append('</ins>')
                        idx2 += (w_j2 - w_j1)

            # Handle potential trailing whitespace differences if not ignoring whitespace
            if not ignore_whitespace:
                 if line1.endswith(' ') and not line2.endswith(' '): highlighted1.append(' ')
                 if line2.endswith(' ') and not line1.endswith(' '): highlighted2.append(' ')

            return " ".join(highlighted1), " ".join(highlighted2)
        # --- End helper ---

        if tag == 'equal':
            for i in range(i1, i2):
                diff_result.append((line_num_a, a_lines[i], line_num_b, b_lines[j1 + (i - i1)], 'equal'))
                line_num_a += 1
                line_num_b += 1
        elif tag == 'replace':
             len_a = i2 - i1
             len_b = j2 - j1
             max_len = max(len_a, len_b)
             for k in range(max_len):
                 text_a, text_b = "", ""
                 num_a, num_b = None, None
                 if k < len_a:
                     text_a = a_lines[i1 + k]
                     num_a = line_num_a
                     line_num_a += 1
                 if k < len_b:
                     text_b = b_lines[j1 + k]
                     num_b = line_num_b
                     line_num_b +=1

                 # Highlight word differences if both lines exist in this step
                 if text_a and text_b:
                      text_a_h, text_b_h = highlight_word_diffs(text_a, text_b)
                      diff_result.append((num_a, text_a_h, num_b, text_b_h, 'replace'))
                 elif text_a: # Only text A exists (like delete in this step)
                      diff_result.append((num_a, f"<del>{text_a}</del>", num_b, text_b, 'replace')) # Mark whole line deleted
                 elif text_b: # Only text B exists (like insert in this step)
                      diff_result.append((num_a, text_a, num_b, f"<ins>{text_b}</ins>", 'replace')) # Mark whole line inserted

        elif tag == 'delete':
            for i in range(i1, i2):
                diff_result.append((line_num_a, f"<del>{a_lines[i]}</del>", None, '', 'delete')) # Mark whole line deleted
                line_num_a += 1
        elif tag == 'insert':
            for j in range(j1, j2):
                 diff_result.append((None, '', line_num_b, f"<ins>{b_lines[j]}</ins>", 'insert')) # Mark whole line inserted
                 line_num_b += 1

    return diff_result