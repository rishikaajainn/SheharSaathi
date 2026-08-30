import os

import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")

model = None

if api_key:
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash"
    )


class AIServiceError(Exception):
    """Raised when Gemini cannot generate a response."""


def is_ai_available() -> bool:
    """
    Returns True when Gemini is configured.
    """
    return model is not None


def generate_response(prompt: str) -> str:
    """
    Send a prompt to Gemini and return the generated text.

    Raises AIServiceError when Gemini is unavailable
    or fails to generate a response.
    """

    if model is None:
        raise AIServiceError(
            "Gemini AI is not configured."
        )

    if not prompt or not prompt.strip():
        raise AIServiceError(
            "AI prompt cannot be empty."
        )

    try:
        response = model.generate_content(prompt)

        if not response:
            raise AIServiceError(
                "Gemini returned an empty response."
            )

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        raise AIServiceError(
            "Gemini returned no usable text."
        )

    except AIServiceError:
        raise

    except Exception as e:
        print(f"Gemini Error: {type(e).__name__}: {e}")

        raise AIServiceError(
            "Gemini failed to generate a response."
        ) from e