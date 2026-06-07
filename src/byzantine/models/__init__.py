"""Configuration and data models for consensus."""

from .config import ByzantineModelsConfig
from .entities import (
    Proposal,
    ConsensusResult,
    NodeEvaluation,
)

__all__ = [
    "ByzantineModelsConfig",
    "Proposal",
    "ConsensusResult",
    "NodeEvaluation",
]
