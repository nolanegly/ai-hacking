# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Setup and Installation:**
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-api-key-here"
```

**Running the Application:**
```bash
# Basic extraction
python3 main.py --input-dir data/input

# Full extraction with aggregation and reports
python3 main.py --input-dir data/input --summary --aggregate --verbose
```

**Testing:**
```bash
# Run all tests
python3 test_extraction.py
python3 test_modular_extraction.py
python3 test_personal_data_format.py
python3 test_file_collision.py
python3 test_personal_data_aggregation.py

# Test specific functionality
python3 test_personal_data_aggregation.py  # Test cross-document aggregation
python3 test_personal_data_format.py       # Test JSON output format
```

## Architecture Overview

This is a **modular document data extraction system** built around a pipeline architecture that coordinates multiple specialized extractors to process documents using Claude AI.

### Core Architecture Pattern

The system follows a **Pipeline + Strategy pattern** where:

1. **ExtractionPipeline** (`src/agent/core/extraction_pipeline.py`) orchestrates multiple extractors
2. **BaseExtractor** (`src/agent/core/base_extractor.py`) defines the interface for all extractors
3. **Concrete Extractors** (`src/agent/extractors/`) implement specific extraction logic
4. **OutputManager** (`src/agent/utils/output_manager.py`) handles result formatting and aggregation

### Key Components

**Pipeline Coordination:**
- `ExtractionPipeline` manages extractor registration, execution order (by priority), and result consolidation
- Each extractor can decide via `can_process()` whether it should run on a given document
- Results are collected into a unified output with metadata tracking

**Extractor System:**
- `BaseExtractor` provides common Claude integration and requires implementing `extract()` and `_build_extraction_prompt()`
- `PersonalDataExtractor` extracts 12 standard personal fields (firstName, lastName, etc.) with camelCase output
- `TabularDataExtractor` finds and classifies tables with dataType detection (financial_data, contact_list, etc.)

**Output Processing:**
- Results are structured as `{"personalData": [...], "tabularData": [...], "extraction_metadata": {...}}`
- Personal data uses camelCase field names and excludes "Not found" values
- Cross-document aggregation creates weighted scores based on occurrence frequency: `weightedScore = occurrences / total_occurrences_for_field`

### Data Flow

1. **Document Processing**: `DocumentProcessor` reads TXT/PDF/DOCX files from input directory
2. **Pipeline Execution**: `ExtractionPipeline` runs applicable extractors based on `can_process()` logic
3. **Result Formatting**: `OutputManager` converts extractor results to standardized JSON with camelCase fields
4. **Aggregation**: Optional cross-document analysis groups values by field and calculates weighted scores
5. **Output**: Separate JSON files per document plus optional aggregation report

### Extension Points

**Adding New Extractors:**
1. Inherit from `BaseExtractor`
2. Implement `extraction_type`, `description`, `extract()`, and `_build_extraction_prompt()`
3. Add to pipeline via `pipeline.add_extractor()`
4. Pipeline will automatically coordinate execution and output formatting

**Key Design Decisions:**
- Uses composition over inheritance for extractor management
- Claude prompts are isolated in each extractor's `_build_extraction_prompt()`
- All Claude communication goes through `BaseExtractor._extract_with_claude()`
- File collision prevention by including file extension in output names
- Confidence scoring and weighted scoring are separate concepts (confidence = extraction quality, weightedScore = frequency proportion)

## Important Implementation Notes

- Always use `python3` in commands and documentation
- Personal data output excludes "Not found" values and uses camelCase field names
- WeightedScore calculation: `occurrences / sum_of_all_occurrences_for_that_field`
- File output naming includes extension to prevent overwrites: `document_pdf_results.json`
- The system automatically registers default extractors in pipeline initialization