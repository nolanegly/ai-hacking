"""
Extraction pipeline for coordinating multiple extractors.
"""
from typing import List, Dict, Any, Optional, Type
import logging
from datetime import datetime
import anthropic

from .base_extractor import BaseExtractor, ExtractionResult
from ..extractors.personal_data_extractor import PersonalDataExtractor
from ..extractors.tabular_data_extractor import TabularDataExtractor


class ExtractionPipeline:
    """Coordinates multiple extractors to process documents comprehensively."""

    def __init__(self, claude_client: anthropic.Anthropic):
        """
        Initialize the extraction pipeline.

        Args:
            claude_client: Anthropic Claude client instance.
        """
        self.claude_client = claude_client
        self.extractors: List[BaseExtractor] = []
        self.logger = logging.getLogger(__name__)

        # Register default extractors
        self._register_default_extractors()

    def _register_default_extractors(self):
        """Register the default set of extractors."""
        self.add_extractor(PersonalDataExtractor(self.claude_client))
        self.add_extractor(TabularDataExtractor(self.claude_client))

    def add_extractor(self, extractor: BaseExtractor):
        """
        Add an extractor to the pipeline.

        Args:
            extractor: The extractor instance to add.
        """
        self.extractors.append(extractor)
        self.logger.info(f"Added extractor: {extractor.name} ({extractor.extraction_type})")

    def remove_extractor(self, extractor_name: str):
        """
        Remove an extractor from the pipeline.

        Args:
            extractor_name: Name of the extractor to remove.
        """
        self.extractors = [e for e in self.extractors if e.name != extractor_name]
        self.logger.info(f"Removed extractor: {extractor_name}")

    def list_extractors(self) -> List[Dict[str, str]]:
        """Get information about all registered extractors."""
        return [
            {
                "name": extractor.name,
                "type": extractor.extraction_type,
                "description": extractor.description,
                "priority": extractor.get_priority()
            }
            for extractor in self.extractors
        ]

    def process_document(self, document_content: str, filename: str = "",
                        enabled_extractors: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Process a document through the extraction pipeline.

        Args:
            document_content: The document text to process.
            filename: Source filename for reference.
            enabled_extractors: List of extractor names to run. If None, runs all applicable extractors.

        Returns:
            Dictionary containing all extraction results.
        """
        start_time = datetime.now()
        self.logger.info(f"Starting extraction pipeline for: {filename}")

        # Filter extractors based on enabled list and document compatibility
        active_extractors = self._get_active_extractors(document_content, enabled_extractors)

        # Sort extractors by priority
        active_extractors.sort(key=lambda x: x.get_priority())

        results = {}
        extraction_metadata = {
            "filename": filename,
            "processed_at": start_time.isoformat(),
            "extractors_run": [],
            "total_processing_time": 0.0,
            "success_count": 0,
            "error_count": 0
        }

        # Run each extractor
        for extractor in active_extractors:
            extractor_start = datetime.now()

            try:
                self.logger.info(f"Running extractor: {extractor.name}")
                result = extractor.extract(document_content, filename)

                # Store result based on extraction type
                if extractor.extraction_type == "personal_data":
                    results["personalData"] = result.to_dict()
                elif extractor.extraction_type == "tabular_data":
                    results["tabularData"] = result.to_dict()
                else:
                    results[extractor.extraction_type] = result.to_dict()

                extraction_metadata["extractors_run"].append({
                    "name": extractor.name,
                    "type": extractor.extraction_type,
                    "success": True,
                    "processing_time": (datetime.now() - extractor_start).total_seconds(),
                    "confidence": result.confidence
                })
                extraction_metadata["success_count"] += 1

                self.logger.info(f"Completed extractor: {extractor.name} (confidence: {result.confidence:.2f})")

            except Exception as e:
                self.logger.error(f"Extractor {extractor.name} failed: {str(e)}")

                extraction_metadata["extractors_run"].append({
                    "name": extractor.name,
                    "type": extractor.extraction_type,
                    "success": False,
                    "error": str(e),
                    "processing_time": (datetime.now() - extractor_start).total_seconds()
                })
                extraction_metadata["error_count"] += 1

        # Calculate total processing time
        extraction_metadata["total_processing_time"] = (datetime.now() - start_time).total_seconds()
        extraction_metadata["completed_at"] = datetime.now().isoformat()

        # Add metadata to results
        results["extraction_metadata"] = extraction_metadata

        self.logger.info(f"Pipeline completed for {filename}: {extraction_metadata['success_count']} successes, {extraction_metadata['error_count']} errors")

        return results

    def _get_active_extractors(self, document_content: str,
                             enabled_extractors: Optional[List[str]] = None) -> List[BaseExtractor]:
        """
        Get list of extractors that should process this document.

        Args:
            document_content: The document content to evaluate.
            enabled_extractors: List of specific extractors to enable.

        Returns:
            List of extractors to run.
        """
        active = []

        for extractor in self.extractors:
            # Check if extractor is in enabled list (if provided)
            if enabled_extractors and extractor.name not in enabled_extractors:
                continue

            # Check if extractor can process this document
            if extractor.can_process(document_content):
                active.append(extractor)
                self.logger.debug(f"Extractor {extractor.name} can process document")
            else:
                self.logger.debug(f"Extractor {extractor.name} skipping document")

        return active

    def get_extraction_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of extraction results.

        Args:
            results: The extraction results dictionary.

        Returns:
            Summary information about the extraction.
        """
        metadata = results.get("extraction_metadata", {})

        summary = {
            "total_extractors": len(metadata.get("extractors_run", [])),
            "successful_extractors": metadata.get("success_count", 0),
            "failed_extractors": metadata.get("error_count", 0),
            "processing_time": metadata.get("total_processing_time", 0.0),
            "extraction_types_found": []
        }

        # Check what types of data were extracted
        for key, value in results.items():
            if key != "extraction_metadata" and isinstance(value, dict):
                data = value.get("data", [])
                if data:  # Only include if data was actually found
                    summary["extraction_types_found"].append(key)

        # Calculate average confidence
        confidences = []
        for key, value in results.items():
            if key != "extraction_metadata" and isinstance(value, dict):
                confidence = value.get("confidence", 0.0)
                if confidence > 0:
                    confidences.append(confidence)

        summary["average_confidence"] = sum(confidences) / len(confidences) if confidences else 0.0

        return summary

    def set_model_config_all(self, model: str = None, max_tokens: int = None, temperature: float = None):
        """Update model configuration for all extractors."""
        for extractor in self.extractors:
            extractor.set_model_config(model, max_tokens, temperature)