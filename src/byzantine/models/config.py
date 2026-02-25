"""Configuration models for the Byzantine LLM network."""

from typing import List
from pydantic import BaseModel, Field, field_validator


class ByzantineModelsConfig(BaseModel):
    """Configuration for the LLM models in the Byzantine network."""
    node_models: List[str] = Field(..., min_length=1, description="List of LLM models for the N nodes")
    judge_model: str = Field(..., min_length=1, description="LLM model for the Judge")

    @field_validator("judge_model")
    @classmethod
    def not_empty_string(cls, v: str) -> str:
        """Validate that judge model is not empty."""
        if not v.strip():
            raise ValueError("Judge model string cannot be empty")
        return v.strip()
