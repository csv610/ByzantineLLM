"""Base participant class for debate platform."""

import logging
from abc import ABC, abstractmethod

from litellm import completion

logger = logging.getLogger(__name__)


class Participant(ABC):
    """Base class for all debate participants."""

    def __init__(self, name: str, model: str):
        """
        Initialize participant.

        Args:
            name: Participant's display name
            model: LLM model identifier (e.g., 'gpt-4', 'claude-3-opus-20240229')
        """
        self.name = name
        self.model = model

    @abstractmethod
    def get_role(self) -> str:
        """Return participant's role."""
        pass

    def generate_response(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Generate response using litellm.

        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum tokens in response

        Returns:
            Generated response text

        Raises:
            Exception: If API call fails
        """
        try:
            logger.debug(f"Generating response for {self.name} using {self.model}")
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response for {self.name}: {str(e)}")
            raise

    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text."""
        return len(text.split())
