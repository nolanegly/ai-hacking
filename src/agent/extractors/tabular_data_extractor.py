"""
Tabular data extractor implementation.
"""
import json
import re
from typing import Dict, List, Any, Optional
from ..core.base_extractor import BaseExtractor, ExtractionResult


class TabularDataExtractor(BaseExtractor):
    """Extracts tabular data from documents."""

    def __init__(self, claude_client):
        super().__init__(claude_client, "tabular_data_extractor")

    @property
    def extraction_type(self) -> str:
        return "tabular_data"

    @property
    def description(self) -> str:
        return "Extracts tabular data and identifies data types within tables"

    def get_priority(self) -> int:
        return 20  # Lower priority than personal data

    def can_process(self, document_content: str) -> bool:
        """Check if document likely contains tabular data."""
        tabular_indicators = [
            # Table structure indicators
            "|", "+-", "===", "---",
            # Column/row indicators
            "table", "column", "row", "header",
            # Data organization patterns
            "\t", "    ",  # Tabs and multiple spaces
        ]

        # Check for CSV-like patterns
        lines = document_content.split('\n')
        csv_like_lines = 0
        for line in lines[:20]:  # Check first 20 lines
            if ',' in line and len(line.split(',')) >= 2:
                csv_like_lines += 1

        # Check for multiple aligned data patterns
        aligned_data = 0
        for line in lines[:30]:
            if re.search(r'\w+\s{2,}\w+\s{2,}\w+', line):  # Multiple words with 2+ spaces
                aligned_data += 1

        return (
            csv_like_lines >= 3 or  # At least 3 CSV-like lines
            aligned_data >= 3 or    # At least 3 aligned data lines
            any(indicator in document_content for indicator in tabular_indicators)
        )

    def extract(self, document_content: str, filename: str = "") -> ExtractionResult:
        """Extract tabular data from document content."""
        try:
            # Use Claude to extract the data
            raw_response = self._extract_with_claude(document_content)

            # Parse Claude's response
            extracted_tables = self._parse_claude_response(raw_response)

            # Validate and format the results
            formatted_tables = self._format_extracted_tables(extracted_tables, filename)

            # Calculate overall confidence
            confidences = [table.get("confidence", 0.0) for table in formatted_tables]
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return ExtractionResult(
                data=formatted_tables,
                extractor_type=self.extraction_type,
                confidence=overall_confidence,
                metadata={
                    "tables_found": len(formatted_tables),
                    "total_data_points": sum(len(table.get("data", [])) for table in formatted_tables),
                    "source_file": filename
                }
            )

        except Exception as e:
            self.logger.error(f"Failed to extract tabular data from {filename}: {str(e)}")
            # Return empty result on failure
            return ExtractionResult(
                data=[],
                extractor_type=self.extraction_type,
                confidence=0.0,
                metadata={"error": str(e), "source_file": filename}
            )

    def _build_extraction_prompt(self, document_content: str) -> str:
        """Build the extraction prompt for tabular data."""
        return f"""
Please identify and extract all tabular data from the document below.
For each table or structured data area you find, provide:
1. The table data in a structured format
2. A dataType classification (e.g., "financial_data", "personal_info", "inventory", "schedule", "contact_list", "transaction_history", etc.)
3. Column headers if present
4. A confidence score (0.0 to 1.0) for the extraction accuracy

Document content:
---
{document_content}
---

Please respond with a JSON array where each element represents a table with this structure:

[
  {{
    "dataType": "financial_data",
    "headers": ["Date", "Description", "Amount"],
    "data": [
      ["2024-01-01", "Salary", "5000"],
      ["2024-01-02", "Rent", "-1200"]
    ],
    "confidence": 0.9,
    "description": "Monthly financial transactions"
  }},
  {{
    "dataType": "contact_list",
    "headers": ["Name", "Phone", "Email"],
    "data": [
      ["John Doe", "555-1234", "john@email.com"],
      ["Jane Smith", "555-5678", "jane@email.com"]
    ],
    "confidence": 0.85,
    "description": "Contact information list"
  }}
]

If no tabular data is found, return an empty array: []

Focus on identifying structured data that would be useful in a business or personal context.
Common dataType classifications include: financial_data, personal_info, inventory, schedule, contact_list, transaction_history, asset_list, liability_list, income_statement, expense_report, etc.
"""

    def _parse_claude_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse Claude's response to extract table data."""
        try:
            # Try to extract JSON array from the response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
                if isinstance(parsed_data, list):
                    return parsed_data

        except json.JSONDecodeError:
            self.logger.warning("Failed to parse JSON from Claude response, using fallback parsing")

        # Fallback parsing if JSON fails
        return self._fallback_parse_response(response_text)

    def _fallback_parse_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Fallback parsing when JSON parsing fails."""
        tables = []
        lines = response_text.split('\n')
        current_table = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for table indicators
            if '|' in line or '\t' in line or re.search(r'\w+\s{3,}\w+', line):
                if current_table is None:
                    current_table = {
                        "dataType": "unknown",
                        "headers": [],
                        "data": [],
                        "confidence": 0.5,
                        "description": "Table detected via fallback parsing"
                    }

                # Try to split the line into columns
                if '|' in line:
                    columns = [col.strip() for col in line.split('|') if col.strip()]
                elif '\t' in line:
                    columns = [col.strip() for col in line.split('\t') if col.strip()]
                else:
                    columns = re.split(r'\s{2,}', line)

                if len(columns) >= 2:
                    if not current_table["headers"]:
                        current_table["headers"] = columns
                    else:
                        current_table["data"].append(columns)

            else:
                # End of current table
                if current_table and len(current_table["data"]) > 0:
                    tables.append(current_table)
                    current_table = None

        # Add final table if exists
        if current_table and len(current_table["data"]) > 0:
            tables.append(current_table)

        return tables

    def _format_extracted_tables(self, tables: List[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        """Format and validate extracted table data."""
        formatted_tables = []

        for i, table in enumerate(tables):
            if not isinstance(table, dict):
                continue

            formatted_table = {
                "dataType": self._validate_data_type(table.get("dataType", "unknown")),
                "headers": table.get("headers", []),
                "data": table.get("data", []),
                "confidence": max(0.0, min(1.0, float(table.get("confidence", 0.0)))),
                "description": table.get("description", f"Table {i+1}"),
                "table_id": f"table_{i+1}",
                "row_count": len(table.get("data", [])),
                "column_count": len(table.get("headers", []))
            }

            # Only include tables with actual data
            if formatted_table["row_count"] > 0 and formatted_table["column_count"] > 0:
                formatted_tables.append(formatted_table)

        return formatted_tables

    def _validate_data_type(self, data_type: str) -> str:
        """Validate and normalize data type classification."""
        valid_types = {
            "financial_data", "personal_info", "inventory", "schedule",
            "contact_list", "transaction_history", "asset_list",
            "liability_list", "income_statement", "expense_report",
            "employment_history", "education_history", "reference_list",
            "unknown"
        }

        # Normalize the data type
        normalized = data_type.lower().replace(" ", "_")

        if normalized in valid_types:
            return normalized

        # Try to match partial types
        for valid_type in valid_types:
            if normalized in valid_type or valid_type in normalized:
                return valid_type

        return "unknown"