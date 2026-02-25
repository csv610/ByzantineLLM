"""Configuration and data models for consensus."""

from .config import ConsensusConfig
from .entities import (
    Proposal, 
    ConsensusResult,
    NodeEvaluation
)

__all__ = [
    "ConsensusConfig",
    "Proposal",
    "ConsensusResult",
    "NodeEvaluation",
]
