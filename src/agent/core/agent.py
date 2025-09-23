"""
Core AI Agent class for document processing and personal data extraction.
"""
import os
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import anthropic


class Tool(ABC):
    """Abstract base class for agent tools."""

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the tool with given arguments."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return the tool description."""
        pass


class DocumentExtractionAgent:
    """AI Agent specialized in extracting personal details from documents."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the agent with Claude API credentials.

        Args:
            api_key: Claude API key. If None, reads from ANTHROPIC_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Claude API key must be provided or set in ANTHROPIC_API_KEY environment variable")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.tools: List[Tool] = []

        # Default model configuration
        self.model = "claude-3-haiku-20240307"
        self.max_tokens = 4000
        self.temperature = 0.1

    def add_tool(self, tool: Tool) -> None:
        """Add a tool to the agent's toolkit."""
        self.tools.append(tool)

    def remove_tool(self, tool_name: str) -> None:
        """Remove a tool from the agent's toolkit."""
        self.tools = [tool for tool in self.tools if tool.name != tool_name]

    def list_tools(self) -> List[str]:
        """Return list of available tool names."""
        return [tool.name for tool in self.tools]


    def set_model_config(self, model: str = None, max_tokens: int = None, temperature: float = None):
        """Update model configuration parameters."""
        if model:
            self.model = model
        if max_tokens:
            self.max_tokens = max_tokens
        if temperature is not None:
            self.temperature = temperature