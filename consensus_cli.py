"""Command-line interface for the ByzantineLLM Framework."""

import argparse
import logging
import json
from src.byzantine import ByzantineLLM, ByzantineModelsConfig, PromptBuilder

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="ByzantineLLM CLI (Blind Consensus Mode)")

    parser.add_argument("--topic", type=str, help="The consensus topic/question")
    parser.add_argument("--config", type=str, help="Path to JSON config file")
    parser.add_argument("--node-model", type=str, default="gpt-4o-mini", help="Default LLM for nodes")
    parser.add_argument("--judge-model", type=str, default="gpt-4o", help="LLM for the Judge")
    parser.add_argument("--n", type=int, default=3, help="Number of nodes (used with --node-model)")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature")
    parser.add_argument("--system-prompt", type=str, help="Override default system prompt")
    parser.add_argument("--user-prompt-template", type=str, help="Override default user prompt template")
    parser.add_argument("--output", type=str, help="Path to save results (JSON)")

    args = parser.parse_args()

    if not args.topic and not args.config:
        parser.error("Either --topic or --config must be provided")

    topic = args.topic

    if args.config:
        cfg = load_config(args.config)
        topic = topic or cfg.get("topic", topic)
        models_data = cfg.get("models", {})
        node_models = models_data.get("node_models", [args.node_model] * args.n)
        judge_model = models_data.get("judge_model", args.judge_model)
        temperature = cfg.get("temperature", args.temperature)
    else:
        node_models = [args.node_model] * args.n
        judge_model = args.judge_model
        temperature = args.temperature

    models_config = ByzantineModelsConfig(
        node_models=node_models,
        judge_model=judge_model
    )

    builder_args = {}
    if args.system_prompt:
        builder_args["system_prompt"] = args.system_prompt
    if args.user_prompt_template:
        builder_args["user_template"] = args.user_prompt_template

    prompt_builder = PromptBuilder(**builder_args) if builder_args else None

    engine = ByzantineLLM(
        models=models_config,
        prompt_builder=prompt_builder,
        temperature=temperature
    )

    try:
        result = engine.run(topic)

        print("\nParticipant Scores:")
        for name, score in result.final_scores.items():
            print(f"  {name}: {score}/10")

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result.model_dump(), f, indent=2)
            print(f"Results saved to {args.output}")

    except Exception as e:
        print(f"Error: {str(e)}")
        logger.exception("Byzantine session failed")


if __name__ == "__main__":
    main()
