# utility_tools/uuid_generator_logic.py
import uuid

def generate_uuids(version=4, quantity=1, uppercase=False, remove_hyphens=False):
    """
    Generates a list of UUIDs based on specified options.

    Args:
        version (int): UUID version (1 or 4 supported).
        quantity (int): Number of UUIDs to generate.
        uppercase (bool): Output UUIDs in uppercase.
        remove_hyphens (bool): Remove hyphens from the output.

    Returns:
        list: A list of generated UUID strings, or None on error.
    """
    if version not in [1, 4]:
        print(f"[UUID Gen] Error: Unsupported version requested: {version}")
        return None # Only support v1 and v4 for now
    if quantity < 1 or quantity > 1000: # Set a reasonable upper limit
        print(f"[UUID Gen] Error: Invalid quantity requested: {quantity}")
        return None

    generated_list = []
    try:
        print(f"[UUID Gen] Generating {quantity} UUID(s) version {version}...")
        for _ in range(quantity):
            if version == 1:
                new_uuid = uuid.uuid1()
            else: # Default to v4
                new_uuid = uuid.uuid4()

            uuid_str = str(new_uuid)

            if remove_hyphens:
                uuid_str = uuid_str.replace('-', '')

            if uppercase:
                uuid_str = uuid_str.upper()

            generated_list.append(uuid_str)

        print(f"[UUID Gen] Generation complete. Generated {len(generated_list)} UUIDs.")
        return generated_list

    except Exception as e:
        print(f"Error generating UUIDs: {e}")
        import traceback
        traceback.print_exc()
        return None