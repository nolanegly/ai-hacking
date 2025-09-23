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
                formatted_record = {
                    "record": f"{record['field_name']}: {record['field_value']}",
                    "confidence": record.get("confidence", 0.0)
                }

                if include_metadata:
                    formatted_record["field_name"] = record["field_name"]
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