"""Node participant for decentralized consensus."""

import logging
from typing import Dict, List, Optional
import json

from .base import Participant
from ..models.entities import NodeEvaluation

logger = logging.getLogger(__name__)


class Node(Participant):
    """Generates answers and ranks all participants' responses independently."""

    def __init__(self, name: str, model: str):
        super().__init__(name, model)
        self.proposal_history: List[str] = []

    def get_role(self) -> str:
        return "consensus_node"

    def add_own_proposal(self, content: str, round_number: int) -> None:
        self.proposal_history.append(content)

    def generate_proposal(self, topic: str, **kwargs) -> str:
        """Step 2: Generate answer to the question."""
        prompt = f"""You are a participant in an objective consensus session.
Question: {topic}

Task: Provide a high-quality, comprehensive answer to the question above.
Your response will be evaluated by all other participants and a final Judge.

Response:"""
        logger.info(f"{self.name} generating proposal...")
        return self.generate_response(prompt, max_tokens=1000)

    def rank_proposals(self, topic: str, all_proposals: Dict[str, str]) -> NodeEvaluation:
        """Step 3: Evaluate and rank ALL N responses anonymously."""
        proposals_text = ""
        for name, content in all_proposals.items():
            proposals_text += f"\nPARTICIPANT: {name}\nRESPONSE:\n{content}\n{'-'*40}\n"

        prompt = f"""You are an independent evaluator in a blind consensus session.
Question: {topic}

Evaluation Criteria:
1. Factual Accuracy
2. Completeness
3. Logical Reasoning
4. Clarity and Structure

Below are responses from N anonymous participants (including yourself).
{proposals_text}

Task:
1. Objectively evaluate each response based on the criteria.
2. Rank the participants from BEST to WORST.
3. Provide brief feedback for each to justify your ranking.

Return ONLY a valid JSON object with this structure:
{{
    "rankings": ["Name of Best", "Name of Second Best", ...],
    "evaluations": {{
        "Participant Name": "Brief feedback..."
    }}
}}
"""
        logger.info(f"{self.name} ranking all proposals independently...")
        response = self.generate_response(prompt, max_tokens=1500, temperature=0.1)
        
        try:
            cleaned = response.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            
            data = json.loads(cleaned)
            return NodeEvaluation(
                evaluator_name=self.name,
                rankings=data["rankings"],
                evaluations=data["evaluations"]
            )
        except Exception as e:
            logger.error(f"Failed to parse ranking from {self.name}: {e}")
            names = list(all_proposals.keys())
            return NodeEvaluation(
                evaluator_name=self.name,
                rankings=names,
                evaluations={n: "Error parsing ranking" for n in names}
            )
