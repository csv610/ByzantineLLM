"""Judge for blind Byzantine Consensus."""

import logging
from typing import List, Dict
import json

from .base import Participant
from ..models.entities import NodeEvaluation

logger = logging.getLogger(__name__)


class Judge(Participant):
    """The Judge who analyzes the blind NxN matrix to discover the verified consensus."""

    def get_role(self) -> str:
        return "judge"

    def determine_verdict(self, topic: str, all_proposals: Dict[str, str], all_rankings: Dict[str, NodeEvaluation]) -> Dict:
        """
        Step 5: Evaluate the anonymous NxN table.
        Step 6: Write the response of the winners.
        """
        
        matrix_text = "EVALUATOR | RANKINGS (Best -> Worst)\n"
        matrix_text += "----------|------------------------\n"
        for evaluator, eval_obj in all_rankings.items():
            matrix_text += f"{evaluator} | {', '.join(eval_obj.rankings)}\n"

        justifications = ""
        for evaluator, eval_obj in all_rankings.items():
            justifications += f"\nEvaluations from {evaluator}:\n"
            for target, feedback in eval_obj.evaluations.items():
                justifications += f"- {target}: {feedback}\n"

        prompt = f"""You are the Judge in a Blind Byzantine Consensus session.
Question: {topic}

THE NxN RANKING TABLE (Anonymous):
{matrix_text}

DETAILED FEEDBACK FROM PARTICIPANTS:
{justifications}

Your Role:
You have no prior knowledge of which nodes are honest or adversarial. You must treat all data as potentially Byzantine.
Your goal is to find the "Ground Truth" by analyzing the agreement matrix and the quality of justifications.

Task:
1. Identify the consensus winner(s) based on the aggregate rankings.
2. Detect "Byzantine" behavior: Look for outliers in the ranking table (e.g., participants who rank generally accepted "best" answers very low, or who promote low-quality answers).
3. Determine the final aggregate ranking of the participants.
4. Based on the content of the highest-ranked winner, write the FINAL, authoritative answer to the original question.

Return ONLY a valid JSON object with this structure:
{{
    "final_ranking": ["Winner Name", "Runner Up", ...],
    "byzantine_detection": "Analysis of any detected adversarial or inconsistent behavior.",
    "final_response": "The authoritative response based on the winner's content."
}}
"""
        logger.info("Judge is analyzing the blind NxN matrix for Byzantine behavior...")
        response = self.generate_response(prompt, max_tokens=3000, temperature=0.1)
        
        try:
            cleaned = response.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            data = json.loads(cleaned)
            return data
        except Exception as e:
            logger.error(f"Judge failed to generate JSON verdict: {e}")
            return {
                "final_ranking": list(all_proposals.keys()),
                "byzantine_detection": "Error parsing verdict.",
                "final_response": "The judge failed to reach a structured conclusion."
            }
