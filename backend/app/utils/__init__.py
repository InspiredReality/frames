"""Utility functions."""


def inches_to_cm(inches):
    """Convert inches to centimeters."""
    return inches * 2.54


def cm_to_inches(cm):
    """Convert centimeters to inches."""
    return cm / 2.54


def validate_dimensions(width, height, min_val=0.1, max_val=500):
    """
    Validate dimension values are within acceptable range.

    Args:
        width: Width value
        height: Height value
        min_val: Minimum acceptable value
        max_val: Maximum acceptable value

    Returns:
        Tuple of (is_valid, error_message)
    """
    if width is None or height is None:
        return False, "Width and height are required"

    try:
        width = float(width)
        height = float(height)
    except (TypeError, ValueError):
        return False, "Width and height must be numbers"

    if width < min_val or height < min_val:
        return False, f"Dimensions must be at least {min_val}"

    if width > max_val or height > max_val:
        return False, f"Dimensions must not exceed {max_val}"

    return True, None
