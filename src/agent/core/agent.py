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

    def process_document(self, document_content: str) -> Dict[str, str]:
        """
        Extract personal details from a document using Claude.

        Args:
            document_content: The content of the document to process.

        Returns:
            Dictionary containing extracted personal details.
        """
        prompt = self._build_extraction_prompt(document_content)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return self._parse_extraction_response(response.content[0].text)

        except Exception as e:
            raise RuntimeError(f"Failed to process document with Claude: {str(e)}")

    def _build_extraction_prompt(self, document_content: str) -> str:
        """Build the prompt for personal data extraction."""
        return f"""
Please extract the following personal details from the document below.
Return the information in JSON format with each field as a key-value pair.
If a field is not found, use "Not found" as the value.

Fields to extract:
- First name
- Last name
- Middle name
- Date of birth
- Social Security Number
- Phone number
- Email address
- Home address
- Employment status
- Annual income
- Employer name
- Job title

Document content:
{document_content}

Please respond with a valid JSON object only, no additional text.
"""

    def _parse_extraction_response(self, response_text: str) -> Dict[str, str]:
        """
        Parse Claude's response and extract the personal details.

        Args:
            response_text: Raw response from Claude.

        Returns:
            Dictionary of extracted personal details.
        """
        import json
        import re

        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback: parse manually if JSON parsing fails
        details = {}
        lines = response_text.strip().split('\n')

        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                details[key.strip()] = value.strip()

        return details

    def set_model_config(self, model: str = None, max_tokens: int = None, temperature: float = None):
        """Update model configuration parameters."""
        if model:
            self.model = model
        if max_tokens:
            self.max_tokens = max_tokens
        if temperature is not None:
            self.temperature = temperature