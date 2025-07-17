# utility_tools/timestamp_logic.py
import time
from datetime import datetime, timezone, timedelta

# Define standard formats
UTC_FORMAT = "%Y-%m-%d %H:%M:%S %Z%z" # Good standard format including timezone
INPUT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S" # Format we expect for date string input

def convert_timestamp(input_value, unit='s'):
    """
    Converts a Unix timestamp (seconds/ms) to dates or a date string to timestamp.

    Args:
        input_value (str): The user input (timestamp number or date string).
        unit (str): 's' for seconds, 'ms' for milliseconds (applies if input is timestamp).

    Returns:
        dict: Results including timestamp, utc_date, error, or None if input invalid.
    """
    input_value = input_value.strip()
    if not input_value:
        return {'error': 'Input cannot be empty.'}

    result = {'input_value': input_value, 'input_unit': unit} # Store input for context

    try:
        # --- Try interpreting as a Timestamp first ---
        timestamp_float = float(input_value)

        # Adjust based on unit
        if unit == 'ms':
            timestamp_seconds = timestamp_float / 1000.0
        # Add 'us' (microseconds) later if needed
        # elif unit == 'us':
        #     timestamp_seconds = timestamp_float / 1000000.0
        else: # Default to seconds
            timestamp_seconds = timestamp_float

        # Basic validation for plausible timestamp range (e.g., not negative, not excessively large)
        # Arbitrary range check - adjust if needed
        if timestamp_seconds < 0 or timestamp_seconds > time.time() + (30 * 365 * 24 * 60 * 60): # Allow up to ~30 years in future
             raise ValueError("Timestamp value seems out of plausible range.")

        result['timestamp'] = int(timestamp_seconds) # Store integer timestamp

        # Convert timestamp to UTC datetime object
        dt_utc = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
        result['utc_date'] = dt_utc.strftime(UTC_FORMAT)

        # We will add local date via JavaScript in the template

        print(f"[Timestamp Convert] Input treated as timestamp ({unit}). Result: {result}")
        return result

    except ValueError:
        # --- Input wasn't a valid number, try parsing as Date String ---
        print(f"[Timestamp Convert] Input not a number, trying as date string: {input_value}")
        try:
            # Assume input string is in LOCAL TIME unless timezone specified
            # We parse WITHOUT timezone awareness first
            dt_naive = datetime.strptime(input_value, INPUT_DATE_FORMAT)

            # Convert naive datetime assumed to be local -> UTC timestamp
            # This is complex without knowing the *server's* local timezone setting
            # or using JS to get browser's timezone.
            # Safer approach: Assume input date string IS UTC for now for backend calculation
            # We will rely on JS to show the *browser's* local time based on the calculated timestamp.
            dt_aware_utc = dt_naive.replace(tzinfo=timezone.utc) # Assume input was UTC

            result['timestamp'] = int(dt_aware_utc.timestamp())
            result['utc_date'] = dt_aware_utc.strftime(UTC_FORMAT) # Already have UTC string

            print(f"[Timestamp Convert] Input treated as UTC date string. Result: {result}")
            return result

        except ValueError as date_parse_error:
             print(f"[Timestamp Convert] Failed to parse as date string ({INPUT_DATE_FORMAT}): {date_parse_error}")
             return {'error': f"Invalid input. Please enter a valid Unix timestamp (number) or a date string in YYYY-MM-DD HH:MM:SS format."}
        except Exception as e:
             print(f"[Timestamp Convert] Unknown error during date parsing: {e}")
             return {'error': "An unexpected error occurred during date parsing."}

    except Exception as e:
        print(f"Unexpected error during timestamp conversion: {e}")
        import traceback
        traceback.print_exc()
        return {'error': "An unexpected error occurred."}