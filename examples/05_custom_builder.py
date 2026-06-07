"""Example of subclassing PromptBuilder for dynamic logic."""

from src.byzantine import ByzantineLLM, ByzantineModelsConfig, PromptBuilder


class ResearchPromptBuilder(PromptBuilder):
    """A custom builder that injects research context."""

    def create_system_prompt(self) -> str:
        return "You are a PhD researcher specializing in Robotics and AI Ethics."

    def create_user_prompt(self, query: str) -> str:
        context = "Context: The Three Laws were devised by Isaac Asimov."
        return f"{context}\n\nQuestion: {query}"


def main():
    models = ByzantineModelsConfig(
        node_models=["gpt-4o-mini", "claude-3-haiku-20240307"],
        judge_model="gpt-4o"
    )
    builder = ResearchPromptBuilder()
    engine = ByzantineLLM(models=models, prompt_builder=builder)
    question = "What are the three laws of robotics?"
    print("Querying with ResearchPromptBuilder...")
    result = engine.run(question)

    print(f"\nWinner: {result.winner}")
    print(f"Final Response:\n{result.final_response}")


if __name__ == "__main__":
    main()
