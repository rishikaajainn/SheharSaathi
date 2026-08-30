import json
import re


class AIResponseParseError(Exception):
    """Raised when an AI response cannot be parsed as JSON."""


def parse_json_response(response_text: str) -> dict:
    """
    Parse a Gemini response into a JSON object.

    Handles:
    - normal JSON
    - JSON wrapped in markdown fences
    - accidental text before/after JSON
    """

    if not response_text:
        raise AIResponseParseError(
            "AI returned an empty response."
        )

    text = response_text.strip()

    # Remove markdown code fences if Gemini adds them.
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    text = text.strip()

    # First attempt: response is already valid JSON.
    try:
        data = json.loads(text)

        if not isinstance(data, dict):
            raise AIResponseParseError(
                "AI response must be a JSON object."
            )

        return data

    except json.JSONDecodeError:
        pass

    # Second attempt: find the outermost JSON object.
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise AIResponseParseError(
            "No JSON object found in AI response."
        )

    json_text = text[start:end + 1]

    try:
        data = json.loads(json_text)

    except json.JSONDecodeError as e:
        raise AIResponseParseError(
            "AI returned invalid JSON."
        ) from e

    if not isinstance(data, dict):
        raise AIResponseParseError(
            "AI response must be a JSON object."
        )

    return data