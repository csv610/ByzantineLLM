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

    def generate_response(self, prompt: str, max_tokens: int = 1000, response_format: type = None) -> str:
        """
        Generate response using litellm.

        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum tokens in response
            response_format: Optional Pydantic model class for structured output

        Returns:
            Generated response text (JSON string if response_format is provided)

        Raises:
            Exception: If API call fails
        """
        try:
            logger.debug(f"Generating response for {self.name} using {self.model}")
            
            kwargs = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            if response_format:
                kwargs["response_format"] = response_format

            response = completion(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response for {self.name}: {str(e)}")
            raise

    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text."""
        return len(text.split())

    @staticmethod
    def _clean_json_response(text: str) -> str:
        """
        Clean LLM response by removing markdown code blocks.
        
        Args:
            text: Raw response from LLM
            
        Returns:
            Cleaned JSON string
        """
        text = text.strip()
        if text.startswith("```"):
            # Remove opening block (e.g., ```json or ```)
            lines = text.splitlines()
            if len(lines) > 2:
                # Find the first line after the opening ```
                # and the last line before the closing ```
                start_idx = 1
                end_idx = len(lines) - 1
                while end_idx > start_idx and not lines[end_idx].strip().startswith("```"):
                    end_idx -= 1
                
                content = "\n".join(lines[start_idx:end_idx])
                return content.strip()
        
        # If it contains ``` anywhere, try to extract content between them
        if "```" in text:
            import re
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                return match.group(1).strip()
                
        return text
