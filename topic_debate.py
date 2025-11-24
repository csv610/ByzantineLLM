"""
Core debate engine for multi-participant AI debates.

This module contains the core business logic for orchestrating debates between
multiple AI participants (Organizer, Debaters, Judge) using different LLM models
via litellm.

Classes:
    - Participant: Base class for all debate participants
    - Organizer: Provides neutral topic overview
    - Debater: Presents arguments for/against topic with history tracking
    - Judge: Evaluates and scores debate arguments
    - DebateSession: Orchestrates the complete debate flow
    - DebateResult: Data structure for debate outcomes

Example:
    >>> debate = DebateSession(
    ...     topic="AI will have net positive impact on jobs",
    ...     organizer=Organizer("Moderator", "gpt-4"),
    ...     supporter=Debater("Alice", "gpt-4", is_supporter=True),
    ...     opposer=Debater("Bob", "claude-3-opus-20240229", is_supporter=False),
    ...     judge=Judge("Judge Panel", "gpt-4")
    ... )
    >>> result = debate.run(num_rounds=3)
    >>> print(f"Winner: {result.winner}")
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
import logging

from litellm import completion

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class DebateConfig:
    """Configuration for a debate session."""
    topic: str                          # The debate topic
    organizer_model: str                # LLM model for organizer
    supporter_model: str                # LLM model for supporter
    opposer_model: str                  # LLM model for opposer
    judge_model: str                    # LLM model for judge
    num_rounds: int = 3                 # Number of debate rounds (1-10)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    def validate(self) -> Tuple[bool, str]:
        """
        Validate configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.topic or not self.topic.strip():
            return False, "Topic cannot be empty"

        if self.num_rounds < 1 or self.num_rounds > 10:
            return False, "Number of rounds must be between 1 and 10"

        for model in [self.organizer_model, self.supporter_model, self.opposer_model, self.judge_model]:
            if not model or not model.strip():
                return False, "All participant models must be specified"

        return True, "Configuration is valid"


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
    debater_role: str  # "supporter" or "opposer"
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
        return f"{self.debater_role}: {self.overall_score:.1f}/10 ({self.fact_count} facts, {self.irrefutable_arguments} backed arguments)"


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


# ============================================================================
# PARTICIPANT BASE CLASS
# ============================================================================

class Participant(ABC):
    """Base class for all debate participants."""

    def __init__(self, name: str, model: str):
        """
        Initialize participant.

        Args:
            name: Participant's display name
            model: LLM model identifier (e.g., 'gpt-4', 'claude-3-opus-20240229')
        """
        self.name = name
        self.model = model

    @abstractmethod
    def get_role(self) -> str:
        """Return participant's role."""
        pass

    def generate_response(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Generate response using litellm.

        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum tokens in response

        Returns:
            Generated response text

        Raises:
            Exception: If API call fails
        """
        try:
            logger.debug(f"Generating response for {self.name} using {self.model}")
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response for {self.name}: {str(e)}")
            raise

    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text."""
        return len(text.split())


# ============================================================================
# ORGANIZER CLASS
# ============================================================================

class Organizer(Participant):
    """Provides neutral overview of debate topic."""

    def get_role(self) -> str:
        """Return role."""
        return "organizer"

    def generate_overview(self, topic: str) -> str:
        """
        Generate neutral overview of the topic (200-300 words).

        Args:
            topic: The debate topic

        Returns:
            Neutral overview text
        """
        prompt = f"""You are a neutral debate organizer. Provide a comprehensive but neutral overview of the following topic in 200-300 words.

Topic: {topic}

Your overview should:
1. Explain the key aspects of the topic
2. Identify main arguments that could be made on both sides
3. Define any important terms or concepts
4. Present historical or current context if relevant
5. Remain completely neutral and unbiased

Overview:"""

        logger.info(f"{self.name} generating overview for topic: {topic[:50]}...")
        response = self.generate_response(prompt, max_tokens=500)
        return response


# ============================================================================
# DEBATER CLASS
# ============================================================================

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
        response = self.generate_response(prompt, max_tokens=800)

        try:
            analysis = json.loads(response)
            gaps = (
                analysis.get("gaps", []) +
                analysis.get("inconsistencies", []) +
                analysis.get("logical_fallacies", [])
            )
            gaps = [g for g in gaps if g.strip()]
            return gaps[:5]
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse gap analysis JSON for {self.name}")
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
            response = self.generate_response(prompt, max_tokens=500)
            validation = json.loads(response)

            has_new_info = validation.get("has_new_information", False)
            strong_novelty = validation.get("has_strong_novelty", False)
            refutes = validation.get("refutes_opponent", False)
            avoids_rep = validation.get("avoids_repetition", True)

            # Argument is valid if:
            # - Has strong novelty OR
            # - Successfully refutes opponent AND has some new info OR
            # - Has new info that's not repetitive
            is_substantive = (
                strong_novelty or
                (refutes and has_new_info) or
                (has_new_info and avoids_rep)
            )

            reason = validation.get("reason", "Validation failed")

            logger.info(f"{self.name} argument validation: {is_substantive} - {reason}")
            return is_substantive, reason

        except json.JSONDecodeError:
            logger.warning(f"Failed to parse validation JSON for {self.name}")
            return False, "Validation parsing error"

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
        response = self.generate_response(prompt, max_tokens=800)

        try:
            analysis = json.loads(response)
            valid_points = analysis.get("acknowledged_valid_points", [])
            weaknesses = analysis.get("identified_weaknesses", [])

            # Filter and limit
            valid_points = [p for p in valid_points if p.strip()][:3]
            weaknesses = [w for w in weaknesses if w.strip()][:3]

            logger.info(f"{self.name} found {len(valid_points)} valid points and {len(weaknesses)} weaknesses")
            return valid_points, weaknesses
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse evaluation JSON for {self.name}")
            return [], []


# ============================================================================
# JUDGE CLASS
# ============================================================================

class Judge(Participant):
    """Evaluates and scores debate arguments."""

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

                for other_arg in self.arguments:
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


# ============================================================================
# DEBATE SESSION
# ============================================================================

class DebateSession:
    """Orchestrates the complete debate flow."""

    def __init__(
        self,
        topic: str,
        organizer: Organizer,
        supporter: Debater,
        opposer: Debater,
        judge: Judge
    ):
        """
        Initialize debate session.

        Args:
            topic: The debate topic
            organizer: Organizer participant
            supporter: Supporting debater
            opposer: Opposing debater
            judge: Judge participant
        """
        self.topic = topic
        self.organizer = organizer
        self.supporter = supporter
        self.opposer = opposer
        self.judge = judge
        self.arguments: List[Argument] = []

    @classmethod
    def from_config(cls, config: DebateConfig) -> "DebateSession":
        """
        Create a DebateSession from a DebateConfig object.

        Args:
            config: DebateConfig object with all debate settings

        Returns:
            DebateSession instance ready to run

        Raises:
            ValueError: If configuration is invalid
        """
        is_valid, error_msg = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid debate configuration: {error_msg}")

        organizer = Organizer("Organizer", config.organizer_model)
        supporter = Debater("Supporter", config.supporter_model, is_supporter=True)
        opposer = Debater("Opposer", config.opposer_model, is_supporter=False)
        judge = Judge("Judge", config.judge_model)

        logger.info(f"Created DebateSession from config: {config.topic}")
        return cls(
            topic=config.topic,
            organizer=organizer,
            supporter=supporter,
            opposer=opposer,
            judge=judge
        )

    def run(self, num_rounds: int) -> DebateResult:
        """
        Run the complete debate.

        Args:
            num_rounds: Number of debate rounds

        Returns:
            DebateResult containing all arguments and scores
        """
        logger.info(f"Starting debate on '{self.topic}' with {num_rounds} rounds")

        # Round 0: Organizer overview
        self._run_organizer_round()

        # Rounds 1-N: Debate rounds
        termination = None
        for round_num in range(1, num_rounds + 1):
            termination = self._run_debate_round(round_num)
            if termination and termination.terminated:
                logger.info(f"Debate terminated: {termination.reason}")
                break

        # Final: Judge evaluation
        scores = self._run_judge_evaluation()

        # Determine winner
        winner = self._determine_winner(scores)

        # Create termination record if not set
        if not termination:
            termination = DebateTermination(
                terminated=False,
                reason="completed",
                round_number=num_rounds,
                message="Debate completed successfully"
            )

        result = DebateResult(
            topic=self.topic,
            arguments=self.arguments,
            scores=scores,
            winner=winner,
            timestamp=datetime.now().isoformat(),
            num_rounds=len(self.arguments) - 1,  # Excluding organizer round
            participants={
                self.organizer.name: self.organizer.get_role(),
                self.supporter.name: self.supporter.get_role(),
                self.opposer.name: self.opposer.get_role(),
                self.judge.name: self.judge.get_role()
            },
            termination=termination
        )

        logger.info(f"Debate completed. Winner: {winner}. Termination: {termination.reason}")
        return result

    def _run_organizer_round(self) -> None:
        """Run organizer's overview round."""
        logger.debug("Running organizer round")

        overview = self.organizer.generate_overview(self.topic)

        arg = Argument(
            round_number=0,
            participant_name=self.organizer.name,
            participant_role="organizer",
            content=overview,
            timestamp=datetime.now().isoformat(),
            word_count=self.organizer.count_words(overview)
        )
        self.arguments.append(arg)

    def _run_debate_round(self, round_num: int) -> Optional[DebateTermination]:
        """
        Run a single debate round with both debaters.

        Returns:
            DebateTermination if debate should stop, None otherwise
        """
        logger.debug(f"Running debate round {round_num}")

        is_initial = (round_num == 1)

        # Calculate intermediate scores if not initial round
        supporter_score = None
        opposer_score = None
        if not is_initial and round_num > 1:
            try:
                intermediate_scores = self.judge.score_debate(self.topic, self.arguments)
                for score in intermediate_scores:
                    if score.debater_name == self.supporter.name:
                        supporter_score = score.overall_score
                    elif score.debater_name == self.opposer.name:
                        opposer_score = score.overall_score
                logger.info(f"Intermediate scores - {self.supporter.name}: {supporter_score:.1f}, {self.opposer.name}: {opposer_score:.1f}")
            except Exception as e:
                logger.warning(f"Could not calculate intermediate scores: {str(e)}")

        # Supporter's turn
        if is_initial:
            supporter_arg = self.supporter.generate_argument(
                self.topic,
                round_num,
                is_initial=True
            )
        else:
            gaps = self.supporter.analyze_opponent_arguments(
                self.topic,
                [arg.content for arg in self.arguments if arg.participant_name == self.opposer.name]
            )
            supporter_arg = self.supporter.generate_argument(
                self.topic,
                round_num,
                is_initial=False,
                own_score=supporter_score,
                opponent_score=opposer_score
            )

        # Validate supporter's argument quality
        if not is_initial:
            is_valid, validation_reason = self.supporter.validate_argument_quality(self.topic, supporter_arg)
            if not is_valid:
                logger.warning(f"Supporter argument validation failed: {validation_reason}")
                return DebateTermination(
                    terminated=True,
                    reason="low_quality",
                    round_number=round_num,
                    debater_name=self.supporter.name,
                    message=validation_reason
                )

        # Store supporter's argument
        self.supporter.add_own_argument(supporter_arg, round_num)
        self.opposer.add_opponent_argument(supporter_arg, round_num)

        # Evaluate opponent's latest argument (if not initial)
        acknowledged_valid = None
        identified_weak = None
        if not is_initial and self.arguments:
            opponent_latest = [arg for arg in self.arguments if arg.participant_name == self.opposer.name]
            if opponent_latest:
                acknowledged_valid, identified_weak = self.supporter.evaluate_opponent_argument(
                    self.topic,
                    opponent_latest[-1].content
                )

        supporter_arg_obj = Argument(
            round_number=round_num,
            participant_name=self.supporter.name,
            participant_role="supporter",
            content=supporter_arg,
            timestamp=datetime.now().isoformat(),
            word_count=self.supporter.count_words(supporter_arg),
            gaps_identified=self.supporter.analyze_opponent_arguments(
                self.topic,
                [arg.content for arg in self.arguments if arg.participant_name == self.opposer.name]
            ) if not is_initial else None,
            acknowledged_valid_points=acknowledged_valid,
            identified_weaknesses=identified_weak
        )
        self.arguments.append(supporter_arg_obj)

        # Opposer's turn
        if is_initial:
            opposer_arg = self.opposer.generate_argument(
                self.topic,
                round_num,
                is_initial=True
            )
        else:
            gaps = self.opposer.analyze_opponent_arguments(
                self.topic,
                [arg.content for arg in self.arguments if arg.participant_name == self.supporter.name]
            )
            opposer_arg = self.opposer.generate_argument(
                self.topic,
                round_num,
                is_initial=False,
                own_score=opposer_score,
                opponent_score=supporter_score
            )

        # Validate opposer's argument quality
        if not is_initial:
            is_valid, validation_reason = self.opposer.validate_argument_quality(self.topic, opposer_arg)
            if not is_valid:
                logger.warning(f"Opposer argument validation failed: {validation_reason}")
                return DebateTermination(
                    terminated=True,
                    reason="low_quality",
                    round_number=round_num,
                    debater_name=self.opposer.name,
                    message=validation_reason
                )

        # Store opposer's argument
        self.opposer.add_own_argument(opposer_arg, round_num)
        self.supporter.add_opponent_argument(opposer_arg, round_num)

        # Evaluate opponent's latest argument (if not initial)
        acknowledged_valid_opp = None
        identified_weak_opp = None
        if not is_initial:
            supporter_latest = [arg for arg in self.arguments if arg.participant_name == self.supporter.name]
            if supporter_latest:
                acknowledged_valid_opp, identified_weak_opp = self.opposer.evaluate_opponent_argument(
                    self.topic,
                    supporter_latest[-1].content
                )

        opposer_arg_obj = Argument(
            round_number=round_num,
            participant_name=self.opposer.name,
            participant_role="opposer",
            content=opposer_arg,
            timestamp=datetime.now().isoformat(),
            word_count=self.opposer.count_words(opposer_arg),
            gaps_identified=self.opposer.analyze_opponent_arguments(
                self.topic,
                [arg.content for arg in self.arguments if arg.participant_name == self.supporter.name]
            ) if not is_initial else None,
            acknowledged_valid_points=acknowledged_valid_opp,
            identified_weaknesses=identified_weak_opp
        )
        self.arguments.append(opposer_arg_obj)

        # Debate continues - no termination
        return None

    def _run_judge_evaluation(self) -> List[Score]:
        """
        Run judge evaluation.

        Returns:
            List of scores
        """
        logger.debug("Running judge evaluation")
        return self.judge.score_debate(self.topic, self.arguments)

    def _determine_winner(self, scores: List[Score]) -> Optional[str]:
        """
        Determine debate winner based on scores.

        Args:
            scores: List of scores

        Returns:
            Winner name or None if tie
        """
        if len(scores) < 2:
            return None

        scores_sorted = sorted(scores, key=lambda s: s.overall_score, reverse=True)

        if scores_sorted[0].overall_score > scores_sorted[1].overall_score:
            return scores_sorted[0].debater_name
        else:
            return None  # Tie

    def get_arguments_by_participant(self, participant_name: str) -> List[Argument]:
        """
        Get all arguments by a specific participant.

        Args:
            participant_name: Name of participant

        Returns:
            List of arguments
        """
        return [arg for arg in self.arguments if arg.participant_name == participant_name]

    def get_arguments_by_role(self, role: str) -> List[Argument]:
        """
        Get all arguments by a specific role.

        Args:
            role: Role name (organizer, supporter, opposer)

        Returns:
            List of arguments
        """
        return [arg for arg in self.arguments if arg.participant_role == role]

    def get_round_arguments(self, round_num: int) -> List[Argument]:
        """
        Get all arguments from a specific round.

        Args:
            round_num: Round number

        Returns:
            List of arguments
        """
        return [arg for arg in self.arguments if arg.round_number == round_num]
