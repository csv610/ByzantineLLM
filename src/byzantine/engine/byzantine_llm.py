"""Core engine for the Byzantine LLM protocol."""

import logging
import string
from datetime import datetime
from typing import List, Dict, Optional, Any

from ..models.config import ByzantineModelsConfig
from ..models.entities import Proposal, ConsensusResult, NodeEvaluation
from ..participants import Node, Judge
from .prompts import PromptBuilder

logger = logging.getLogger(__name__)

class ByzantineLLM:
    """
    The primary engine for the Byzantine Consensus protocol.
    It orchestrates the 6-step workflow to reach a verified consensus.
    """

    def __init__(
        self,
        models: ByzantineModelsConfig,
        prompt_builder: Optional[PromptBuilder] = None,
        temperature: float = 0.7
    ):
        """
        Initialize the Byzantine network.
        """
        self.models = models
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.temperature = temperature
        
        # Initialize participants
        self.nodes = [
            Node(f"Node-{i+1}", model, temperature=self.temperature) 
            for i, model in enumerate(models.node_models)
        ]
        self.judge = Judge("The Judge", models.judge_model)

    def run(self, question: str) -> ConsensusResult:
        """
        Execute the 6-step Blind Consensus workflow for a given question.
        """
        print(f"\n🚀 Starting Blind NxN Byzantine Consensus: '{question}'")
        print(f"Nodes: {len(self.nodes)} (Full Blindness Mode)")

        # Step 2: Parallel Proposal Generation
        print("\n[Step 2] Nodes generating independent responses...")
        
        system_prompt = self.prompt_builder.create_system_prompt()
        user_prompt = self.prompt_builder.create_user_prompt(question)
        
        proposals: List[Proposal] = []
        real_name_to_content = {}
        
        for node in self.nodes:
            content = node.generate_proposal(user_prompt, system_prompt=system_prompt)
            proposals.append(Proposal(
                participant_name=node.name,
                participant_role=node.get_role(),
                content=content,
                timestamp=datetime.now().isoformat(),
                word_count=len(content.split())
            ))
            real_name_to_content[node.name] = content
            print(f"✅ {node.name} finished.")

        # Step 3: Anonymization
        anonymous_ids = list(string.ascii_uppercase)
        real_to_anon = {node.name: f"Participant {anonymous_ids[i]}" for i, node in enumerate(self.nodes)}
        anon_to_real = {v: k for k, v in real_to_anon.items()}
        anon_proposals = {real_to_anon[name]: content for name, content in real_name_to_content.items()}

        # Step 4: Blind Cross-Auditing (Independent Ranking)
        print("\n[Step 3 & 4] Nodes ranking responses independently and anonymously...")
        anon_rankings = {} 
        for node in self.nodes:
            eval_obj = node.rank_proposals(question, anon_proposals)
            anon_rankings[node.name] = eval_obj
            print(f"✅ {node.name} submitted audit.")

        # Step 5 & 6: Judge Analysis & Matrix Discovery
        print("\n[Step 5 & 6] Judge discovering consensus via NxN Matrix...")
        
        # Anonymize evaluators for the judge
        judge_anon_rankings = {}
        evaluator_real_to_anon = {node.name: f"Evaluator {i+1}" for i, node in enumerate(self.nodes)}
        for node_name, eval_obj in anon_rankings.items():
            judge_anon_rankings[evaluator_real_to_anon[node_name]] = eval_obj

        verdict_data = self.judge.determine_verdict(question, anon_proposals, judge_anon_rankings)
        
        # De-anonymize results
        anon_winner = verdict_data["final_ranking"][0] if verdict_data["final_ranking"] else "None"
        real_winner = anon_to_real.get(anon_winner, anon_winner)
        
        result = ConsensusResult(
            topic=question,
            proposals=proposals,
            ranking_matrix={node_name: eval_obj.rankings for node_name, eval_obj in anon_rankings.items()},
            final_scores={}, 
            winner=real_winner,
            final_response=verdict_data["final_response"],
            timestamp=datetime.now().isoformat(),
            participants={n.name: n.get_role() for n in self.nodes}
        )

        print(f"🏆 Consensus Winner: {real_winner}")
        print("\n" + "="*50)
        print("FINAL AUTHORITATIVE RESPONSE:")
        print("="*50)
        print(result.final_response)
        print("="*50)
        
        return result
