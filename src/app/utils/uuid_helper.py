"""UUID generation utilities."""

import uuid


def generate_uuid() -> str:
    """Generate a new UUID v4 string.

    Returns:
        str: UUID v4 as a hexadecimal string.
    """
    return str(uuid.uuid4())
