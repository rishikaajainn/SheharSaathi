from typing import Any


def get_list(
    data: dict,
    key: str,
) -> list:
    """
    Safely retrieve a list from an AI response.
    """

    value = data.get(key, [])

    return value if isinstance(value, list) else []


def get_string(
    data: dict,
    key: str,
    default: str = "",
) -> str:
    """
    Safely retrieve a string from an AI response.
    """

    value = data.get(key, default)

    return value if isinstance(value, str) else default


def get_number(
    data: dict,
    key: str,
    default: float = 0,
) -> float:
    """
    Safely retrieve a numeric value from an AI response.
    """

    value: Any = data.get(key, default)

    if isinstance(value, (int, float)):
        return value

    return default