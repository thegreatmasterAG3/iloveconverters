# utility_tools/color_converter_logic.py
import re
import math

def parse_color_string(color_str):
    """ Attempts to parse various color string formats into RGBA values (0-255 for RGB, 0-1 for A). """
    color_str = color_str.strip().lower()
    r, g, b, a = None, None, None, 1.0 # Default alpha to 1

    # Try HEX (#RRGGBB, #RGB, RRGGBB, RGB)
    hex_match = re.match(r'^#?([a-f0-9]{6})$', color_str)
    if hex_match:
        hex_val = hex_match.group(1)
        r = int(hex_val[0:2], 16)
        g = int(hex_val[2:4], 16)
        b = int(hex_val[4:6], 16)
        print(f"[Color Parse] Parsed HEX (#RRGGBB): ({r},{g},{b})")
        return r, g, b, a

    hex_match_short = re.match(r'^#?([a-f0-9]{3})$', color_str)
    if hex_match_short:
        hex_val = hex_match_short.group(1)
        r = int(hex_val[0] * 2, 16)
        g = int(hex_val[1] * 2, 16)
        b = int(hex_val[2] * 2, 16)
        print(f"[Color Parse] Parsed HEX (#RGB): ({r},{g},{b})")
        return r, g, b, a

    # Try RGB (rgb(r, g, b))
    rgb_match = re.match(r'^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$', color_str)
    if rgb_match:
        try:
            r = int(rgb_match.group(1))
            g = int(rgb_match.group(2))
            b = int(rgb_match.group(3))
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                print(f"[Color Parse] Parsed RGB: ({r},{g},{b})")
                return r, g, b, a
        except ValueError: pass # Ignore if conversion fails

    # Try RGBA (rgba(r, g, b, a)) - alpha can be 0-1 or 0-100%
    rgba_match = re.match(r'^rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*([0-9.]+%?)\s*\)$', color_str)
    if rgba_match:
        try:
            r = int(rgba_match.group(1))
            g = int(rgba_match.group(2))
            b = int(rgba_match.group(3))
            a_str = rgba_match.group(4)

            if a_str.endswith('%'):
                a = float(a_str.rstrip('%')) / 100.0
            else:
                a = float(a_str)

            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255 and 0 <= a <= 1:
                print(f"[Color Parse] Parsed RGBA: ({r},{g},{b},{a})")
                return r, g, b, a
        except ValueError: pass # Ignore conversion errors

    # HSL/HSLA parsing could be added here later

    print(f"[Color Parse] Failed to parse color string: {color_str}")
    return None, None, None, None # Failed to parse


def rgb_to_hsl(r, g, b):
    """ Converts RGB (0-255) to HSL (H: 0-360, S: 0-100%, L: 0-100%). """
    r /= 255.0
    g /= 255.0
    b /= 255.0
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2.0

    if max_c == min_c:
        h = s = 0 # achromatic
    else:
        d = max_c - min_c
        s = d / (2.0 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
        if max_c == r:
            h = (g - b) / d + (6.0 if g < b else 0.0)
        elif max_c == g:
            h = (b - r) / d + 2.0
        else: # max_c == b
            h = (r - g) / d + 4.0
        h /= 6.0

    h = round(h * 360)
    s = round(s * 100)
    l = round(l * 100)
    return h, s, l

def format_color_outputs(r, g, b, a):
    """ Formats RGBA values into various string representations. """
    if r is None: return None # Parsing failed

    outputs = {}

    # HEX (#RRGGBB) - Ignore alpha for standard hex
    outputs['hex'] = f"#{r:02x}{g:02x}{b:02x}"

    # RGB / RGBA string
    rgb_str = f"rgb({r}, {g}, {b})"
    rgba_str = f"rgba({r}, {g}, {b}, {a:.2f})".rstrip('0').rstrip('.') # Format alpha nicely
    outputs['rgb'] = rgb_str if a == 1.0 else rgba_str # Show RGB if alpha is 1

    # HSL / HSLA string
    h, s, l = rgb_to_hsl(r, g, b)
    hsl_str = f"hsl({h}, {s}%, {l}%)"
    hsla_str = f"hsla({h}, {s}%, {l}%, {a:.2f})".rstrip('0').rstrip('.')
    outputs['hsl'] = hsl_str if a == 1.0 else hsla_str

    # Also return raw RGBA for preview
    outputs['rgba_tuple'] = (r, g, b, a)

    return outputs