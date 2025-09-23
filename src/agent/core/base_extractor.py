"""
Base extractor class for implementing different data extraction types.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import anthropic


class ExtractionResult:
    """Container for extraction results with metadata."""

    def __init__(self, data: Any, extractor_type: str, confidence: float = 0.0, metadata: Optional[Dict] = None):
        self.data = data
        self.extractor_type = extractor_type
        self.confidence = confidence
        self.metadata = metadata or {}
        self.extracted_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "data": self.data,
            "extractor_type": self.extractor_type,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "extracted_at": self.extracted_at
        }


class BaseExtractor(ABC):
    """Abstract base class for all data extractors."""

    def __init__(self, claude_client: anthropic.Anthropic, name: str):
        """
        Initialize the base extractor.

        Args:
            claude_client: Anthropic Claude client instance.
            name: Name identifier for this extractor.
        """
        self.claude_client = claude_client
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

        # Default Claude configuration
        self.model = "claude-3-haiku-20240307"
        self.max_tokens = 4000
        self.temperature = 0.1

    @property
    @abstractmethod
    def extraction_type(self) -> str:
        """Return the type of data this extractor handles."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what this extractor does."""
        pass

    @abstractmethod
    def extract(self, document_content: str, filename: str = "") -> ExtractionResult:
        """
        Extract data from document content.

        Args:
            document_content: The document text to process.
            filename: Source filename for reference.

        Returns:
            ExtractionResult containing the extracted data.
        """
        pass

    @abstractmethod
    def _build_extraction_prompt(self, document_content: str) -> str:
        """Build the Claude prompt for this extraction type."""
        pass

    def _extract_with_claude(self, document_content: str) -> str:
        """
        Use Claude to extract data from document content.

        Args:
            document_content: The document text to process.

        Returns:
            Raw response text from Claude.
        """
        prompt = self._build_extraction_prompt(document_content)

        try:
            response = self.claude_client.messages.create(
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

            return response.content[0].text

        except Exception as e:
            self.logger.error(f"Claude extraction failed: {str(e)}")
            raise RuntimeError(f"Failed to extract with Claude: {str(e)}")

    def set_model_config(self, model: str = None, max_tokens: int = None, temperature: float = None):
        """Update Claude model configuration."""
        if model:
            self.model = model
        if max_tokens:
            self.max_tokens = max_tokens
        if temperature is not None:
            self.temperature = temperature

    def can_process(self, document_content: str) -> bool:
        """
        Determine if this extractor can process the given document.
        Override in subclasses for specific logic.

        Args:
            document_content: The document text to evaluate.

        Returns:
            True if this extractor should process the document.
        """
        return True  # Base implementation processes all documents

    def get_priority(self) -> int:
        """
        Get the processing priority for this extractor.
        Lower numbers = higher priority. Override in subclasses.

        Returns:
            Priority value (default: 100).
        """
        return 100