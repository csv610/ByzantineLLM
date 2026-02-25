"""Data entity models for ranking-based Byzantine Consensus."""

import logging
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Proposal(BaseModel):
    """Represents a node's answer to the common question."""
    participant_name: str
    participant_role: str  # "consensus_node", "byzantine_node"
    content: str
    timestamp: str
    word_count: int

    def __str__(self) -> str:
        return f"{self.participant_name}: {self.content[:100]}..."


class NodeEvaluation(BaseModel):
    """A node's evaluation and ranking of all participants."""
    evaluator_name: str
    rankings: List[str]  # List of participant names from best to worst
    evaluations: Dict[str, str]  # participant_name -> feedback/justification


class ConsensusResult(BaseModel):
    """Final result including the N x N ranking matrix."""
    topic: str
    proposals: List[Proposal]
    ranking_matrix: Dict[str, List[str]]  # evaluator_name -> ranked_list
    final_scores: Dict[str, float]  # aggregated score/rank for each node
    winner: str
    final_response: str  # The Judge's final response based on winners
    timestamp: str
    participants: Dict[str, str]
