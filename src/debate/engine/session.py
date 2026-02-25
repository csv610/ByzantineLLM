"""Debate session orchestrator."""

import logging
from datetime import datetime
from typing import List, Optional

from ..models import DebateConfig, Argument, Score, DebateTermination, DebateResult
from ..participants import Organizer, Debater, Judge

logger = logging.getLogger(__name__)


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
            Winner role (supporter/opposer) or None if tie
        """
        if len(scores) < 2:
            return None

        scores_sorted = sorted(scores, key=lambda s: s.overall_score, reverse=True)

        if scores_sorted[0].overall_score > scores_sorted[1].overall_score:
            return scores_sorted[0].debater_role
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
