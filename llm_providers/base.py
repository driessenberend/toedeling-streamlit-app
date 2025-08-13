from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    name: str

    @abstractmethod
    def classify(self, *, model: str, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        """Voer een chat-achtige classificatie uit en retourneer de ruwe string-respons."""
        raise NotImplementedError
