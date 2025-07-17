# utility_tools/unit_converter_logic.py
from pint import UnitRegistry, DimensionalityError, UndefinedUnitError

# Initialize Unit Registry
# Use 'system=None' to avoid potential system-specific issues initially
# 'auto_reduce_dimensions=False' might be safer if handling complex units later
ureg = UnitRegistry(system=None, auto_reduce_dimensions=False)
# Allow redefining common units if needed, or handle abbreviations
# ureg.define('tonne = 1000 * kilogram = t')
# ureg.define('liter = dm**3 = l = L') # Pint often defines 'liter' already
# ureg.define('milliliter = cm**3 = ml = mL')

# Define categories and units we support (using Pint's expected names/symbols)
# Store them in a way that's easy to pass to the template
UNIT_CATEGORIES = {
    "Length": {
        "m": "Meter (m)",
        "km": "Kilometer (km)",
        "cm": "Centimeter (cm)",
        "mm": "Millimeter (mm)",
        "mi": "Mile (mi)",
        "yd": "Yard (yd)",
        "ft": "Foot (ft)",
        "inch": "Inch (in)",
    },
    "Mass": {
        "kg": "Kilogram (kg)",
        "g": "Gram (g)",
        "mg": "Milligram (mg)",
        "tonne": "Tonne (t)", # Use 'tonne' as defined by Pint or our definition
        "lb": "Pound (lb)",
        "oz": "Ounce (oz)",
    },
    "Temperature": {
        # Pint handles temperature scales correctly (delta vs absolute)
        "degC": "Celsius (°C)",
        "degF": "Fahrenheit (°F)",
        "K": "Kelvin (K)",
    },
    # Add more categories like Area, Volume, Speed later
}

# Flatten list for easier template iteration if needed, or keep nested
ALL_UNITS = {unit: name for category in UNIT_CATEGORIES.values() for unit, name in category.items()}

def convert_units(value_str, from_unit, to_unit):
    """
    Converts a value from one unit to another using Pint.

    Args:
        value_str (str): The input value as a string.
        from_unit (str): The unit symbol to convert from (e.g., 'm', 'kg', 'degC').
        to_unit (str): The unit symbol to convert to.

    Returns:
        tuple: (float: Converted value or None,
                str: Error message or None)
    """
    if not value_str:
        return None, "Please enter a value to convert."
    if not from_unit or not to_unit:
        return None, "Please select both 'From' and 'To' units."

    try:
        value = float(value_str) # Convert input string to float
    except ValueError:
        return None, "Invalid input value. Please enter a number."

    try:
        # Create a Pint Quantity object
        quantity = value * ureg(from_unit)
        print(f"[Unit Convert] Input Quantity: {quantity}")

        # Perform the conversion
        converted_quantity = quantity.to(ureg(to_unit))
        print(f"[Unit Convert] Converted Quantity: {converted_quantity}")

        # Return only the magnitude (the numerical value)
        return converted_quantity.magnitude, None

    except UndefinedUnitError as e:
        print(f"[Unit Convert] Error: Undefined Unit - {e}")
        return None, f"Invalid unit selected: '{e}'. Please check unit selections."
    except DimensionalityError as e:
        # This happens if trying to convert between incompatible dimensions (e.g., meters to kg)
        print(f"[Unit Convert] Error: Dimensionality Mismatch - {e}")
        return None, f"Cannot convert between '{from_unit}' and '{to_unit}'. Units measure different things (e.g., length vs. mass)."
    except Exception as e:
        print(f"Error during unit conversion: {e}")
        import traceback
        traceback.print_exc()
        return None, f"An unexpected error occurred during conversion: {e}"