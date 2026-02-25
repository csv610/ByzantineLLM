"""Core engine for ByzantineLLM."""

from .byzantine_llm import ByzantineLLM
from .prompts import PromptBuilder

__all__ = ["ByzantineLLM", "PromptBuilder"]
