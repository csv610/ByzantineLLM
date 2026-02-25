"""Command-line interface for the ByzantineLLM Framework."""

import argparse
import asyncio
import logging
import json
from src.byzantine import ByzantineLLM, ByzantineModelsConfig, PromptBuilder

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_consensus_cli():
    parser = argparse.ArgumentParser(description="ByzantineLLM CLI (Blind Mode)")
    
    # Core arguments
    parser.add_argument("--topic", type=str, required=True, help="The consensus topic/question")
    
    # Network Configuration
    parser.add_argument("--node-model", type=str, default="gpt-4o-mini", help="Default LLM for nodes")
    parser.add_argument("--judge-model", type=str, default="gpt-4o", help="LLM for the Judge")
    parser.add_argument("--n", type=int, default=3, help="Number of nodes")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature")

    # Prompt overrides
    parser.add_argument("--system-prompt", type=str, help="Override default system prompt")
    parser.add_argument("--user-prompt-template", type=str, help="Override default user prompt template")
    
    # Output
    parser.add_argument("--output", type=str, help="Path to save results (JSON)")

    args = parser.parse_args()

    # 1. Setup Models
    models_config = ByzantineModelsConfig(
        node_models=[args.node_model] * args.n,
        judge_model=args.judge_model
    )

    # 2. Setup Prompt Builder
    builder_args = {}
    if args.system_prompt:
        builder_args["system_prompt"] = args.system_prompt
    if args.user_prompt_template:
        builder_args["user_template"] = args.user_prompt_template
    
    prompt_builder = PromptBuilder(**builder_args) if builder_args else None

    # 3. Initialize the Engine
    engine = ByzantineLLM(
        models=models_config,
        prompt_builder=prompt_builder,
        temperature=args.temperature
    )

    # 3. Run Consensus
    try:
        result = engine.run(args.topic)
        
        print("\n📊 Participant Scores:")
        for name, score in result.final_scores.items():
            print(f"  - {name}: {score}/10")
            
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result.model_dump(), f, indent=2)
            print(f"✅ Results saved to {args.output}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.exception("Byzantine session failed")

if __name__ == "__main__":
    asyncio.run(run_consensus_cli())
