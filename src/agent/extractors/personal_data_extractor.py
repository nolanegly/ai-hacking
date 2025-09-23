"""
Personal data extractor implementation.
"""
import json
import re
from typing import Dict, List, Any
from ..core.base_extractor import BaseExtractor, ExtractionResult


class PersonalDataExtractor(BaseExtractor):
    """Extracts personal information for loan applications."""

    # Standard personal data fields for loan applications
    STANDARD_FIELDS = [
        "First name",
        "Last name",
        "Middle name",
        "Date of birth",
        "Social Security Number",
        "Phone number",
        "Email address",
        "Home address",
        "Employment status",
        "Annual income",
        "Employer name",
        "Job title"
    ]

    def __init__(self, claude_client):
        super().__init__(claude_client, "personal_data_extractor")

    @property
    def extraction_type(self) -> str:
        return "personal_data"

    @property
    def description(self) -> str:
        return "Extracts personal information fields for loan applications"

    def get_priority(self) -> int:
        return 10  # High priority for personal data

    def can_process(self, document_content: str) -> bool:
        """Check if document likely contains personal data."""
        personal_indicators = [
            "name", "address", "phone", "email", "ssn", "social security",
            "date of birth", "dob", "employer", "income", "salary"
        ]
        content_lower = document_content.lower()
        return any(indicator in content_lower for indicator in personal_indicators)

    def extract(self, document_content: str, filename: str = "") -> ExtractionResult:
        """Extract personal data from document content."""
        try:
            # Use Claude to extract the data
            raw_response = self._extract_with_claude(document_content)

            # Parse Claude's response
            extracted_data = self._parse_claude_response(raw_response)

            # Format the results
            formatted_records = self._format_extracted_data(extracted_data, filename)

            # Calculate overall confidence
            confidences = [record.get("confidence", 0.0) for record in formatted_records]
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return ExtractionResult(
                data=formatted_records,
                extractor_type=self.extraction_type,
                confidence=overall_confidence,
                metadata={
                    "fields_extracted": len([r for r in formatted_records if r["field_value"] != "Not found"]),
                    "total_fields": len(formatted_records),
                    "source_file": filename
                }
            )

        except Exception as e:
            self.logger.error(f"Failed to extract personal data from {filename}: {str(e)}")
            # Return empty result on failure
            return ExtractionResult(
                data=self._create_empty_records(filename),
                extractor_type=self.extraction_type,
                confidence=0.0,
                metadata={"error": str(e), "source_file": filename}
            )

    def _build_extraction_prompt(self, document_content: str) -> str:
        """Build the extraction prompt for personal data."""
        fields_list = "\n".join([f"- {field}" for field in self.STANDARD_FIELDS])

        return f"""
Please extract the following personal details from the document below.
For each field, provide the extracted value and a confidence score (0.0 to 1.0) indicating how certain you are about the extraction.

Fields to extract:
{fields_list}

If a field is not found in the document, use "Not found" as the value and 0.0 as confidence.
If a field is found but you're uncertain about the value, use a lower confidence score.

Document content:
---
{document_content}
---

Please respond with a JSON object where each key is a field name and each value is an object with "value" and "confidence" properties. Example:

{{
  "First name": {{"value": "John", "confidence": 0.9}},
  "Last name": {{"value": "Not found", "confidence": 0.0}}
}}
"""

    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's response to extract data and confidence scores."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
                return parsed_data

        except json.JSONDecodeError:
            self.logger.warning("Failed to parse JSON from Claude response, using fallback parsing")

        # Fallback parsing if JSON fails
        return self._fallback_parse_response(response_text)

    def _fallback_parse_response(self, response_text: str) -> Dict[str, Any]:
        """Fallback parsing when JSON parsing fails."""
        extracted = {}

        for field in self.STANDARD_FIELDS:
            # Simple pattern matching as fallback
            pattern = rf'{re.escape(field)}[:\s]+([^\n]+)'
            match = re.search(pattern, response_text, re.IGNORECASE)

            if match:
                value = match.group(1).strip()
                confidence = 0.6  # Lower confidence for fallback parsing
            else:
                value = "Not found"
                confidence = 0.0

            extracted[field] = {"value": value, "confidence": confidence}

        return extracted

    def _format_extracted_data(self, raw_data: Dict[str, Any], filename: str) -> List[Dict[str, str]]:
        """Format extracted data into standardized records."""
        records = []

        for field in self.STANDARD_FIELDS:
            if field in raw_data:
                field_data = raw_data[field]
                if isinstance(field_data, dict):
                    value = field_data.get("value", "Not found")
                    confidence = float(field_data.get("confidence", 0.0))
                else:
                    # Handle cases where Claude returns just the value
                    value = str(field_data)
                    confidence = self._calculate_basic_confidence(field, value)
            else:
                value = "Not found"
                confidence = 0.0

            # Clean and validate the value
            value = self._clean_value(value)

            # Validate confidence score
            confidence = max(0.0, min(1.0, confidence))

            record = {
                "field_name": field,
                "field_value": value,
                "confidence": confidence
            }

            records.append(record)

        return records

    def _create_empty_records(self, filename: str) -> List[Dict[str, str]]:
        """Create empty records when extraction fails."""
        records = []

        for field in self.STANDARD_FIELDS:
            record = {
                "field_name": field,
                "field_value": "Not found",
                "confidence": 0.0
            }
            records.append(record)

        return records

    def _clean_value(self, value: str) -> str:
        """Clean and normalize extracted values."""
        if not value or value.lower() in ["not found", "n/a", "none", "null", ""]:
            return "Not found"

        # Remove extra whitespace
        value = re.sub(r'\s+', ' ', value.strip())

        # Remove quotes if they wrap the entire value
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]

        return value

    def _calculate_basic_confidence(self, field: str, value: str) -> float:
        """Calculate basic confidence score for extracted field."""
        if value == "Not found":
            return 0.0

        # Basic validation patterns
        patterns = {
            "Social Security Number": r'^\d{3}-?\d{2}-?\d{4}$',
            "Phone number": r'^[\+]?[\d\s\-\(\)]{10,}$',
            "Email address": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            "Date of birth": r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}',
        }

        if field in patterns:
            if re.search(patterns[field], value):
                return 0.8
            else:
                return 0.5  # Value present but doesn't match expected pattern

        # For other fields, basic confidence scoring
        if len(value.strip()) > 0:
            return 0.7

        return 0.0