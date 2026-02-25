"""Consensus engine for Blind Byzantine Consensus."""

import logging
from datetime import datetime
from typing import List, Dict
import string

from ..models import ConsensusConfig, Proposal, ConsensusResult, NodeEvaluation
from ..participants import Node, Judge

# Note: Keeping the Judge class name as it represents the role, 
# but updating the config field reference.

logger = logging.getLogger(__name__)


class ConsensusSession:
    """Orchestrates the 6-step Blind Byzantine Consensus workflow."""

    def __init__(
        self,
        topic: str,
        nodes: List[Node],
        judge: Judge,
        system_prompt: str = "You are a participant in an objective consensus session. Provide a high-quality, comprehensive, and factual answer.",
        user_prompt_template: str = "{topic}"
    ):
        """Initialize consensus session."""
        self.topic = topic
        self.nodes = nodes
        self.judge = judge
        self.system_prompt = system_prompt
        self.user_prompt_template = user_prompt_template
        self.proposals: List[Proposal] = []
        self.rankings: Dict[str, NodeEvaluation] = {}

    @classmethod
    def from_config(cls, config: ConsensusConfig) -> "ConsensusSession":
        """Create a ConsensusSession from configuration."""
        validated_config = ConsensusConfig.model_validate(config)
        
        nodes = []
        for i, model in enumerate(validated_config.node_models):
            name = f"Node-{i+1}"
            nodes.append(Node(name, model, temperature=validated_config.temperature))
        
        judge = Judge("The Judge", validated_config.judge_model)
        return cls(
            topic=validated_config.topic, 
            nodes=nodes, 
            judge=judge,
            system_prompt=validated_config.system_prompt,
            user_prompt_template=validated_config.user_prompt_template
        )

    def run(self) -> ConsensusResult:
        """
        Execute the 6-step Blind Consensus workflow.
        """
        print(f"\n🚀 Starting Blind NxN Byzantine Consensus: '{self.topic}'")
        print(f"Nodes: {len(self.nodes)} (Full Blindness - No pre-defined adversarial agents)")

        # Step 2: Generate Answers
        print("\n[Step 2] Nodes are generating their responses...")
        
        user_prompt = self.user_prompt_template.format(topic=self.topic)
        
        real_name_to_content = {}
        for node in self.nodes:
            # Step 2: Every model receives the SAME system and user prompt
            content = node.generate_proposal(user_prompt, system_prompt=self.system_prompt)
            self.proposals.append(Proposal(
                participant_name=node.name,
                participant_role=node.get_role(),
                content=content,
                timestamp=datetime.now().isoformat(),
                word_count=len(content.split())
            ))
            real_name_to_content[node.name] = content
            print(f"✅ {node.name} finished response.")

        # Step 3: Anonymize for Blind Evaluation
        anonymous_ids = list(string.ascii_uppercase)
        real_to_anon = {node.name: f"Participant {anonymous_ids[i]}" for i, node in enumerate(self.nodes)}
        anon_to_real = {v: k for k, v in real_to_anon.items()}
        anon_proposals = {real_to_anon[name]: content for name, content in real_name_to_content.items()}

        # Step 3 & 4: Rank Anonymously
        print("\n[Step 3 & 4] Nodes are ranking responses independently and anonymously...")
        anon_rankings = {} 
        for node in self.nodes:
            eval_obj = node.rank_proposals(self.topic, anon_proposals)
            anon_rankings[node.name] = eval_obj
            print(f"✅ {node.name} submitted rankings.")

        # Step 5 & 6: Judge evaluates matrix
        print("\n[Step 5 & 6] Judge discovering consensus via NxN Matrix...")
        
        judge_anon_rankings = {}
        evaluator_real_to_anon = {node.name: f"Evaluator {i+1}" for i, node in enumerate(self.nodes)}
        for node_name, eval_obj in anon_rankings.items():
            judge_anon_rankings[evaluator_real_to_anon[node_name]] = eval_obj

        verdict_data = self.judge.determine_verdict(self.topic, anon_proposals, judge_anon_rankings)
        
        # De-anonymize
        anon_winner = verdict_data["final_ranking"][0] if verdict_data["final_ranking"] else "None"
        real_winner = anon_to_real.get(anon_winner, anon_winner)
        real_final_ranking = [anon_to_real.get(item, item) for item in verdict_data["final_ranking"]]
        
        print(f"🏆 Consensus Winner: {real_winner} ({anon_winner})")
        print(f"⚖️ Final Rankings: {', '.join(real_final_ranking)}")
        if verdict_data.get("byzantine_detection"):
            print(f"🧐 Judge Analysis: {verdict_data['byzantine_detection']}")

        result = ConsensusResult(
            topic=self.topic,
            proposals=self.proposals,
            ranking_matrix={node_name: eval_obj.rankings for node_name, eval_obj in anon_rankings.items()},
            final_scores={}, # Using simple rankings for now
            winner=real_winner,
            final_response=verdict_data["final_response"],
            timestamp=datetime.now().isoformat(),
            participants={n.name: n.get_role() for n in self.nodes}
        )

        print("\n" + "="*50)
        print("FINAL AUTHORITATIVE RESPONSE:")
        print("="*50)
        print(result.final_response)
        print("="*50)
        
        return result
