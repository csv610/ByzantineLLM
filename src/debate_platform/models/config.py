"""Configuration models for debate sessions."""

from dataclasses import dataclass, asdict
from typing import Dict, Tuple


@dataclass
class DebateConfig:
    """Configuration for a debate session."""
    topic: str                          # The debate topic
    organizer_name: str                 # Name of organizer
    organizer_model: str                # LLM model for organizer
    supporter_name: str                 # Name of supporter
    supporter_model: str                # LLM model for supporter
    opposer_name: str                   # Name of opposer
    opposer_model: str                  # LLM model for opposer
    judge_name: str                     # Name of judge
    judge_model: str                    # LLM model for judge
    num_rounds: int = 3                 # Number of debate rounds (1-10)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    def validate(self) -> Tuple[bool, str]:
        """
        Validate configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.topic or not self.topic.strip():
            return False, "Topic cannot be empty"

        if self.num_rounds < 1 or self.num_rounds > 10:
            return False, "Number of rounds must be between 1 and 10"

        for name in [self.organizer_name, self.supporter_name, self.opposer_name, self.judge_name]:
            if not name or not name.strip():
                return False, "All participant names must be provided"

        for model in [self.organizer_model, self.supporter_model, self.opposer_model, self.judge_model]:
            if not model or not model.strip():
                return False, "All participant models must be specified"

        return True, "Configuration is valid"
