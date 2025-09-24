# Modular Document Data Extraction Agent

A Python AI agent that uses Claude to extract multiple types of data from documents. Features a modular pipeline architecture that can extract personal information, tabular data, and more. Perfect for streamlining loan applications, data processing, and document analysis workflows.

## Features

### **🔧 Modular Pipeline Architecture**
- **Multiple Extractors**: Personal data, tabular data, and easily extensible for more
- **Priority-based Processing**: Extractors run in order of importance
- **Smart Document Filtering**: Each extractor decides if it should process a document
- **Parallel Processing**: Multiple extraction types run on the same document

### **📊 Data Extraction Types**
- **Personal Data**: Names, addresses, SSN, employment info, etc. (12 standard fields)
- **Tabular Data**: Automatically detects and extracts tables with data type classification
- **Extensible**: Easy to add new extraction types via base extractor class

### **🎯 Advanced Features**
- **Multi-format Support**: Processes TXT, PDF, and DOCX files
- **Claude Integration**: Uses Anthropic's Claude API for intelligent extraction
- **Confidence Scoring**: Each extraction includes confidence levels
- **Structured Output**: JSON format with separate sections for each data type
- **Comprehensive Reporting**: Built-in validation and summary reports
- **Smart File Handling**: Prevents overwrites when files have same name but different extensions
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
python3 main.py --input-dir data/input --output-dir data/output
```

## Usage

### Basic Usage
```bash
python3 main.py --input-dir ./documents
```

### Advanced Usage
```bash
python3 main.py \
    --input-dir ./documents \
    --output-dir ./results \
    --output-file personal_data.json \
    --include-metadata \
    --validate \
    --summary \
    --aggregate \
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
- `--aggregate`: Generate personal data aggregation across all documents
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

Results are saved as JSON with separate sections for each extraction type:

```json
{
  "extraction_summary": {
    "total_files_processed": 1,
    "processed_at": "2024-01-15T10:30:00",
    "extraction_types": ["personalData", "tabularData"]
  },
  "personalData": [
    {
      "firstName": "John",
      "confidence": 0.9
    },
    {
      "lastName": "Smith",
      "confidence": 0.8
    },
    {
      "phoneNumber": "(555) 123-4567",
      "confidence": 0.9
    }
  ],
  "tabularData": [
    {
      "dataType": "financial_data",
      "headers": ["Account Type", "Balance", "Credit Limit"],
      "data": [
        ["Checking", "$5,000", "N/A"],
        ["Credit Card", "$2,500", "$10,000"]
      ],
      "confidence": 0.85,
      "description": "Financial accounts summary",
      "table_id": "table_1",
      "row_count": 2,
      "column_count": 3
    }
  ],
  "extraction_metadata": {
    "filename": "document.pdf",
    "processed_at": "2024-01-15T10:30:00",
    "extractors_run": [
      {
        "name": "personal_data_extractor",
        "type": "personal_data",
        "success": true,
        "confidence": 0.85
      },
      {
        "name": "tabular_data_extractor",
        "type": "tabular_data",
        "success": true,
        "confidence": 0.90
      }
    ],
    "success_count": 2,
    "error_count": 0
  }
}
```

### **Personal Data Format**
The personal data section uses camelCase field names and only includes fields where data was actually found:

**Field Mappings:**
- `First name` → `firstName`
- `Last name` → `lastName`
- `Phone number` → `phoneNumber`
- `Email address` → `emailAddress`
- `Home address` → `homeAddress`
- `Social Security Number` → `socialSecurityNumber`
- `Date of birth` → `dateOfBirth`
- `Employment status` → `employmentStatus`
- `Annual income` → `annualIncome`
- `Employer name` → `employerName`
- `Job title` → `jobTitle`
- `Middle name` → `middleName`

**Key Features:**
- Only includes fields with actual data (excludes "Not found" values)
- Each record is a separate object with the field name as the key
- Confidence score included for each field
- Clean, structured format for easy parsing

**Aggregation Features:**
- **Weighted Score**: Calculated as `occurrences / total_occurrences_for_field`
- **Instance Tracking**: Records which files contain each value
- **Occurrence Counting**: Shows frequency of each value across documents

### **Tabular Data Types**
The tabular data extractor automatically classifies tables into types such as:
- `financial_data` - Account balances, transactions, etc.
- `personal_info` - Contact lists, personal details
- `asset_list` - Property, investments, valuables
- `liability_list` - Debts, loans, obligations
- `income_statement` - Income sources and amounts
- `expense_report` - Monthly expenses, budgets
- `contact_list` - Names, phones, emails
- `employment_history` - Work experience
- And more...

## Personal Data Aggregation

The `--aggregate` flag generates a comprehensive cross-document analysis that identifies all values found for each personal data field and tracks which documents they appeared in. This is valuable for:

- **Inconsistency Detection**: Identifies when different documents contain different values for the same person
- **Data Validation**: Helps verify information accuracy across multiple sources
- **Completeness Assessment**: Shows which fields have data and which are missing

### Aggregation Output Format

```json
{
  "aggregated_personal_data": {
    "firstName": [
      {
        "value": "John",
        "instances": [
          {"file": "document1.pdf", "confidence": 0.9},
          {"file": "document2.txt", "confidence": 0.95}
        ],
        "occurrences": 2,
        "weightedScore": 0.667
      },
      {
        "value": "Jane",
        "instances": [
          {"file": "bank_statement.docx", "confidence": 0.92}
        ],
        "occurrences": 1,
        "weightedScore": 0.333
      }
    ],
    "phoneNumber": [
      {
        "value": "(555) 123-4567",
        "instances": [
          {"file": "document1.pdf", "confidence": 0.85}
        ],
        "occurrences": 1,
        "weightedScore": 0.5
      },
      {
        "value": "(555) 987-6543",
        "instances": [
          {"file": "document2.txt", "confidence": 0.9}
        ],
        "occurrences": 1,
        "weightedScore": 0.5
      }
    ]
  },
  "summary": {
    "fields_with_data": 5,
    "total_unique_values": 8,
    "inconsistencies_found": [
      {
        "field": "firstName",
        "value_count": 2,
        "values": ["John", "Jane"]
      },
      {
        "field": "phoneNumber",
        "value_count": 2,
        "values": ["(555) 123-4567", "(555) 987-6543"]
      }
    ],
    "most_common_values": {
      "firstName": {"value": "John", "occurrences": 2, "weightedScore": 0.667}
    }
  }
}
```

### Usage Example

```bash
# Process multiple documents and generate aggregation
python3 main.py --input-dir ./loan_documents --aggregate

# Console output will show:
# 📊 Personal Data Aggregation Summary:
#   Fields with data: 5
#   Total unique values: 8
#   ⚠️  Inconsistencies found in 2 fields:
#     • firstName: 2 different values ("John", "Jane")
#     • phoneNumber: 2 different values ("(555) 123-4567", "(555) 987-6543")
```

## Architecture

The agent follows a modular pipeline architecture:

```
src/
├── agent/
│   ├── core/
│   │   ├── agent.py              # Main DocumentExtractionAgent class
│   │   ├── base_extractor.py     # Abstract base class for extractors
│   │   └── extraction_pipeline.py # Pipeline coordinator
│   ├── extractors/
│   │   ├── personal_data_extractor.py  # Personal information extraction
│   │   └── tabular_data_extractor.py   # Table data extraction
│   ├── utils/
│   │   ├── document_processor.py       # Document reading utilities
│   │   └── output_manager.py           # Output handling
│   └── tools/                          # Agent tools directory
├── website/
│   ├── public/
│   │   ├── index.html            # Web interface for viewing aggregation data
│   │   └── script.js             # Frontend JavaScript for interactive display
│   ├── server.js                 # Node.js Express server
│   └── data/                     # Symlink to aggregation output files
```

## Web Interface

The project includes a web-based interface for viewing and analyzing personal data aggregation results. This interface provides an interactive way to explore the data extracted from documents and identify inconsistencies across multiple files.

### Features

- **Interactive Dropdowns**: Select personal data fields to view all found values
- **Occurrence Sorting**: Values are sorted by frequency and then alphabetically
- **File Source Tracking**: See which documents contain each value with confidence scores
- **Clickable File Links**: Direct links to open original source documents
- **Responsive Design**: Clean, modern interface optimized for data exploration

### Setup

1. **Start the web server**:
```bash
cd src/website
node server.js
```

2. **Access the interface**: Open http://localhost:3000 in your browser

### Requirements

- Node.js and npm
- Express.js (install with `npm install express`)

### Usage

1. **Generate aggregation data**:
```bash
python3 main.py --input-dir data/input --aggregate
```

2. **Start the web server** (from the `src/website` directory):
```bash
node server.js
```

3. **Explore the data**:
   - Use dropdowns to select different personal data fields
   - View all found values sorted by occurrence frequency
   - Click on values to see which files contain them
   - Click on file names to open the original documents

### File Opening Feature

The web interface includes a file opening feature that allows you to click on file names to open the original documents:

- **Cross-platform support**: Works on Windows, macOS, and Linux
- **Default application**: Opens files with the system's default application
- **Error handling**: Provides feedback if files cannot be opened
- **Security**: Only opens files within the designated data directories

### API Endpoints

- `GET /`: Main web interface
- `GET /data/personal_data_aggregation.json`: Aggregation data endpoint
- `POST /open-file`: Opens files using Node.js (file path in request body)

### File Structure

```
src/website/
├── public/
│   ├── index.html        # Main interface with embedded CSS
│   └── script.js         # Frontend logic and file interaction
├── server.js             # Express server with file opening capability
└── data/                 # Link to aggregation output files
```

## Adding Custom Extractors

To add new data extraction types:

1. Create a new extractor inheriting from `BaseExtractor`:

```python
from agent.core.base_extractor import BaseExtractor, ExtractionResult

class CustomDataExtractor(BaseExtractor):
    def __init__(self, claude_client):
        super().__init__(claude_client, "custom_extractor")

    @property
    def extraction_type(self) -> str:
        return "custom_data"

    @property
    def description(self) -> str:
        return "Extracts custom data from documents"

    def extract(self, document_content: str, filename: str = "") -> ExtractionResult:
        # Your extraction logic here
        raw_response = self._extract_with_claude(document_content)
        # Process and return ExtractionResult
        pass

    def _build_extraction_prompt(self, document_content: str) -> str:
        return "Your custom Claude prompt here..."
```

2. Add the extractor to the pipeline:

```python
from agent.core.extraction_pipeline import ExtractionPipeline

pipeline = ExtractionPipeline(claude_client)
pipeline.add_extractor(CustomDataExtractor(claude_client))
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

## File Handling

- **No Overwrites**: Files with same name but different extensions generate unique outputs
  - `document.pdf` → `document_pdf_results.json`
  - `document.txt` → `document_txt_results.json`
- **Batch Processing**: Multiple documents processed in sequence
- **Individual Outputs**: Each document gets its own results file

## Requirements

- Python 3.7+
- Valid Anthropic Claude API key
- Internet connection for Claude API calls

## License

This project is provided as-is for educational and development purposes.