"""Command-line interface for Blind Byzantine Consensus."""

import argparse
import asyncio
import logging
import json
import os
from datetime import datetime

from src.consensus import ConsensusConfig, ConsensusSession

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def run_consensus_cli():
    """Run the consensus session via CLI."""
    parser = argparse.ArgumentParser(description="Byzantine Consensus Platform CLI (Blind Mode)")
    
    # Core arguments
    parser.add_argument("--topic", type=str, help="The consensus topic/question")
    
    # Model arguments
    parser.add_argument("--node-model", type=str, default="gpt-4o-mini", help="Default LLM for nodes")
    parser.add_argument("--judge-model", type=str, default="gpt-4o-mini", help="LLM for the Judge")
    parser.add_argument("--n", type=int, default=3, help="Number of nodes to initialize (if using default model)")
    parser.add_argument("--temperature", type=float, help="Sampling temperature for all nodes (0.0 to 2.0)")

    # Prompt overrides
    parser.add_argument("--system-prompt", type=str, help="Override default system prompt")
    parser.add_argument("--user-prompt-template", type=str, help="Override default user prompt template (must include {topic})")
    
    # Config/Output
    parser.add_argument("--config", type=str, help="Path to a JSON configuration file")
    parser.add_argument("--output", type=str, help="Path to save the consensus results (JSON)")

    args = parser.parse_args()

    # Load configuration
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config_dict = json.load(f)
                config = ConsensusConfig.model_validate(config_dict)
        except Exception as e:
            print(f"❌ Error loading config file: {str(e)}")
            return
    else:
        if not args.topic:
            print("❌ Error: --topic is required when not using --config")
            return
        
        node_models = [args.node_model] * args.n
        
        config_args = {
            "topic": args.topic,
            "node_models": node_models,
            "judge_model": args.judge_model
        }
        
        if args.system_prompt:
            config_args["system_prompt"] = args.system_prompt
        if args.user_prompt_template:
            config_args["user_prompt_template"] = args.user_prompt_template
        if args.temperature is not None:
            config_args["temperature"] = args.temperature
            
        config = ConsensusConfig(**config_args)

    # Initialize and run session
    try:
        session = ConsensusSession.from_config(config)
        result = session.run()
        
        # Save output if requested
        if args.output:
            result.save(args.output)
            print(f"✅ Results saved to {args.output}")
            
    except Exception as e:
        print(f"❌ Error during consensus: {str(e)}")
        logger.exception("Consensus session failed")


if __name__ == "__main__":
    asyncio.run(run_consensus_cli())
