"""Example of using a custom PromptBuilder."""

import asyncio
from src.byzantine import ByzantineLLM, ByzantineModelsConfig, PromptBuilder

async def main():
    # 1. Define the network configuration
    models = ByzantineModelsConfig(
        node_models=["gpt-4o-mini", "claude-3-haiku-20240307"],
        judge_model="gpt-4o"
    )

    # 2. Initialize a custom PromptBuilder
    builder = PromptBuilder(
        system_prompt="You are a professional landscape architect and urban planner. Provide a technical and evidence-based analysis.",
        user_template="As an expert, please write a technical analysis of: {topic}"
    )

    # 3. Initialize the ByzantineLLM engine with the custom builder
    engine = ByzantineLLM(models=models, prompt_builder=builder)
    
    # 4. Run the consensus session
    question = "The benefits of urban gardening"
    print(f"Starting consensus session with custom PromptBuilder...")
    result = engine.run(question)

    # 5. View results
    print("\n--- FINAL AUTHORITATIVE RESPONSE ---")
    print(result.final_response)

if __name__ == "__main__":
    asyncio.run(main())
