"""
Document Personal Data Extraction Agent

A modular Python AI agent that uses Claude to extract personal details
from documents for streamlining bank loan applications.
"""

from .core.agent import DocumentExtractionAgent, Tool
from .core.extractor import PersonalDataExtractor
from .utils.document_processor import DocumentProcessor
from .utils.output_manager import OutputManager

__version__ = "1.0.0"
__author__ = "AI Document Processing Team"

__all__ = [
    "DocumentExtractionAgent",
    "Tool",
    "PersonalDataExtractor",
    "DocumentProcessor",
    "OutputManager"
]