"""Prompt building logic for the Byzantine network."""

class PromptBuilder:
    """
    Standard class for building node prompts. 
    Can be inherited and overridden to implement custom logic for different applications.
    """
    
    def __init__(
        self, 
        system_prompt: str = "You are a participant in an objective consensus session. Provide a high-quality, comprehensive, and factual answer.",
        user_template: str = "{topic}"
    ):
        self.system_prompt = system_prompt
        self.user_template = user_template

    def create_system_prompt(self) -> str:
        """Returns the system prompt for all nodes."""
        return self.system_prompt

    def create_user_prompt(self, query: str) -> str:
        """Returns the user prompt for all nodes based on the query."""
        return self.user_template.format(topic=query)
