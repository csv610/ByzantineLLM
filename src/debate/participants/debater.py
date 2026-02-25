"""Debater participant for debate platform."""

import logging
from typing import Dict, List, Optional, Tuple

from .base import Participant
from ..models.entities import GapAnalysis, ValidationResult, OpponentEvaluation

logger = logging.getLogger(__name__)


class Debater(Participant):
    """Presents arguments for or against the topic."""

    def __init__(self, name: str, model: str, is_supporter: bool):
        """
        Initialize debater.

        Args:
            name: Debater's name
            model: LLM model identifier
            is_supporter: True if supporting topic, False if opposing
        """
        super().__init__(name, model)
        self.is_supporter = is_supporter
        self.argument_history: List[Dict] = []
        self.opponent_argument_history: List[Dict] = []

    def get_role(self) -> str:
        """Return role."""
        return "supporter" if self.is_supporter else "opposer"

    def add_own_argument(self, argument: str, round_number: int) -> None:
        """
        Store own argument in history.

        Args:
            argument: The argument text
            round_number: Round number
        """
        self.argument_history.append({
            "round": round_number,
            "content": argument
        })

    def add_opponent_argument(self, argument: str, round_number: int) -> None:
        """
        Store opponent's argument in history.

        Args:
            argument: The opponent's argument text
            round_number: Round number
        """
        self.opponent_argument_history.append({
            "round": round_number,
            "content": argument
        })

    def generate_argument(
        self,
        topic: str,
        round_number: int,
        is_initial: bool = False,
        own_score: Optional[float] = None,
        opponent_score: Optional[float] = None
    ) -> str:
        """
        Generate an argument for the debate.

        Args:
            topic: The debate topic
            round_number: Current round number
            is_initial: True if initial argument, False if rebuttal
            own_score: Current score (if available)
            opponent_score: Opponent's current score (if available)

        Returns:
            Generated argument text
        """
        position = "supporting" if self.is_supporter else "opposing"

        if is_initial:
            task = f"Present your initial {position} argument for the topic. Introduce your main thesis and primary reasoning."
            history_context = ""
            score_context = ""
        else:
            own_args_summary = self._build_history_summary(
                self.argument_history,
                "Your previous arguments"
            )
            opponent_args_summary = self._build_history_summary(
                self.opponent_argument_history,
                "Opponent's arguments"
            )

            history_context = f"""
DEBATE HISTORY:

{own_args_summary}

{opponent_args_summary}

You must address the gaps and weaknesses in the opponent's position while introducing NEW INFORMATION and NEW ARGUMENTS not previously mentioned."""

            # Build score context for strategic adaptation
            score_context = ""
            if own_score is not None and opponent_score is not None:
                score_diff = own_score - opponent_score
                if score_diff > 1.5:
                    score_context = f"""
YOUR CURRENT POSITION:
- Your score: {own_score:.1f}/10 (Leading by {score_diff:.1f} points)
- Maintain your approach: strong evidence and citations are working well
- Continue presenting facts, studies, and irrefutable arguments"""
                elif score_diff < -1.5:
                    score_context = f"""
YOUR CURRENT POSITION:
- Your score: {own_score:.1f}/10 (Behind by {-score_diff:.1f} points)
- Critical: Increase use of citations, peer-reviewed research, and specific data
- Focus on evidence-backed arguments to close the gap
- Provide facts and verifiable sources for all major claims"""
                else:
                    score_context = f"""
YOUR CURRENT POSITION:
- Your score: {own_score:.1f}/10 (Close match with opponent at {opponent_score:.1f}/10)
- Strategy: Both sides are presenting compelling arguments
- Win by superior evidence: Use more citations, specific data, and research
- Improve on evidence quality - this will be decisive"""

            task = f"""Present your {position} rebuttal with NEW ARGUMENTS and NEW INFORMATION.
IMPORTANT: Do not repeat arguments you've already made. Focus on:
1. Addressing specific weaknesses in the opponent's latest arguments
2. Introducing completely new evidence, examples, or logical arguments
3. Building on previous points with deeper analysis
4. Challenging any new claims the opponent has introduced
5. STRENGTHEN YOUR EVIDENCE: The judge heavily weights factual claims and citations (40% of score)"""

        prompt = f"""You are a debate participant in an academic debate.

Topic: {topic}
Your position: {position} the topic
Round: {round_number}
Your role: {'Supporter' if self.is_supporter else 'Opposer'}
{history_context}
{score_context}

Task: {task}

Your response must:
1. Be clear, concise, and well-reasoned
2. Reference new evidence, studies, or logical arguments not mentioned before
3. Address specific points from opponent's most recent argument
4. Avoid repeating arguments from your previous rounds
5. Stay within 500 words
6. Use formal academic language
7. Be substantively different from all your previous arguments
8. MAXIMIZE CITATIONS AND EVIDENCE - Facts and citations determine winners

Response:"""

        logger.info(
            f"{self.name} generating {'initial' if is_initial else 'rebuttal'} argument for round {round_number}"
            f" (own_score={own_score}, opponent_score={opponent_score})"
        )
        response = self.generate_response(prompt, max_tokens=800)
        return response

    def _build_history_summary(self, history: List[Dict], label: str) -> str:
        """
        Build formatted summary of argument history.

        Args:
            history: List of argument dictionaries
            label: Label for the section

        Returns:
            Formatted summary string
        """
        if not history:
            return f"{label}: None yet"

        summary = f"\n{label}:\n"
        for entry in history:
            summary += f"\nRound {entry['round']}:\n{entry['content']}\n"
            summary += "---\n"

        return summary

    def analyze_opponent_arguments(self, topic: str, opponent_arguments: List[str]) -> List[str]:
        """
        Analyze opponent's arguments and identify gaps.

        Args:
            topic: The debate topic
            opponent_arguments: List of opponent's argument texts

        Returns:
            List of identified gaps (max 5)
        """
        if not opponent_arguments:
            return []

        opponent_text = "\n".join([
            f"Round {i+1}:\n{arg}\n"
            for i, arg in enumerate(opponent_arguments)
        ])

        prompt = f"""You are a critical debate analyst. Analyze the opponent's most recent argument(s) below and identify specific gaps, logical fallacies, unsupported claims, and inconsistencies.

Topic: {topic}
Your position: {'supporting' if self.is_supporter else 'opposing'} the topic

OPPONENT'S ARGUMENTS (latest to earliest):
{opponent_text}

Identify NEW gaps not previously mentioned. Do not repeat criticisms from earlier rounds.

Provide a JSON response with the following structure:
{{
    "gaps": ["gap1 (NEW)", "gap2 (NEW)", ...],
    "inconsistencies": ["inconsistency1 (NEW)", ...],
    "logical_fallacies": ["fallacy1 (NEW)", ...],
    "unsupported_claims": ["claim1 (NEW)", ...]
}}

Focus only on the latest argument's new weaknesses. Response:"""

        logger.debug(f"{self.name} analyzing opponent arguments")
        response = self.generate_response(prompt, max_tokens=800, response_format=GapAnalysis)

        try:
            cleaned_response = self._clean_json_response(response)
            analysis = GapAnalysis.model_validate_json(cleaned_response)
            return analysis.all_weaknesses()[:5]
        except Exception as e:
            logger.warning(f"Failed to parse gap analysis for {self.name}: {str(e)}")
            return []

    def validate_argument_quality(self, topic: str, current_argument: str) -> Tuple[bool, str]:
        """
        Validate if argument provides new information AND/OR refutes opponent.

        Argument is valid if it:
        - Introduces new evidence, examples, or logical arguments, OR
        - Specifically refutes opponent's claims with evidence

        Returns:
            Tuple of (is_valid, reason)
            - is_valid: True if argument meets substantive criteria
            - reason: Explanation of validation result
        """
        if not current_argument:
            return False, "Argument is empty"

        if len(current_argument.split()) < 50:
            return False, "Argument is too short (< 50 words)"

        prompt = f"""You are a debate quality validator. Analyze if this argument provides substantive value.

Topic: {topic}
Your position: {'supporting' if self.is_supporter else 'opposing'} the topic

ARGUMENT TO VALIDATE:
{current_argument}

PREVIOUS ARGUMENTS BY YOU:
{self._build_history_summary(self.argument_history, "Your previous arguments")}

Evaluate the argument on these criteria:
1. NOVELTY: Does it introduce NEW evidence, examples, or logical arguments NOT already presented?
2. REFUTATION: Does it SPECIFICALLY ADDRESS and REFUTE opponent's latest claims with evidence?
3. REPETITION: Does it avoid merely repeating your own previous points?

The argument is VALID if it satisfies BOTH novelty AND refutation, or at least has strong novelty.
The argument is INVALID if it has neither new information nor opponent refutation.

Return JSON:
{{
    "has_new_information": true/false,
    "has_strong_novelty": true/false,
    "refutes_opponent": true/false,
    "avoids_repetition": true/false,
    "is_substantive": true/false,
    "reason": "<brief explanation of why valid or invalid>",
    "missing_elements": ["element1", "element2"]
}}

Be objective and strict. Response:"""

        try:
            response = self.generate_response(prompt, max_tokens=500, response_format=ValidationResult)
            cleaned_response = self._clean_json_response(response)
            validation = ValidationResult.model_validate_json(cleaned_response)

            # Argument is valid if:
            # - Has strong novelty OR
            # - Successfully refutes opponent AND has some new info OR
            # - Has new info that's not repetitive
            is_substantive = (
                validation.has_strong_novelty or
                (validation.refutes_opponent and validation.has_new_information) or
                (validation.has_new_information and validation.avoids_repetition)
            )

            logger.info(f"{self.name} argument validation: {is_substantive} - {validation.reason}")
            return is_substantive, validation.reason

        except Exception as e:
            logger.warning(f"Failed to parse validation for {self.name}: {str(e)}")
            return False, f"Validation parsing error: {str(e)}"

    def evaluate_opponent_argument(self, topic: str, opponent_argument: str) -> Tuple[List[str], List[str]]:
        """
        Evaluate opponent's argument for valid points and weaknesses.

        This is crucial for dynamic scoring - debaters can acknowledge valid opponent
        points (increasing opponent score) or identify weaknesses (decreasing opponent score).

        Args:
            topic: The debate topic
            opponent_argument: The opponent's latest argument

        Returns:
            Tuple of (acknowledged_valid_points, identified_weaknesses)
        """
        if not opponent_argument:
            return [], []

        prompt = f"""You are an objective debate evaluator. Analyze the opponent's argument below and provide a balanced assessment.

Topic: {topic}
Your position: {'supporting' if self.is_supporter else 'opposing'} the topic

OPPONENT'S ARGUMENT:
{opponent_argument}

Provide a JSON response identifying:
1. VALID POINTS: Strong, well-reasoned points in the opponent's argument that have merit
2. WEAKNESSES: Logical gaps, unsupported claims, errors, or inconsistencies

Be objective - even if you disagree, identify genuinely valid points. This improves debate quality.

{{
    "acknowledged_valid_points": [
        "Valid point 1: [explanation of why it's valid]",
        "Valid point 2: [explanation]",
        ...
    ],
    "identified_weaknesses": [
        "Weakness 1: [explanation of the flaw]",
        "Weakness 2: [explanation]",
        ...
    ]
}}

Response:"""

        logger.debug(f"{self.name} evaluating opponent argument for valid points and weaknesses")
        response = self.generate_response(prompt, max_tokens=800, response_format=OpponentEvaluation)

        try:
            cleaned_response = self._clean_json_response(response)
            eval_result = OpponentEvaluation.model_validate_json(cleaned_response)
            
            # Filter and limit
            valid_points = [p for p in eval_result.acknowledged_valid_points if p.strip()][:3]
            weaknesses = [w for w in eval_result.identified_weaknesses if w.strip()][:3]

            logger.info(f"{self.name} found {len(valid_points)} valid points and {len(weaknesses)} weaknesses")
            return valid_points, weaknesses
        except Exception as e:
            logger.warning(f"Failed to parse evaluation for {self.name}: {str(e)}")
            return [], []
