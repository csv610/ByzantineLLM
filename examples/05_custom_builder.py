"""Example of subclassing PromptBuilder for dynamic logic."""

import asyncio
from src.byzantine import ByzantineLLM, ByzantineModelsConfig, PromptBuilder

class ResearchPromptBuilder(PromptBuilder):
    """A custom builder that injects research context."""
    
    def create_system_prompt(self) -> str:
        return "You are a PhD researcher specializing in Robotics and AI Ethics."

    def create_user_prompt(self, query: str) -> str:
        # Imagine fetching this context from a database or RAG system
        context = "Context: The Three Laws were devised by Isaac Asimov."
        return f"{context}\n\nQuestion: {query}"

async def main():
    # 1. Network setup
    models = ByzantineModelsConfig(
        node_models=["gpt-4o-mini", "claude-3-haiku-20240307"],
        judge_model="gpt-4o"
    )
    
    # 2. Use the custom subclass
    builder = ResearchPromptBuilder()
    
    # 3. Initialize engine
    engine = ByzantineLLM(models=models, prompt_builder=builder)

    # 4. Run session
    question = "What are the three laws of robotics?"
    print(f"Querying with ResearchPromptBuilder...")
    result = engine.run(question)

    print(f"\nWinner: {result.winner}")
    print(f"Final Response:\n{result.final_response}")

if __name__ == "__main__":
    asyncio.run(main())
