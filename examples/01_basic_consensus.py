"""Basic example of running a Blind Byzantine Consensus session."""

import asyncio
from src.byzantine import ByzantineLLM, ByzantineModelsConfig

async def main():
    # 1. Define the network configuration
    models = ByzantineModelsConfig(
        node_models=["gpt-4o-mini", "gpt-4o-mini", "gpt-4o-mini"],
        judge_model="gpt-4o"
    )

    # 2. Initialize the ByzantineLLM engine
    # By default, this uses a standard PromptBuilder and temperature of 0.7
    engine = ByzantineLLM(models=models)
    
    # 3. Run the blind consensus protocol
    question = "Explain why the sky is blue."
    print(f"Starting consensus session on topic: '{question}'...")
    result = engine.run(question)

    # 4. View results
    print("\n" + "="*50)
    print("CONSENSUS RESULT")
    print("="*50)
    print(f"Winner: {result.winner}")
    print(f"Final Response:\n{result.final_response}")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
