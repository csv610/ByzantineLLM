"""Basic example of running a Blind Byzantine Consensus session."""

from src.byzantine import ByzantineLLM, ByzantineModelsConfig


def main():
    models = ByzantineModelsConfig(
        node_models=["gpt-4o-mini", "gpt-4o-mini", "gpt-4o-mini"],
        judge_model="gpt-4o"
    )
    engine = ByzantineLLM(models=models)
    question = "Explain why the sky is blue."
    print(f"Starting consensus session on topic: '{question}'...")
    result = engine.run(question)

    print("\n" + "=" * 50)
    print("CONSENSUS RESULT")
    print("=" * 50)
    print(f"Winner: {result.winner}")
    print(f"Final Response:\n{result.final_response}")
    print("=" * 50)


if __name__ == "__main__":
    main()
