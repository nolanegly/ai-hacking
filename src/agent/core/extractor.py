"""
Personal data extraction logic and processing pipeline.
"""
from typing import Dict, List, Any
import logging
import re
from datetime import datetime


class PersonalDataExtractor:
    """Handles extraction and validation of personal data fields."""

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

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_and_format(self, raw_data: Dict[str, str], filename: str = "") -> List[Dict[str, str]]:
        """
        Extract and format personal data into standardized records.

        Args:
            raw_data: Raw extracted data from the agent.
            filename: Source filename for reference.

        Returns:
            List of formatted records with field name and value.
        """
        records = []

        for field in self.STANDARD_FIELDS:
            value = self._find_field_value(raw_data, field)

            # Format the record
            record = {
                "field_name": field,
                "field_value": value,
                "source_file": filename,
                "extracted_at": datetime.now().isoformat(),
                "confidence": self._calculate_confidence(field, value)
            }

            records.append(record)

        return records

    def _find_field_value(self, raw_data: Dict[str, str], target_field: str) -> str:
        """
        Find the value for a target field from raw extracted data.

        Args:
            raw_data: Dictionary of extracted data.
            target_field: The field name to search for.

        Returns:
            The field value or "Not found" if not available.
        """
        # Direct match
        if target_field in raw_data:
            return self._clean_value(raw_data[target_field])

        # Case-insensitive search
        for key, value in raw_data.items():
            if key.lower() == target_field.lower():
                return self._clean_value(value)

        # Fuzzy matching for common variations
        variations = self._get_field_variations(target_field)
        for key, value in raw_data.items():
            if any(var.lower() in key.lower() for var in variations):
                return self._clean_value(value)

        return "Not found"

    def _get_field_variations(self, field: str) -> List[str]:
        """Get common variations of field names."""
        variations_map = {
            "First name": ["firstname", "first", "given name", "forename"],
            "Last name": ["lastname", "last", "surname", "family name"],
            "Middle name": ["middlename", "middle", "middle initial"],
            "Date of birth": ["dob", "birth date", "birthdate", "born"],
            "Social Security Number": ["ssn", "social security", "social sec"],
            "Phone number": ["phone", "telephone", "mobile", "cell"],
            "Email address": ["email", "e-mail", "electronic mail"],
            "Home address": ["address", "residence", "street address"],
            "Employment status": ["employment", "job status", "work status"],
            "Annual income": ["income", "salary", "yearly income", "gross income"],
            "Employer name": ["employer", "company", "workplace"],
            "Job title": ["title", "position", "occupation", "role"]
        }

        return variations_map.get(field, [field])

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