# utility_tools/timezone_converter_logic.py
from datetime import datetime, time
# Use standard library zoneinfo (requires Python 3.9+)
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones
# Removed pytz specific errors

def get_available_timezones():
    """Returns a sorted list of available IANA timezone names."""
    return sorted(list(available_timezones()))

def convert_timezone(input_dt_str, source_tz_str, target_tz_str):
    """
    Converts a datetime string from a source timezone to a target timezone using zoneinfo.

    Args:
        input_dt_str (str): Datetime string in 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD HH:MM:SS' format.
        source_tz_str (str): IANA timezone name (e.g., 'America/New_York').
        target_tz_str (str): IANA timezone name (e.g., 'Europe/London').

    Returns:
        tuple: (datetime: Converted datetime object or None,
                str: Formatted output string or None,
                str: Error message or None)
    """
    if not all([input_dt_str, source_tz_str, target_tz_str]):
        return None, None, "Missing input data, source timezone, or target timezone."

    try:
        # --- Parsing Input ---
        naive_dt = None
        supported_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
        for fmt in supported_formats:
            try:
                naive_dt = datetime.strptime(input_dt_str, fmt)
                break # Stop if parsing successful
            except ValueError:
                continue # Try next format
        if naive_dt is None:
             return None, None, f"Invalid date/time format. Use one of: {', '.join(supported_formats)}"

        # --- Timezone Handling (zoneinfo) ---
        try:
            source_tz = ZoneInfo(source_tz_str)
        except ZoneInfoNotFoundError: # Specific error for invalid key
            return None, None, f"Invalid source timezone key: '{source_tz_str}'"
        except Exception as e: # Catch other potential init errors
            print(f"Error initializing source ZoneInfo: {e}")
            return None, None, f"Invalid source timezone: '{source_tz_str}'"
        try:
            target_tz = ZoneInfo(target_tz_str)
        except ZoneInfoNotFoundError:
             return None, None, f"Invalid target timezone key: '{target_tz_str}'"
        except Exception as e:
             print(f"Error initializing target ZoneInfo: {e}")
             return None, None, f"Invalid target timezone: '{target_tz_str}'"


        # --- Make datetime timezone-aware using zoneinfo ---
        # Replace the naive datetime's tzinfo.
        # zoneinfo handles DST automatically based on the naive time *and* the fold attribute (defaults to 0)
        # For ambiguous or non-existent times, datetime operations might raise exceptions later,
        # or you can handle the 'fold' attribute more explicitly if needed.
        # See: https://docs.python.org/3/library/datetime.html#datetime.datetime.replace
        try:
            source_dt_aware = naive_dt.replace(tzinfo=source_tz)
            print(f"  Aware source DT created: {source_dt_aware}")
        except Exception as replace_err: # Catch potential errors during replace (less common)
            print(f"Timezone assignment error: {replace_err}")
            # This might relate to ambiguous/non-existent times for certain tzinfo operations,
            # although replace() itself is usually safe. The error might show up in conversion.
            return None, None, f"Error processing time for {source_tz_str}. Check for DST issues."

        # --- Conversion ---
        # astimezone automatically handles DST rules based on the aware source time
        target_dt_aware = source_dt_aware.astimezone(target_tz)
        print(f"  Converted DT: {target_dt_aware}")

        # --- Formatting Output ---
        # Get UTC offset string including DST if applicable
        offset_str = target_dt_aware.strftime('%Z %z') # Use standard format codes (e.g., EST -0500)

        # Create a more detailed format string
        formatted_output = target_dt_aware.strftime(f"%A, %B %d, %Y %I:%M:%S %p ({target_tz_str} / {offset_str})")

        print(f"[TZ Convert] {input_dt_str} ({source_tz_str}) -> {formatted_output}")
        return target_dt_aware, formatted_output, None # Success

    # Catch specific errors if needed (e.g., from astimezone on invalid times)
    except ValueError as ve: # Might catch errors from invalid date/time components during conversion
        print(f"ValueError during conversion: {ve}")
        return None, None, f"Could not convert the specified time, potentially due to DST transitions or invalid date components: {ve}"
    except Exception as e:
        print(f"Error during timezone conversion: {e}")
        import traceback
        traceback.print_exc()
        return None, None, f"An unexpected error occurred: {e}"