from __future__ import annotations

import os
from typing import Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

from .base import LLMClient


class OpenAIClient(LLMClient):
    name = "openai"

    def __init__(self, api_key: Optional[str] = None):
        # Leest sleutel uit argument of uit omgevingsvariabele/Streamlit secrets
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def classify(self, *, model: str, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        if OpenAI is None:
            raise RuntimeError("openai-package niet geïnstalleerd. Voeg 'openai' toe aan requirements.txt")
        if not (self.api_key or os.getenv("OPENAI_API_KEY")):
            raise RuntimeError("Geen OpenAI API key gevonden. Stel OPENAI_API_KEY in via Streamlit secrets of env.")

        client = OpenAI(api_key=self.api_key)
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content or ""
