"""Example of initializing ByzantineLLM from a config dictionary."""

from src.byzantine import ByzantineLLM, ByzantineModelsConfig, PromptBuilder


def main():
    config_data = {
        "models": {
            "node_models": ["gpt-4o-mini", "claude-3-haiku-20240307"],
            "judge_model": "gpt-4o"
        },
        "system_prompt": "You are a senior distributed systems engineer.",
        "user_template": "Explain this concept for a graduate class: {topic}",
        "temperature": 0.5
    }

    models = ByzantineModelsConfig(**config_data["models"])
    builder = PromptBuilder(
        system_prompt=config_data["system_prompt"],
        user_template=config_data["user_template"]
    )
    engine = ByzantineLLM(
        models=models,
        prompt_builder=builder,
        temperature=config_data["temperature"]
    )
    question = "Byzantine Fault Tolerance"
    print("Starting consensus session loaded from config data...")
    result = engine.run(question)

    print(f"\nWinner: {result.winner}")
    print(f"Final Response:\n{result.final_response}")


if __name__ == "__main__":
    main()
