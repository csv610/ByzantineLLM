"""Example of using a custom PromptBuilder."""

from src.byzantine import ByzantineLLM, ByzantineModelsConfig, PromptBuilder


def main():
    models = ByzantineModelsConfig(
        node_models=["gpt-4o-mini", "claude-3-haiku-20240307"],
        judge_model="gpt-4o"
    )
    builder = PromptBuilder(
        system_prompt="You are a professional landscape architect and urban planner. Provide a technical and evidence-based analysis.",
        user_template="As an expert, please write a technical analysis of: {topic}"
    )
    engine = ByzantineLLM(models=models, prompt_builder=builder)
    question = "The benefits of urban gardening"
    print("Starting consensus session with custom PromptBuilder...")
    result = engine.run(question)

    print("\n--- FINAL AUTHORITATIVE RESPONSE ---")
    print(result.final_response)


if __name__ == "__main__":
    main()
