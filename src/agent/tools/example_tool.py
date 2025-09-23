"""
Example tool implementation demonstrating the tool interface.
"""
from typing import Any
from ..core.agent import Tool


class DocumentValidatorTool(Tool):
    """Example tool that validates document content before processing."""

    @property
    def name(self) -> str:
        return "document_validator"

    @property
    def description(self) -> str:
        return "Validates document content quality and readability before extraction"

    def execute(self, document_content: str, **kwargs) -> dict:
        """
        Validate document content quality.

        Args:
            document_content: The document text to validate.

        Returns:
            Dictionary with validation results.
        """
        if not document_content or not isinstance(document_content, str):
            return {
                "is_valid": False,
                "reason": "Document content is empty or invalid",
                "score": 0.0
            }

        # Basic validation checks
        word_count = len(document_content.split())
        char_count = len(document_content)
        line_count = len(document_content.split('\n'))

        # Check for minimum content requirements
        if word_count < 10:
            return {
                "is_valid": False,
                "reason": "Document too short (less than 10 words)",
                "score": 0.1
            }

        # Check for reasonable text structure
        if char_count / word_count > 50:  # Average word length too high
            return {
                "is_valid": False,
                "reason": "Document may contain corrupted or encoded content",
                "score": 0.3
            }

        # Calculate quality score
        score = min(1.0, (word_count / 100) * 0.5 + (line_count / 20) * 0.3 + 0.2)

        return {
            "is_valid": True,
            "reason": "Document passed validation checks",
            "score": score,
            "word_count": word_count,
            "char_count": char_count,
            "line_count": line_count
        }


class DataFormatterTool(Tool):
    """Example tool that formats extracted data in different ways."""

    @property
    def name(self) -> str:
        return "data_formatter"

    @property
    def description(self) -> str:
        return "Formats extracted personal data into different output formats"

    def execute(self, extracted_data: dict, format_type: str = "standard", **kwargs) -> Any:
        """
        Format extracted data according to specified format.

        Args:
            extracted_data: Dictionary of extracted personal data.
            format_type: Type of formatting to apply ('standard', 'compact', 'verbose').

        Returns:
            Formatted data structure.
        """
        if format_type == "compact":
            return self._format_compact(extracted_data)
        elif format_type == "verbose":
            return self._format_verbose(extracted_data)
        else:
            return self._format_standard(extracted_data)

    def _format_standard(self, data: dict) -> dict:
        """Standard formatting with field name and value."""
        return {f"{key}": value for key, value in data.items()}

    def _format_compact(self, data: dict) -> dict:
        """Compact formatting with shortened field names."""
        field_mapping = {
            "First name": "fname",
            "Last name": "lname",
            "Date of birth": "dob",
            "Social Security Number": "ssn",
            "Phone number": "phone",
            "Email address": "email",
            "Home address": "address",
            "Employment status": "emp_status",
            "Annual income": "income",
            "Employer name": "employer",
            "Job title": "title"
        }

        return {
            field_mapping.get(key, key.lower().replace(" ", "_")): value
            for key, value in data.items()
        }

    def _format_verbose(self, data: dict) -> dict:
        """Verbose formatting with additional metadata."""
        result = {}
        for key, value in data.items():
            result[key] = {
                "value": value,
                "field_type": self._get_field_type(key),
                "is_required": key in ["First name", "Last name", "Social Security Number"],
                "data_length": len(str(value)) if value != "Not found" else 0
            }
        return result

    def _get_field_type(self, field_name: str) -> str:
        """Determine the expected data type for a field."""
        type_mapping = {
            "Date of birth": "date",
            "Social Security Number": "ssn",
            "Phone number": "phone",
            "Email address": "email",
            "Annual income": "currency",
            "Home address": "address"
        }
        return type_mapping.get(field_name, "text")