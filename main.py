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
from agent.core.extraction_pipeline import ExtractionPipeline
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
        logger.info("Initializing Document Extraction Agent with modular pipeline...")

        agent = DocumentExtractionAgent(api_key=args.api_key)
        agent.set_model_config(model=args.model)

        doc_processor = DocumentProcessor()
        extraction_pipeline = ExtractionPipeline(agent.client)
        extraction_pipeline.set_model_config_all(model=args.model)
        output_manager = OutputManager(args.output_dir)

        # Log available extractors
        extractors_info = extraction_pipeline.list_extractors()
        logger.info(f"Loaded {len(extractors_info)} extractors:")
        for extractor_info in extractors_info:
            logger.info(f"  - {extractor_info['name']}: {extractor_info['description']}")

        # Process documents
        logger.info(f"Processing documents from: {args.input_dir}")
        documents = doc_processor.process_directory(args.input_dir)

        if not documents:
            logger.warning("No supported documents found in the input directory.")
            return

        logger.info(f"Found {len(documents)} documents to process")

        all_results = {}

        # Process each document
        for doc in documents:
            logger.info(f"Processing: {doc['filename']}")

            try:
                # Extract data using the modular extraction pipeline
                extraction_results = extraction_pipeline.process_document(
                    doc['content'],
                    doc['filename']
                )

                all_results[doc['filename']] = extraction_results

                # Log summary
                summary = extraction_pipeline.get_extraction_summary(extraction_results)
                logger.info(f"Successfully processed {doc['filename']} - found {len(summary['extraction_types_found'])} data types")

            except Exception as e:
                logger.error(f"Failed to process {doc['filename']}: {str(e)}")
                continue

        if not all_results:
            logger.error("No data was successfully extracted from any documents.")
            return

        # Save results for each document
        logger.info("Saving extraction results...")
        saved_files = []

        for filename, results in all_results.items():
            # Create filename for this document's results - include extension to avoid conflicts
            file_path = Path(filename)
            base_name = f"{file_path.stem}_{file_path.suffix[1:]}" if file_path.suffix else file_path.stem
            output_filename = f"{base_name}_extraction_results.json" if not args.output_file else args.output_file

            results_file = output_manager.save_extraction_results(
                results,
                output_filename if len(all_results) == 1 else f"{base_name}_results.json",
                args.include_metadata
            )
            saved_files.append(results_file)

        print(f"✅ Extraction completed! Results saved to: {', '.join(saved_files)}")

        # Generate summary report for all documents
        if args.summary or args.validate:
            logger.info("Generating comprehensive summary...")

            overall_summary = {
                "total_documents_processed": len(all_results),
                "processing_summary": {},
                "extraction_types_found": set(),
                "average_confidence_by_type": {},
                "document_summaries": {}
            }

            for filename, results in all_results.items():
                summary = extraction_pipeline.get_extraction_summary(results)
                overall_summary["document_summaries"][filename] = summary
                overall_summary["extraction_types_found"].update(summary["extraction_types_found"])

            # Calculate averages
            all_confidences = []
            confidence_by_type = {}

            for filename, results in all_results.items():
                for key, value in results.items():
                    if key != "extraction_metadata" and isinstance(value, dict):
                        confidence = value.get("confidence", 0.0)
                        if confidence > 0:
                            all_confidences.append(confidence)
                            if key not in confidence_by_type:
                                confidence_by_type[key] = []
                            confidence_by_type[key].append(confidence)

            overall_summary["overall_average_confidence"] = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            overall_summary["extraction_types_found"] = list(overall_summary["extraction_types_found"])

            for ext_type, confidences in confidence_by_type.items():
                overall_summary["average_confidence_by_type"][ext_type] = sum(confidences) / len(confidences)

            # Save summary report
            summary_file = output_manager.save_validation_report(overall_summary, "comprehensive_summary.json")
            print(f"📋 Summary report saved to: {summary_file}")

            # Print key statistics
            print(f"\n📈 Overall Summary:")
            print(f"  Documents processed: {overall_summary['total_documents_processed']}")
            print(f"  Extraction types found: {', '.join(overall_summary['extraction_types_found'])}")
            print(f"  Overall average confidence: {overall_summary['overall_average_confidence']:.1%}")

        total_extractions = sum(len(results.get('extraction_metadata', {}).get('extractors_run', [])) for results in all_results.values())
        print(f"\n🎉 Processing complete! {total_extractions} total extractions performed across all documents.")

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("\n⚠️  Process interrupted by user")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()