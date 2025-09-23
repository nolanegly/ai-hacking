#!/usr/bin/env python3
"""
Document Personal Data Extraction Agent

A Python AI agent that uses Claude to extract personal details from documents
for streamlining bank loan applications.
"""
import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent.core.agent import DocumentExtractionAgent
from agent.core.extractor import PersonalDataExtractor
from agent.utils.document_processor import DocumentProcessor
from agent.utils.output_manager import OutputManager


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('extraction_agent.log')
        ]
    )


def main():
    """Main entry point for the extraction agent."""
    parser = argparse.ArgumentParser(
        description="Extract personal data from documents using Claude AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input-dir ./documents --output-dir ./results
  %(prog)s --input-dir ./docs --output personal_data.json --verbose
  %(prog)s --input-dir ./files --include-metadata --validate
        """
    )

    parser.add_argument(
        "--input-dir", "-i",
        required=True,
        help="Directory containing documents to process"
    )

    parser.add_argument(
        "--output-dir", "-o",
        default="data/output",
        help="Output directory for results (default: data/output)"
    )

    parser.add_argument(
        "--output-file", "-f",
        help="Specific output filename (optional)"
    )

    parser.add_argument(
        "--api-key",
        help="Claude API key (overrides ANTHROPIC_API_KEY environment variable)"
    )

    parser.add_argument(
        "--model",
        default="claude-3-haiku-20240307",
        help="Claude model to use (default: claude-3-haiku-20240307)"
    )

    parser.add_argument(
        "--include-metadata",
        action="store_true",
        help="Include extraction metadata in output"
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Generate validation report"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Generate summary report"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Initialize components
        logger.info("Initializing Document Extraction Agent...")

        agent = DocumentExtractionAgent(api_key=args.api_key)
        agent.set_model_config(model=args.model)

        doc_processor = DocumentProcessor()
        extractor = PersonalDataExtractor(agent.client)
        output_manager = OutputManager(args.output_dir)

        # Process documents
        logger.info(f"Processing documents from: {args.input_dir}")
        documents = doc_processor.process_directory(args.input_dir)

        if not documents:
            logger.warning("No supported documents found in the input directory.")
            return

        logger.info(f"Found {len(documents)} documents to process")

        all_results = []

        # Process each document
        for doc in documents:
            logger.info(f"Processing: {doc['filename']}")

            try:
                # Extract data directly using Claude through the extractor
                formatted_results = extractor.extract_from_document(
                    doc['content'],
                    doc['filename']
                )

                all_results.extend(formatted_results)
                logger.info(f"Successfully processed {doc['filename']} - extracted {len(formatted_results)} fields")

            except Exception as e:
                logger.error(f"Failed to process {doc['filename']}: {str(e)}")
                continue

        if not all_results:
            logger.error("No data was successfully extracted from any documents.")
            return

        # Save results
        logger.info("Saving extraction results...")
        results_file = output_manager.save_extraction_results(
            all_results,
            args.output_file,
            args.include_metadata
        )

        print(f"✅ Extraction completed! Results saved to: {results_file}")

        # Generate validation report if requested
        if args.validate:
            logger.info("Generating validation report...")
            validation_data = extractor.validate_extraction(all_results)
            validation_file = output_manager.save_validation_report(validation_data)
            print(f"📊 Validation report saved to: {validation_file}")

            # Print validation summary
            print("\n📈 Extraction Summary:")
            print(f"  Total fields processed: {validation_data['total_fields']}")
            print(f"  Successfully extracted: {validation_data['found_fields']}")
            print(f"  Extraction rate: {validation_data['extraction_rate']:.1%}")
            print(f"  Average confidence: {validation_data['average_confidence']:.1%}")

        # Generate comprehensive summary if requested
        if args.summary:
            logger.info("Generating summary report...")
            summary_data = output_manager.create_summary_report(all_results)
            summary_file = output_manager.save_validation_report(summary_data, "summary_report.json")
            print(f"📋 Summary report saved to: {summary_file}")

            # Print key recommendations
            print("\n💡 Recommendations:")
            for recommendation in summary_data['recommendations']:
                print(f"  • {recommendation}")

        print(f"\n🎉 Processing complete! {len(all_results)} personal data fields extracted.")

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("\n⚠️  Process interrupted by user")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()