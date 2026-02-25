"""Configuration and data models for consensus."""

from .config import ConsensusConfig, ByzantineModelsConfig
from .entities import (
    Proposal, 
    ConsensusResult,
    NodeEvaluation
)

__all__ = [
    "ConsensusConfig",
    "ByzantineModelsConfig",
    "Proposal",
    "ConsensusResult",
    "NodeEvaluation",
]
