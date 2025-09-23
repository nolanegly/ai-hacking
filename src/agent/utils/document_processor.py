"""
Document processing utilities for handling various file formats.
"""
import os
import mimetypes
from pathlib import Path
from typing import List, Dict, Optional
import logging


class DocumentProcessor:
    """Handles reading and processing various document formats."""

    SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.docx', '.doc'}

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_directory(self, directory_path: str) -> List[Dict[str, str]]:
        """
        Process all supported documents in a directory.

        Args:
            directory_path: Path to the directory containing documents.

        Returns:
            List of dictionaries containing file info and content.
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        documents = []
        for file_path in directory.iterdir():
            if file_path.is_file() and self._is_supported_file(file_path):
                try:
                    content = self.read_document(str(file_path))
                    documents.append({
                        'filename': file_path.name,
                        'filepath': str(file_path),
                        'content': content,
                        'size': file_path.stat().st_size
                    })
                    self.logger.info(f"Successfully processed: {file_path.name}")
                except Exception as e:
                    self.logger.error(f"Failed to process {file_path.name}: {str(e)}")
                    continue

        return documents

    def read_document(self, file_path: str) -> str:
        """
        Read content from a document file.

        Args:
            file_path: Path to the document file.

        Returns:
            Text content of the document.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = file_path.suffix.lower()

        if extension == '.txt':
            return self._read_text_file(file_path)
        elif extension == '.pdf':
            return self._read_pdf_file(file_path)
        elif extension in ['.docx', '.doc']:
            return self._read_word_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")

    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if file format is supported."""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def _read_text_file(self, file_path: Path) -> str:
        """Read content from a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()

    def _read_pdf_file(self, file_path: Path) -> str:
        """Read content from a PDF file."""
        try:
            import PyPDF2
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF processing. Install with: pip install PyPDF2")

        content = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                content += page.extract_text() + "\n"

        return content.strip()

    def _read_word_file(self, file_path: Path) -> str:
        """Read content from a Word document."""
        try:
            import docx
        except ImportError:
            raise ImportError("python-docx is required for Word processing. Install with: pip install python-docx")

        doc = docx.Document(str(file_path))
        content = ""
        for paragraph in doc.paragraphs:
            content += paragraph.text + "\n"

        return content.strip()

    def get_file_info(self, file_path: str) -> Dict[str, any]:
        """Get metadata information about a file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = file_path.stat()
        return {
            'filename': file_path.name,
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'extension': file_path.suffix,
            'mime_type': mimetypes.guess_type(str(file_path))[0],
            'is_supported': self._is_supported_file(file_path)
        }