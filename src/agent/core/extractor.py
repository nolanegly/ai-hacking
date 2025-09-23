"""
Personal data extraction logic and processing pipeline.
"""
from typing import Dict, List, Any, Optional
import logging
import re
import json
from datetime import datetime
import anthropic


class PersonalDataExtractor:
    """Handles extraction and validation of personal data fields using Claude."""

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

    def __init__(self, claude_client: anthropic.Anthropic):
        """
        Initialize the extractor with Claude client.

        Args:
            claude_client: Anthropic Claude client instance.
        """
        self.claude_client = claude_client
        self.logger = logging.getLogger(__name__)
        self.model = "claude-3-haiku-20240307"
        self.max_tokens = 4000
        self.temperature = 0.1

    def extract_from_document(self, document_content: str, filename: str = "") -> List[Dict[str, str]]:
        """
        Extract personal data directly from document content using Claude.

        Args:
            document_content: The document text to extract from.
            filename: Source filename for reference.

        Returns:
            List of formatted records with field name and value.
        """
        try:
            # Use Claude to extract the data
            raw_data = self._extract_with_claude(document_content)

            # Format the results
            records = self._format_extracted_data(raw_data, filename)

            self.logger.info(f"Successfully extracted {len(records)} fields from {filename}")
            return records

        except Exception as e:
            self.logger.error(f"Failed to extract from {filename}: {str(e)}")
            # Return empty records for all fields if extraction fails
            return self._create_empty_records(filename)

    def _extract_with_claude(self, document_content: str) -> Dict[str, Any]:
        """
        Use Claude to extract personal data from document content.

        Args:
            document_content: The document text to process.

        Returns:
            Dictionary containing extracted data with confidence scores.
        """
        prompt = self._build_extraction_prompt(document_content)

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

        # Parse Claude's response
        return self._parse_claude_response(response.content[0].text)

    def _build_extraction_prompt(self, document_content: str) -> str:
        """Build the extraction prompt for Claude."""
        fields_list = "\n".join([f"- {field}" for field in self.STANDARD_FIELDS])

        return f"""
Please extract the following personal details from the document below.
For each field, provide the extracted value and a confidence score (0.0 to 1.0) indicating how certain you are about the extraction.

Fields to extract:
{fields_list}

For each field, respond in this exact JSON format:
{{
  "field_name": "value_found_or_Not_found",
  "confidence": 0.0_to_1.0
}}

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
        """
        Parse Claude's response to extract data and confidence scores.

        Args:
            response_text: Raw response from Claude.

        Returns:
            Dictionary with extracted data and confidence scores.
        """
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
        """
        Format extracted data into standardized records.

        Args:
            raw_data: Raw extracted data from Claude.
            filename: Source filename for reference.

        Returns:
            List of formatted records.
        """
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
                    confidence = self._calculate_confidence(field, value)
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
                "source_file": filename,
                "extracted_at": datetime.now().isoformat(),
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
                "source_file": filename,
                "extracted_at": datetime.now().isoformat(),
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

    def _calculate_confidence(self, field: str, value: str) -> float:
        """
        Calculate confidence score for extracted field.

        Args:
            field: The field name.
            value: The extracted value.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
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
                return 0.9
            else:
                return 0.6  # Value present but doesn't match expected pattern

        # For other fields, basic confidence scoring
        if len(value.strip()) > 0:
            return 0.8

        return 0.0

    def validate_extraction(self, records: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Validate the quality of extraction results.

        Args:
            records: List of extraction records.

        Returns:
            Validation summary with statistics and issues.
        """
        total_fields = len(records)
        found_fields = sum(1 for r in records if r["field_value"] != "Not found")

        high_confidence = sum(1 for r in records if float(r["confidence"]) >= 0.8)
        low_confidence = sum(1 for r in records if float(r["confidence"]) < 0.5)

        validation_summary = {
            "total_fields": total_fields,
            "found_fields": found_fields,
            "missing_fields": total_fields - found_fields,
            "extraction_rate": found_fields / total_fields if total_fields > 0 else 0,
            "high_confidence_fields": high_confidence,
            "low_confidence_fields": low_confidence,
            "average_confidence": sum(float(r["confidence"]) for r in records) / total_fields if total_fields > 0 else 0,
            "validation_timestamp": datetime.now().isoformat()
        }

        return validation_summary