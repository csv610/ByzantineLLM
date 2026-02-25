"""Configuration models for decentralized Byzantine Consensus."""

from typing import Dict, List
from pydantic import BaseModel, Field, field_validator


class ConsensusConfig(BaseModel):
    """Configuration for a Byzantine Consensus session."""
    topic: str = Field(..., min_length=1, description="The consensus topic/question")
    node_models: List[str] = Field(..., min_length=1, description="List of LLM models for the N nodes")
    judge_model: str = Field(..., min_length=1, description="LLM model for the Judge")
    system_prompt: str = Field(
        default="You are a participant in an objective consensus session. Provide a high-quality, comprehensive, and factual answer.",
        description="Override the default system prompt for all nodes"
    )
    user_prompt_template: str = Field(
        default="{topic}",
        description="Template for the user prompt. Must include {topic} placeholder."
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for all nodes (0.0 to 2.0)"
    )

    @field_validator("topic", "judge_model")
    @classmethod
    def not_empty_string(cls, v: str) -> str:
        """Validate that strings are not just whitespace."""
        if not v.strip():
            raise ValueError("String cannot be empty or only whitespace")
        return v.strip()

    @field_validator("user_prompt_template")
    @classmethod
    def contains_topic_placeholder(cls, v: str) -> str:
        """Validate that the user prompt template contains the {topic} placeholder."""
        if "{topic}" not in v:
            raise ValueError("user_prompt_template must contain the '{topic}' placeholder")
        return v

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return self.model_dump()
