"""Base participant class for consensus platform."""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from litellm import completion

logger = logging.getLogger(__name__)


class Participant(ABC):
    """Base class for all consensus participants."""

    def __init__(self, name: str, model: str):
        """
        Initialize participant.

        Args:
            name: Participant's display name
            model: LLM model identifier
        """
        self.name = name
        self.model = model

    @abstractmethod
    def get_role(self) -> str:
        """Return participant's role."""
        pass

    def generate_response(self, prompt: str, max_tokens: int = 1000, response_format: type = None, temperature: float = 0.7) -> str:
        """Simple response generation with user prompt only."""
        return self.generate_response_with_system(None, prompt, max_tokens, response_format, temperature)

    def generate_response_with_system(
        self, 
        system_prompt: Optional[str], 
        user_prompt: str, 
        max_tokens: int = 1000, 
        response_format: type = None, 
        temperature: float = 0.7
    ) -> str:
        """
        Generate response using litellm with optional system prompt.
        """
        try:
            logger.debug(f"Generating response for {self.name} using {self.model}")
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            if response_format:
                try:
                    kwargs["response_format"] = response_format
                    response = completion(**kwargs)
                except Exception as e:
                    if "UnsupportedParamsError" in str(e) or "response_format" in str(e):
                        logger.warning(f"Model {self.model} does not support response_format. Falling back to text.")
                    else:
                        raise e
            else:
                response = completion(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response for {self.name}: {str(e)}")
            raise

    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text."""
        return len(text.split())
