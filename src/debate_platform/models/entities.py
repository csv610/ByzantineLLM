"""Data entity models for debate arguments, scores, and results."""

import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class Argument:
    """Represents a single argument in the debate."""
    round_number: int
    participant_name: str
    participant_role: str  # "organizer", "supporter", "opposer"
    content: str
    timestamp: str
    word_count: int
    gaps_identified: Optional[List[str]] = None
    acknowledged_valid_points: Optional[List[str]] = None  # Valid opponent points acknowledged
    identified_weaknesses: Optional[List[str]] = None  # Weaknesses found in opponent's argument

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.participant_name} (Round {self.round_number}): {self.content[:100]}..."


@dataclass
class Score:
    """Score breakdown for a single debater."""
    debater_name: str
    argument_quality: float
    evidence_quality: float
    logical_consistency: float
    responsiveness_to_gaps: float
    overall_score: float
    feedback: str
    fact_count: int = 0  # Number of facts/citations used
    irrefutable_arguments: int = 0  # Number of evidence-backed arguments

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.debater_name}: {self.overall_score:.1f}/10 ({self.fact_count} facts, {self.irrefutable_arguments} backed arguments)"


@dataclass
class DebateTermination:
    """Reason for debate termination."""
    terminated: bool
    reason: str  # "completed", "low_quality", "no_new_info", "no_refutation", "max_rounds"
    round_number: int
    debater_name: Optional[str] = None  # Who failed to meet standards
    message: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    def __str__(self) -> str:
        """String representation."""
        return f"Debate {'terminated' if self.terminated else 'completed'}: {self.reason} at Round {self.round_number}"


@dataclass
class DebateResult:
    """Complete result of a debate session."""
    topic: str
    arguments: List[Argument]
    scores: List[Score]
    winner: Optional[str]
    timestamp: str
    num_rounds: int
    participants: Dict[str, str]  # {name: role}
    termination: Optional[DebateTermination] = None  # Why debate ended

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "topic": self.topic,
            "arguments": [arg.to_dict() for arg in self.arguments],
            "scores": [score.to_dict() for score in self.scores],
            "winner": self.winner,
            "timestamp": self.timestamp,
            "num_rounds": self.num_rounds,
            "participants": self.participants,
            "termination": self.termination.to_dict() if self.termination else None
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, filepath: str) -> None:
        """Save debate result to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
        logger.info(f"Debate result saved to {filepath}")

    @staticmethod
    def load(filepath: str) -> 'DebateResult':
        """Load debate result from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        arguments = [Argument(**arg) for arg in data['arguments']]
        scores = [Score(**score) for score in data['scores']]

        return DebateResult(
            topic=data['topic'],
            arguments=arguments,
            scores=scores,
            winner=data['winner'],
            timestamp=data['timestamp'],
            num_rounds=data['num_rounds'],
            participants=data['participants']
        )
