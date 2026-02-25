"""Configuration models for decentralized Byzantine Consensus."""

from typing import Dict, List
from pydantic import BaseModel, Field, field_validator


class ConsensusConfig(BaseModel):
    """Configuration for a Byzantine Consensus session."""
    topic: str = Field(..., min_length=1, description="The consensus topic/question")
    node_models: List[str] = Field(..., min_length=1, description="List of LLM models for the N nodes")
    judge_model: str = Field(..., min_length=1, description="LLM model for the Judge")

    @field_validator("topic", "judge_model")
    @classmethod
    def not_empty_string(cls, v: str) -> str:
        """Validate that strings are not just whitespace."""
        if not v.strip():
            raise ValueError("String cannot be empty or only whitespace")
        return v.strip()

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return self.model_dump()
