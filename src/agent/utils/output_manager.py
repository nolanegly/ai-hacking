"""
Output management utilities for saving extraction results.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import logging


class OutputManager:
    """Handles saving and managing extraction output files."""

    def __init__(self, output_dir: str = "data/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def save_extraction_results(self,
                               results,
                               filename: str = None,
                               include_metadata: bool = True) -> str:
        """
        Save extraction results to a JSON file.

        Args:
            results: List of extraction records.
            filename: Output filename. If None, generates timestamp-based name.
            include_metadata: Whether to include metadata in output.

        Returns:
            Path to the saved file.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"extraction_results_{timestamp}.json"

        output_path = self.output_dir / filename

        # Format results according to specified format
        formatted_results = self._format_results(results, include_metadata)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(formatted_results, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Results saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Failed to save results: {str(e)}")
            raise

    def _format_results(self, results: Dict[str, Any], include_metadata: bool) -> Dict[str, Any]:
        """Format results according to the new modular extraction structure."""

        # Handle both old format (list of records) and new format (pipeline results)
        if isinstance(results, list):
            # Legacy format - convert to new format
            return self._format_legacy_results(results, include_metadata)

        # New modular format
        output_data = {
            "extraction_summary": {
                "total_files_processed": 1,
                "processed_at": datetime.now().isoformat(),
                "extraction_types": list(results.keys())
            }
        }

        # Format personal data if present
        if "personalData" in results:
            personal_data = results["personalData"]["data"]
            formatted_personal = []

            for record in personal_data:
                # Only include records where data was actually found
                if record["field_value"] != "Not found":
                    camel_case_field = self._convert_to_camel_case(record["field_name"])

                    formatted_record = {
                        camel_case_field: record["field_value"],
                        "confidence": record.get("confidence", 0.0)
                    }

                    if include_metadata:
                        formatted_record["extracted_at"] = results["personalData"].get("extracted_at", "")

                    formatted_personal.append(formatted_record)

            output_data["personalData"] = formatted_personal

        # Format tabular data if present
        if "tabularData" in results:
            tabular_data = results["tabularData"]["data"]
            output_data["tabularData"] = tabular_data

        # Add extraction metadata if present
        if "extraction_metadata" in results:
            output_data["extraction_metadata"] = results["extraction_metadata"]

        # Include any other extraction types
        for key, value in results.items():
            if key not in ["personalData", "tabularData", "extraction_metadata"]:
                output_data[key] = value

        return output_data

    def _format_legacy_results(self, results: List[Dict[str, str]], include_metadata: bool) -> Dict[str, Any]:
        """Format legacy results format for backward compatibility."""
        # Group results by source file
        files_data = {}
        for result in results:
            source_file = result.get("source_file", "unknown")
            if source_file not in files_data:
                files_data[source_file] = []

            # Format as "field name: field value"
            formatted_record = f"{result['field_name']}: {result['field_value']}"

            record_data = {
                "record": formatted_record,
                "confidence": result.get("confidence", 0.0)
            }

            if include_metadata:
                record_data.update({
                    "extracted_at": result.get("extracted_at", "")
                })

            files_data[source_file].append(record_data)

        output_data = {
            "extraction_summary": {
                "total_files_processed": len(files_data),
                "total_records": len(results),
                "processed_at": datetime.now().isoformat()
            },
            "results": files_data
        }

        return output_data

    def _convert_to_camel_case(self, field_name: str) -> str:
        """Convert field name to camelCase format."""
        # Mapping of standard field names to camelCase
        field_mapping = {
            "First name": "firstName",
            "Last name": "lastName",
            "Middle name": "middleName",
            "Date of birth": "dateOfBirth",
            "Social Security Number": "socialSecurityNumber",
            "Phone number": "phoneNumber",
            "Email address": "emailAddress",
            "Home address": "homeAddress",
            "Employment status": "employmentStatus",
            "Annual income": "annualIncome",
            "Employer name": "employerName",
            "Job title": "jobTitle"
        }

        # Return mapped field name or convert generic field name to camelCase
        if field_name in field_mapping:
            return field_mapping[field_name]

        # Generic conversion: remove spaces, lowercase first word, capitalize others
        words = field_name.split()
        if len(words) == 0:
            return field_name

        camel_case = words[0].lower()
        for word in words[1:]:
            camel_case += word.capitalize()

        return camel_case

    def save_validation_report(self, validation_data: Dict[str, Any], filename: str = None) -> str:
        """
        Save validation report to a JSON file.

        Args:
            validation_data: Validation summary data.
            filename: Output filename. If None, generates timestamp-based name.

        Returns:
            Path to the saved file.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"validation_report_{timestamp}.json"

        output_path = self.output_dir / filename

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(validation_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Validation report saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Failed to save validation report: {str(e)}")
            raise

    def create_summary_report(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a comprehensive summary report.

        Args:
            all_results: All extraction results from multiple files.

        Returns:
            Summary report data.
        """
        total_files = len(set(r.get("source_file", "") for r in all_results))
        total_records = len(all_results)

        found_records = [r for r in all_results if r.get("field_value", "") != "Not found"]
        extraction_rate = len(found_records) / total_records if total_records > 0 else 0

        # Field-specific statistics
        field_stats = {}
        fields = set(r.get("field_name", "") for r in all_results)

        for field in fields:
            field_records = [r for r in all_results if r.get("field_name", "") == field]
            found_count = len([r for r in field_records if r.get("field_value", "") != "Not found"])

            field_stats[field] = {
                "total_occurrences": len(field_records),
                "found_count": found_count,
                "success_rate": found_count / len(field_records) if field_records else 0,
                "average_confidence": sum(float(r.get("confidence", 0)) for r in field_records) / len(field_records) if field_records else 0
            }

        summary = {
            "overview": {
                "total_files_processed": total_files,
                "total_records_extracted": total_records,
                "successful_extractions": len(found_records),
                "overall_extraction_rate": extraction_rate,
                "report_generated_at": datetime.now().isoformat()
            },
            "field_statistics": field_stats,
            "recommendations": self._generate_recommendations(field_stats, extraction_rate)
        }

        return summary

    def _generate_recommendations(self, field_stats: Dict[str, Dict], overall_rate: float) -> List[str]:
        """Generate recommendations based on extraction performance."""
        recommendations = []

        if overall_rate < 0.5:
            recommendations.append("Overall extraction rate is low. Consider improving document quality or extraction prompts.")

        # Find fields with low success rates
        low_performing_fields = [
            field for field, stats in field_stats.items()
            if stats["success_rate"] < 0.3
        ]

        if low_performing_fields:
            recommendations.append(f"The following fields have low extraction rates: {', '.join(low_performing_fields)}. Consider adding field variations or improving document formatting.")

        # Find fields with low confidence
        low_confidence_fields = [
            field for field, stats in field_stats.items()
            if stats["average_confidence"] < 0.5
        ]

        if low_confidence_fields:
            recommendations.append(f"The following fields have low confidence scores: {', '.join(low_confidence_fields)}. Manual review recommended.")

        if not recommendations:
            recommendations.append("Extraction performance looks good. No specific recommendations at this time.")

        return recommendations

    def list_output_files(self) -> List[Dict[str, Any]]:
        """List all files in the output directory with metadata."""
        files = []

        for file_path in self.output_dir.iterdir():
            if file_path.is_file() and file_path.suffix == '.json':
                stat = file_path.stat()
                files.append({
                    'filename': file_path.name,
                    'path': str(file_path),
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        return sorted(files, key=lambda x: x['modified'], reverse=True)

    def create_personal_data_aggregation(self, all_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate personal data across all documents to identify patterns and inconsistencies.

        Args:
            all_results: Dictionary of all extraction results by filename.

        Returns:
            Aggregated personal data with all values and their source files.
        """
        aggregated_data = {}

        # Process each document's results
        for filename, results in all_results.items():
            if "personalData" not in results:
                continue

            personal_data_result = results["personalData"]
            if not isinstance(personal_data_result, dict) or "data" not in personal_data_result:
                continue

            # Process each personal data field found in this document
            for record in personal_data_result["data"]:
                field_name = record.get("field_name", "")
                field_value = record.get("field_value", "")
                confidence = record.get("confidence", 0.0)

                # Skip "Not found" values
                if field_value == "Not found":
                    continue

                # Convert to camelCase
                camel_case_field = self._convert_to_camel_case(field_name)

                # Initialize field in aggregated data if not exists
                if camel_case_field not in aggregated_data:
                    aggregated_data[camel_case_field] = []

                # Look for existing value entry
                existing_value_entry = None
                for value_entry in aggregated_data[camel_case_field]:
                    if value_entry["value"] == field_value:
                        existing_value_entry = value_entry
                        break

                # Add new value entry or update existing one
                if existing_value_entry:
                    # Add this file instance to existing value
                    existing_value_entry["instances"].append({
                        "file": filename,
                        "confidence": confidence
                    })
                else:
                    # Create new value entry
                    aggregated_data[camel_case_field].append({
                        "value": field_value,
                        "instances": [{
                            "file": filename,
                            "confidence": confidence
                        }],
                        "occurrences": 1
                    })

        # Update occurrence counts and calculate weighted scores for all fields
        for field_name, values in aggregated_data.items():
            # Update occurrence counts
            for value_entry in values:
                value_entry["occurrences"] = len(value_entry["instances"])

            # Calculate total occurrences for this field
            total_occurrences = sum(value_entry["occurrences"] for value_entry in values)

            # Calculate weighted scores (proportion of total occurrences)
            for value_entry in values:
                value_entry["weightedScore"] = round(value_entry["occurrences"] / total_occurrences, 3) if total_occurrences > 0 else 0.0

        # Sort values by occurrence count (most common first)
        for field_name in aggregated_data:
            aggregated_data[field_name].sort(
                key=lambda x: (x["occurrences"], x["weightedScore"]),
                reverse=True
            )

        return {
            "aggregated_personal_data": aggregated_data,
            "summary": self._generate_aggregation_summary(aggregated_data, len(all_results)),
            "generated_at": datetime.now().isoformat()
        }

    def _generate_aggregation_summary(self, aggregated_data: Dict[str, List], total_files: int) -> Dict[str, Any]:
        """Generate summary statistics for the aggregated personal data."""
        summary = {
            "total_files_processed": total_files,
            "fields_with_data": len(aggregated_data),
            "total_unique_values": sum(len(values) for values in aggregated_data.values()),
            "inconsistencies_found": [],
            "most_common_values": {},
            "confidence_analysis": {}
        }

        # Analyze each field for inconsistencies and patterns
        for field_name, values in aggregated_data.items():
            if len(values) > 1:
                # Multiple values found for this field - potential inconsistency
                summary["inconsistencies_found"].append({
                    "field": field_name,
                    "value_count": len(values),
                    "values": [v["value"] for v in values[:3]]  # Show top 3 values
                })

            # Most common value for this field
            if values:
                most_common = values[0]  # Already sorted by occurrence
                summary["most_common_values"][field_name] = {
                    "value": most_common["value"],
                    "occurrences": most_common["occurrences"],
                    "weightedScore": most_common["weightedScore"]
                }

            # Confidence analysis
            all_confidences = []
            for value_entry in values:
                all_confidences.extend([inst["confidence"] for inst in value_entry["instances"]])

            if all_confidences:
                summary["confidence_analysis"][field_name] = {
                    "average_confidence": sum(all_confidences) / len(all_confidences),
                    "min_confidence": min(all_confidences),
                    "max_confidence": max(all_confidences),
                    "total_instances": len(all_confidences)
                }

        return summary

    def save_personal_data_aggregation(self, aggregation_data: Dict[str, Any], filename: str = None) -> str:
        """
        Save personal data aggregation to a JSON file.

        Args:
            aggregation_data: The aggregation data to save.
            filename: Output filename. If None, generates timestamp-based name.

        Returns:
            Path to the saved file.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"personal_data_aggregation_{timestamp}.json"

        output_path = self.output_dir / filename

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(aggregation_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Personal data aggregation saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Failed to save personal data aggregation: {str(e)}")
            raise