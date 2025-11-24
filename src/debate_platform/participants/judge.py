"""Judge participant for debate platform."""

import json
import logging
from typing import List

from .base import Participant
from ..models.entities import Argument, Score

logger = logging.getLogger(__name__)


class Judge(Participant):
    """Evaluates and scores debate arguments."""

    def __init__(self, name: str, model: str):
        """
        Initialize judge.

        Args:
            name: Judge's name
            model: LLM model identifier
        """
        super().__init__(name, model)
        self.arguments: List[Argument] = []

    def get_role(self) -> str:
        """Return role."""
        return "judge"

    def score_debate(self, topic: str, arguments: List[Argument]) -> List[Score]:
        """
        Score all arguments and provide feedback.

        Scoring includes:
        1. Base scoring on 4 criteria
        2. Bonus for acknowledged valid opponent points
        3. Penalty for identified weaknesses in opponent's arguments

        Args:
            topic: The debate topic
            arguments: List of all arguments in the debate

        Returns:
            List of Score objects for each debater
        """
        scores = []
        debater_arguments = {}

        # Group arguments by role (supporter/opposer)
        for arg in arguments:
            if arg.participant_role in ["supporter", "opposer"]:
                if arg.participant_role not in debater_arguments:
                    debater_arguments[arg.participant_role] = []
                debater_arguments[arg.participant_role].append(arg)

        # Score each debater
        for debater_role, arguments_list in debater_arguments.items():
            arguments_text = "\n".join([
                f"Round {arg.round_number}:\n{arg.content}"
                for arg in arguments_list
            ])

            prompt = f"""You are an expert debate judge evaluating arguments in an academic debate.

Topic: {topic}
Debater Role: {debater_role}

DEBATER'S ARGUMENTS:
{arguments_text}

Evaluate this debater's performance on the following criteria (each 0-10):

1. EVIDENCE QUALITY (0-10) - CRITICAL FACTOR:
   - Count and analyze citations, specific references, and factual claims
   - Award high scores for: peer-reviewed studies, well-known statements, established research, specific data
   - Award low scores for: unsupported claims, vague generalizations, logical leaps without evidence
   - This is weighted most heavily in scoring

2. Argument Quality (0-10):
   - Clarity, structure, logical flow, and persuasiveness
   - How well ideas are presented and organized
   - Coherence and comprehensiveness

3. Logical Consistency (0-10):
   - Consistency across all arguments presented
   - Avoidance of contradictions and logical fallacies
   - Sound reasoning and deduction

4. Responsiveness to Gaps (0-10):
   - How well opponent's points are directly addressed
   - Specific rebuttals to opponent's claims
   - Filling logical gaps identified by opponent

SCORING METHODOLOGY:
- Maximum points go to debaters with most irrefutable arguments backed by facts
- References to well-known statements, research, and citations boost scores
- Unsubstantiated claims lower scores significantly
- Calculate overall_score as: (evidence_quality × 0.4) + (argument_quality × 0.2) + (logical_consistency × 0.2) + (responsiveness_to_gaps × 0.2)

Provide a JSON response with the following structure:
{{
    "argument_quality": <number 0-10>,
    "evidence_quality": <number 0-10>,
    "logical_consistency": <number 0-10>,
    "responsiveness_to_gaps": <number 0-10>,
    "overall_score": <number 0-10>,
    "fact_count": <number of citations/facts found>,
    "irrefutable_arguments": <count of arguments supported by evidence>,
    "feedback": "<detailed feedback focusing on facts and evidence>"
}}

Response:"""

            logger.info(f"{self.name} scoring {debater_role}")
            response = self.generate_response(prompt, max_tokens=500)

            try:
                score_data = json.loads(response)
                overall_score = score_data.get("overall_score", 0)

                # Apply score adjustments based on debate dynamics
                # Count valid points acknowledged in other debater's arguments
                valid_points_acknowledged = 0
                weaknesses_identified = 0

                # Get the opponent role
                opponent_role = "opposer" if debater_role == "supporter" else "supporter"

                for other_arg in arguments:
                    if other_arg.participant_role == opponent_role:
                        # Count how many times THIS debater was acknowledged as valid
                        if other_arg.acknowledged_valid_points:
                            valid_points_acknowledged += len(other_arg.acknowledged_valid_points)
                        # Count weaknesses identified IN THIS DEBATER'S arguments
                        if other_arg.identified_weaknesses:
                            weaknesses_identified += len(other_arg.identified_weaknesses)

                # Apply adjustments
                bonus = valid_points_acknowledged * 0.15  # +0.15 per valid point acknowledged
                penalty = weaknesses_identified * 0.10  # -0.10 per weakness identified

                adjusted_score = min(10.0, max(0.0, overall_score + bonus - penalty))

                logger.info(
                    f"{debater_role}: base={overall_score:.1f}, bonus={bonus:.1f}, penalty={penalty:.1f}, final={adjusted_score:.1f}"
                )

                feedback = score_data.get("feedback", "")
                if bonus > 0 or penalty > 0:
                    feedback += f"\n\nDYNAMIC SCORING ADJUSTMENTS:"
                    if valid_points_acknowledged > 0:
                        feedback += f"\n+ Opponent acknowledged {valid_points_acknowledged} valid point(s) in your argument: +{bonus:.1f} points"
                    if weaknesses_identified > 0:
                        feedback += f"\n- Opponent identified {weaknesses_identified} weakness/weaknesses in your argument: -{penalty:.1f} points"

                scores.append(Score(
                    debater_role=debater_role,
                    argument_quality=score_data.get("argument_quality", 0),
                    evidence_quality=score_data.get("evidence_quality", 0),
                    logical_consistency=score_data.get("logical_consistency", 0),
                    responsiveness_to_gaps=score_data.get("responsiveness_to_gaps", 0),
                    overall_score=adjusted_score,
                    feedback=feedback,
                    fact_count=score_data.get("fact_count", 0),
                    irrefutable_arguments=score_data.get("irrefutable_arguments", 0)
                ))
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse judge response for {debater_role}")
                scores.append(Score(
                    debater_role=debater_role,
                    argument_quality=0,
                    evidence_quality=0,
                    logical_consistency=0,
                    responsiveness_to_gaps=0,
                    overall_score=0,
                    feedback="Error parsing response",
                    fact_count=0,
                    irrefutable_arguments=0
                ))

        return scores
