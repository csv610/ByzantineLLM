import streamlit as st
from litellm import completion
from abc import ABC, abstractmethod
import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

st.set_page_config(layout="wide")

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Argument:
    """Represents a single argument in the debate."""
    round_number: int
    participant_name: str
    participant_role: str  # "organizer", "supporter", "opposer", "judge"
    content: str
    timestamp: str
    word_count: int
    gaps_identified: Optional[List[str]] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class Score:
    """Scoring breakdown for judge evaluation."""
    debater_name: str
    argument_quality: float  # 0-10
    evidence_quality: float  # 0-10
    logical_consistency: float  # 0-10
    responsiveness_to_gaps: float  # 0-10
    overall_score: float  # 0-10
    feedback: str


# ============================================================================
# PARTICIPANT CLASSES
# ============================================================================

class Participant(ABC):
    """Base class for debate participants."""

    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model

    @abstractmethod
    def get_role(self) -> str:
        pass

    def generate_response(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate response using litellm."""
        try:
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"Error with {self.name}: {str(e)}")
            return ""

    def count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())


class Organizer(Participant):
    """Organizer - provides neutral overview of the topic."""

    def get_role(self) -> str:
        return "organizer"

    def generate_overview(self, topic: str) -> str:
        """Generate neutral 200-300 word overview of the topic."""
        prompt = f"""You are a neutral debate organizer. Provide a comprehensive but neutral overview of the following topic in 200-300 words.

Topic: {topic}

Your overview should:
1. Explain the key aspects of the topic
2. Identify main arguments that could be made on both sides
3. Define any important terms or concepts
4. Present historical or current context if relevant
5. Remain completely neutral and unbiased

Overview:"""

        response = self.generate_response(prompt, max_tokens=500)
        return response


class Debater(Participant):
    """Debater - presents arguments for or against the topic."""

    def __init__(self, name: str, model: str, is_supporter: bool):
        super().__init__(name, model)
        self.is_supporter = is_supporter
        self.argument_history = []  # Track own arguments
        self.opponent_argument_history = []  # Track opponent's arguments

    def get_role(self) -> str:
        return "supporter" if self.is_supporter else "opposer"

    def add_own_argument(self, argument: str, round_number: int):
        """Store own argument in history."""
        self.argument_history.append({
            "round": round_number,
            "content": argument
        })

    def add_opponent_argument(self, argument: str, round_number: int):
        """Store opponent's argument in history."""
        self.opponent_argument_history.append({
            "round": round_number,
            "content": argument
        })

    def generate_argument(self, topic: str, round_number: int, is_initial: bool = False) -> str:
        """Generate an argument for the debate."""
        position = "supporting" if self.is_supporter else "opposing"

        if is_initial:
            task = f"Present your initial {position} argument for the topic. Introduce your main thesis and primary reasoning."
            history_context = ""
        else:
            # Build history context from previous rounds
            own_args_summary = self._build_history_summary(self.argument_history, "Your previous arguments")
            opponent_args_summary = self._build_history_summary(self.opponent_argument_history, f"Opponent's arguments")

            history_context = f"""
DEBATE HISTORY:

{own_args_summary}

{opponent_args_summary}

You must address the gaps and weaknesses in the opponent's position while introducing NEW INFORMATION and NEW ARGUMENTS not previously mentioned."""

            task = f"""Present your {position} rebuttal with NEW ARGUMENTS and NEW INFORMATION.
IMPORTANT: Do not repeat arguments you've already made. Focus on:
1. Addressing specific weaknesses in the opponent's latest arguments
2. Introducing completely new evidence, examples, or logical arguments
3. Building on previous points with deeper analysis
4. Challenging any new claims the opponent has introduced"""

        prompt = f"""You are a debate participant in an academic debate.

Topic: {topic}
Your position: {position} the topic
Round: {round_number}
Your role: {'Supporter' if self.is_supporter else 'Opposer'}
{history_context}

Task: {task}

Your response must:
1. Be clear, concise, and well-reasoned
2. Reference new evidence, studies, or logical arguments not mentioned before
3. Address specific points from opponent's most recent argument
4. Avoid repeating arguments from your previous rounds
5. Stay within 500 words
6. Use formal academic language
7. Be substantively different from all your previous arguments

Response:"""

        response = self.generate_response(prompt, max_tokens=800)
        return response

    def _build_history_summary(self, history: List[Dict], label: str) -> str:
        """Build a formatted summary of argument history."""
        if not history:
            return f"{label}: None yet"

        summary = f"\n{label}:\n"
        for entry in history:
            summary += f"\nRound {entry['round']}:\n{entry['content']}\n"
            summary += "---\n"

        return summary

    def analyze_opponent_arguments(self, topic: str, opponent_arguments: List[str]) -> List[str]:
        """Analyze opponent's arguments and identify gaps/inconsistencies."""
        if not opponent_arguments:
            return []

        opponent_text = "\n".join([f"Round {i+1}:\n{arg}\n" for i, arg in enumerate(opponent_arguments)])

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

        response = self.generate_response(prompt, max_tokens=800)

        try:
            analysis = json.loads(response)
            gaps = analysis.get("gaps", []) + analysis.get("inconsistencies", []) + analysis.get("logical_fallacies", [])
            # Filter out empty strings and return top 5 NEW gaps
            gaps = [g for g in gaps if g.strip()]
            return gaps[:5]
        except json.JSONDecodeError:
            return []


class Judge(Participant):
    """Judge - evaluates and scores the debate."""

    def get_role(self) -> str:
        return "judge"

    def score_debate(self, topic: str, arguments: List[Argument]) -> List[Score]:
        """Score all arguments and provide feedback."""
        scores = []
        debater_arguments = {}

        # Group arguments by debater
        for arg in arguments:
            if arg.participant_role in ["supporter", "opposer"]:
                if arg.participant_name not in debater_arguments:
                    debater_arguments[arg.participant_name] = []
                debater_arguments[arg.participant_name].append(arg)

        # Score each debater
        for debater_name, arguments_list in debater_arguments.items():
            arguments_text = "\n".join([f"Round {arg.round_number}:\n{arg.content}" for arg in arguments_list])

            prompt = f"""You are an expert debate judge evaluating arguments in an academic debate.

Topic: {topic}
Debater: {debater_name}

DEBATER'S ARGUMENTS:
{arguments_text}

Evaluate this debater's performance on the following criteria (each 0-10):
1. Argument Quality: Clarity, structure, and persuasiveness
2. Evidence Quality: Use of facts, citations, and logical reasoning
3. Logical Consistency: Consistency across arguments, avoidance of contradictions
4. Responsiveness to Gaps: Addressing opponent's points and filling gaps

Provide a JSON response with the following structure:
{{
    "argument_quality": <number>,
    "evidence_quality": <number>,
    "logical_consistency": <number>,
    "responsiveness_to_gaps": <number>,
    "overall_score": <number>,
    "feedback": "<detailed feedback>"
}}

Response:"""

            response = self.generate_response(prompt, max_tokens=500)

            try:
                score_data = json.loads(response)
                scores.append(Score(
                    debater_name=debater_name,
                    argument_quality=score_data.get("argument_quality", 0),
                    evidence_quality=score_data.get("evidence_quality", 0),
                    logical_consistency=score_data.get("logical_consistency", 0),
                    responsiveness_to_gaps=score_data.get("responsiveness_to_gaps", 0),
                    overall_score=score_data.get("overall_score", 0),
                    feedback=score_data.get("feedback", "")
                ))
            except json.JSONDecodeError:
                scores.append(Score(
                    debater_name=debater_name,
                    argument_quality=0,
                    evidence_quality=0,
                    logical_consistency=0,
                    responsiveness_to_gaps=0,
                    overall_score=0,
                    feedback="Error parsing response"
                ))

        return scores


# ============================================================================
# DEBATE ORCHESTRATION
# ============================================================================

def run_debate(topic: str, organizer: Organizer, supporter: Debater, opposer: Debater, judge: Judge, num_rounds: int):
    """Run the complete debate with full argument history tracking."""
    arguments: List[Argument] = []

    # -------- Round 0: Organizer's Overview --------
    st.header("Round 0: Topic Overview")
    st.write(f"**Topic**: {topic}")

    with st.spinner(f"Waiting for {organizer.name} to provide overview..."):
        overview = organizer.generate_overview(topic)

    st.write(f"**{organizer.name}** (Organizer):")
    st.write(overview)

    overview_arg = Argument(
        round_number=0,
        participant_name=organizer.name,
        participant_role="organizer",
        content=overview,
        timestamp=datetime.now().isoformat(),
        word_count=organizer.count_words(overview)
    )
    arguments.append(overview_arg)
    st.divider()

    # -------- Rounds 1 to N: Debate Rounds --------
    for round_num in range(1, num_rounds + 1):
        st.header(f"Round {round_num}")

        # Display history expanders at the start of round (except round 1)
        if round_num > 1:
            with st.expander("📚 View Full Debate History"):
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader(f"{supporter.name}'s Arguments")
                    for hist_entry in supporter.argument_history:
                        st.write(f"**Round {hist_entry['round']}:**")
                        st.write(hist_entry['content'])
                        st.divider()

                with col2:
                    st.subheader(f"{opposer.name}'s Arguments")
                    for hist_entry in opposer.argument_history:
                        st.write(f"**Round {hist_entry['round']}:**")
                        st.write(hist_entry['content'])
                        st.divider()

        # -------- Supporter's turn --------
        st.subheader(f"{supporter.name} (Supporter) - Round {round_num}")
        is_initial = (round_num == 1)

        with st.spinner(f"Waiting for {supporter.name}'s response..."):
            if is_initial:
                supporter_arg = supporter.generate_argument(topic, round_num, is_initial=True)
            else:
                # Analyze opponent's latest argument for gaps
                gaps = supporter.analyze_opponent_arguments(topic, [arg.content for arg in arguments if arg.participant_name == opposer.name])

                if gaps:
                    st.info(f"🎯 Gaps identified in {opposer.name}'s arguments:\n" + "\n".join([f"• {gap}" for gap in gaps[:3]]))

                # Generate new argument with full history context
                supporter_arg = supporter.generate_argument(topic, round_num, is_initial=False)

        st.write(supporter_arg)

        # Store in debater's history
        supporter.add_own_argument(supporter_arg, round_num)
        opposer.add_opponent_argument(supporter_arg, round_num)

        supporter_argument = Argument(
            round_number=round_num,
            participant_name=supporter.name,
            participant_role="supporter",
            content=supporter_arg,
            timestamp=datetime.now().isoformat(),
            word_count=supporter.count_words(supporter_arg),
            gaps_identified=supporter.analyze_opponent_arguments(topic, [arg.content for arg in arguments if arg.participant_name == opposer.name]) if not is_initial else None
        )
        arguments.append(supporter_argument)

        st.divider()

        # -------- Opposer's turn --------
        st.subheader(f"{opposer.name} (Opposer) - Round {round_num}")

        with st.spinner(f"Waiting for {opposer.name}'s response..."):
            if is_initial:
                opposer_arg = opposer.generate_argument(topic, round_num, is_initial=True)
            else:
                # Analyze supporter's latest argument for gaps
                gaps = opposer.analyze_opponent_arguments(topic, [arg.content for arg in arguments if arg.participant_name == supporter.name])

                if gaps:
                    st.info(f"🎯 Gaps identified in {supporter.name}'s arguments:\n" + "\n".join([f"• {gap}" for gap in gaps[:3]]))

                # Generate new argument with full history context
                opposer_arg = opposer.generate_argument(topic, round_num, is_initial=False)

        st.write(opposer_arg)

        # Store in debater's history
        opposer.add_own_argument(opposer_arg, round_num)
        supporter.add_opponent_argument(opposer_arg, round_num)

        opposer_argument = Argument(
            round_number=round_num,
            participant_name=opposer.name,
            participant_role="opposer",
            content=opposer_arg,
            timestamp=datetime.now().isoformat(),
            word_count=opposer.count_words(opposer_arg),
            gaps_identified=opposer.analyze_opponent_arguments(topic, [arg.content for arg in arguments if arg.participant_name == supporter.name]) if not is_initial else None
        )
        arguments.append(opposer_argument)

        st.divider()

    # -------- Judge Evaluation --------
    st.header("🏛️ Judge's Evaluation")

    with st.spinner(f"Waiting for {judge.name} to evaluate the debate..."):
        scores = judge.score_debate(topic, arguments)

    # Display scores
    for score in scores:
        with st.expander(f"**{score.debater_name}**'s Score: {score.overall_score:.1f}/10"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Argument Quality", f"{score.argument_quality:.1f}")
            with col2:
                st.metric("Evidence Quality", f"{score.evidence_quality:.1f}")
            with col3:
                st.metric("Logical Consistency", f"{score.logical_consistency:.1f}")
            with col4:
                st.metric("Responsiveness", f"{score.responsiveness_to_gaps:.1f}")

            st.write("**Feedback:**")
            st.write(score.feedback)

    # Determine winner
    if len(scores) == 2:
        if scores[0].overall_score > scores[1].overall_score:
            winner = scores[0].debater_name
            st.success(f"🏆 **Winner: {winner}** with score {scores[0].overall_score:.1f}/10")
        elif scores[1].overall_score > scores[0].overall_score:
            winner = scores[1].debater_name
            st.success(f"🏆 **Winner: {winner}** with score {scores[1].overall_score:.1f}/10")
        else:
            st.info("⚖️ **Debate Result: TIE** - Both debaters presented equally compelling arguments")

    return arguments, scores


# ============================================================================
# STREAMLIT UI
# ============================================================================

def main():
    st.title("🎭 Multi-Participant AI Debate Platform")

    st.sidebar.header("Debate Configuration")

    # Topic input
    topic = st.sidebar.text_area("Enter the debate topic:", height=100)

    # Model selection
    st.sidebar.subheader("Select LLM Models")

    organizer_model = st.sidebar.text_input("Organizer's Model (e.g., 'gpt-4', 'claude-3-opus', 'ollama/llama2')", value="gpt-4")
    supporter_model = st.sidebar.text_input("Supporter's Model", value="gpt-4")
    opposer_model = st.sidebar.text_input("Opposer's Model", value="gpt-4")
    judge_model = st.sidebar.text_input("Judge's Model", value="gpt-4")

    # Participant names
    st.sidebar.subheader("Participant Names")
    organizer_name = st.sidebar.text_input("Organizer's Name", value="Moderator")
    supporter_name = st.sidebar.text_input("Supporter's Name", value="Debater A")
    opposer_name = st.sidebar.text_input("Opposer's Name", value="Debater B")
    judge_name = st.sidebar.text_input("Judge's Name", value="Judge")

    # Number of rounds
    num_rounds = st.sidebar.slider("Number of Debate Rounds", min_value=1, max_value=10, value=3)

    # Start debate button
    if st.sidebar.button("🎬 Start Debate", type="primary"):
        if not topic:
            st.error("❌ Please enter a debate topic")
            return

        # Initialize participants
        organizer = Organizer(organizer_name, organizer_model)
        supporter = Debater(supporter_name, supporter_model, is_supporter=True)
        opposer = Debater(opposer_name, opposer_model, is_supporter=False)
        judge = Judge(judge_name, judge_model)

        # Run the debate
        arguments, scores = run_debate(topic, organizer, supporter, opposer, judge, num_rounds)

        # Save debate transcript
        st.sidebar.success("✅ Debate completed!")

        if st.sidebar.button("💾 Download Debate Transcript"):
            transcript = {
                "topic": topic,
                "arguments": [arg.to_dict() for arg in arguments],
                "scores": [asdict(score) for score in scores],
                "timestamp": datetime.now().isoformat()
            }
            st.sidebar.download_button(
                label="Download as JSON",
                data=json.dumps(transcript, indent=2),
                file_name=f"debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )


if __name__ == "__main__":
    main()

