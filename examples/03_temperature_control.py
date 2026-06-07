"""Example of global temperature control for a consensus session."""

from src.byzantine import ByzantineLLM, ByzantineModelsConfig


def main():
    models = ByzantineModelsConfig(
        node_models=["gpt-4o-mini", "claude-3-haiku-20240307", "gemini-1.5-flash"],
        judge_model="gpt-4o"
    )
    engine = ByzantineLLM(models=models, temperature=0.2)
    question = "What is the safest way to store private keys for cryptocurrency?"
    print(f"Starting consensus session with temperature: {engine.temperature}")
    result = engine.run(question)

    print("\n" + "=" * 50)
    print("CONSENSUS WINNER AND VERIFIED ANSWER")
    print("=" * 50)
    print(f"Winner: {result.winner}")
    print(f"Final Response:\n{result.final_response}")
    print("=" * 50)


if __name__ == "__main__":
    main()
