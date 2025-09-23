# Document Personal Data Extraction Agent

A Python AI agent that uses Claude to extract personal details from documents for streamlining bank loan applications. The agent processes documents from a specified directory, extracts personal information using Claude's AI capabilities, and outputs structured JSON data.

## Features

- **Multi-format Support**: Processes TXT, PDF, and DOCX files
- **Modular Architecture**: Easily extensible with custom tools
- **Claude Integration**: Uses Anthropic's Claude API for intelligent extraction
- **Structured Output**: JSON format with field name/value pairs
- **Validation & Reporting**: Built-in confidence scoring and validation reports
- **CLI Interface**: Command-line interface for easy automation

## Installation

1. Clone or download this repository
2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Claude API key:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Quick Start

1. Place your documents in an input directory (e.g., `data/input/`)
2. Run the extraction agent:
```bash
python main.py --input-dir data/input --output-dir data/output
```

## Usage

### Basic Usage
```bash
python main.py --input-dir ./documents
```

### Advanced Usage
```bash
python main.py \
    --input-dir ./documents \
    --output-dir ./results \
    --output-file personal_data.json \
    --include-metadata \
    --validate \
    --summary \
    --verbose
```

### Command Line Options

- `--input-dir, -i`: Directory containing documents to process (required)
- `--output-dir, -o`: Output directory for results (default: data/output)
- `--output-file, -f`: Specific output filename (optional)
- `--api-key`: Claude API key (overrides environment variable)
- `--model`: Claude model to use (default: claude-3-haiku-20240307)
- `--include-metadata`: Include extraction metadata in output
- `--validate`: Generate validation report
- `--summary`: Generate comprehensive summary report
- `--verbose, -v`: Enable verbose logging

## Extracted Fields

The agent extracts the following personal data fields:

- First name
- Last name
- Middle name
- Date of birth
- Social Security Number
- Phone number
- Email address
- Home address
- Employment status
- Annual income
- Employer name
- Job title

## Output Format

Results are saved as JSON with the following structure:

```json
{
  "extraction_summary": {
    "total_files_processed": 1,
    "total_records": 12,
    "processed_at": "2024-01-15T10:30:00"
  },
  "results": {
    "document1.pdf": [
      {
        "record": "First name: John",
        "confidence": 0.9,
        "extracted_at": "2024-01-15T10:30:00"
      },
      {
        "record": "Last name: Smith",
        "confidence": 0.9,
        "extracted_at": "2024-01-15T10:30:00"
      }
    ]
  }
}
```

## Architecture

The agent follows a modular architecture:

```
src/
├── agent/
│   ├── core/
│   │   ├── agent.py          # Main DocumentExtractionAgent class
│   │   └── extractor.py      # PersonalDataExtractor logic
│   ├── utils/
│   │   ├── document_processor.py  # Document reading utilities
│   │   └── output_manager.py      # Output handling
│   └── tools/                     # Extensible tools directory
```

## Adding Custom Tools

To add custom tools to the agent:

1. Create a new tool class inheriting from `Tool`:

```python
from agent.core.agent import Tool

class CustomTool(Tool):
    @property
    def name(self) -> str:
        return "custom_tool"

    @property
    def description(self) -> str:
        return "Description of what this tool does"

    def execute(self, *args, **kwargs):
        # Tool implementation
        pass
```

2. Add the tool to your agent:

```python
agent = DocumentExtractionAgent()
agent.add_tool(CustomTool())
```

## Security & Privacy

- API keys are read from environment variables
- No data is stored beyond the local output files
- All document processing happens locally except for the Claude API calls
- Consider data privacy regulations when processing personal information

## Logging

The agent creates logs in `extraction_agent.log` with detailed processing information. Use `--verbose` flag for debug-level logging.

## Error Handling

- Individual document processing errors don't stop the entire batch
- Comprehensive error logging for troubleshooting
- Graceful handling of unsupported file formats

## Requirements

- Python 3.7+
- Valid Anthropic Claude API key
- Internet connection for Claude API calls

## License

This project is provided as-is for educational and development purposes.