#!/usr/bin/env python3
"""
Test script for the modular extraction system.
"""
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_modular_extraction():
    """Test the modular extraction system without API calls."""
    try:
        # Test imports
        from agent.core.base_extractor import BaseExtractor, ExtractionResult
        from agent.extractors.personal_data_extractor import PersonalDataExtractor
        from agent.extractors.tabular_data_extractor import TabularDataExtractor
        from agent.core.extraction_pipeline import ExtractionPipeline

        print("✅ All modules imported successfully")

        # Test basic class instantiation with mock client
        class MockClient:
            def messages(self):
                pass

        mock_client = MockClient()

        # Test pipeline creation
        pipeline = ExtractionPipeline(mock_client)
        print("✅ Extraction pipeline created")

        # Test extractor listing
        extractors = pipeline.list_extractors()
        print(f"✅ Found {len(extractors)} extractors:")
        for extractor in extractors:
            print(f"  - {extractor['name']}: {extractor['description']}")

        # Test document compatibility checking
        sample_text = "Name: John Doe\nPhone: 555-1234\nTable: Item | Price\nApple | $1.50"

        for extractor in pipeline.extractors:
            can_process = extractor.can_process(sample_text)
            print(f"✅ {extractor.name} can process sample: {can_process}")

        # Test ExtractionResult
        result = ExtractionResult(
            data={"test": "data"},
            extractor_type="test",
            confidence=0.8
        )
        result_dict = result.to_dict()
        print(f"✅ ExtractionResult works: {result_dict['extractor_type']}")

        return True

    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_sample_documents():
    """Test that sample documents exist and are readable."""
    input_dir = Path("data/input")

    if not input_dir.exists():
        print("❌ Input directory doesn't exist")
        return False

    sample_files = list(input_dir.glob("*.txt"))
    print(f"✅ Found {len(sample_files)} sample documents:")

    for file_path in sample_files:
        try:
            content = file_path.read_text()
            print(f"  - {file_path.name}: {len(content)} characters")
        except Exception as e:
            print(f"  ❌ Failed to read {file_path.name}: {str(e)}")
            return False

    return True

if __name__ == "__main__":
    print("Testing Modular Document Extraction System...")
    print("-" * 50)

    success1 = test_modular_extraction()
    print()
    success2 = test_sample_documents()

    print("\n" + "=" * 50)

    if success1 and success2:
        print("🎉 All tests passed!")
        print("\nModular extraction system is ready!")
        print("\nNew Features:")
        print("• Pipeline architecture with multiple extractors")
        print("• Personal data extraction with confidence scores")
        print("• Tabular data extraction with dataType classification")
        print("• Modular design for easy extractor addition")
        print("\nNew Output Format:")
        print("• personalData: Contains field records with confidence")
        print("• tabularData: Contains arrays of table data with dataType")
        print("• extraction_metadata: Processing information and statistics")

        print("\nTo run with real data:")
        print("1. Set ANTHROPIC_API_KEY environment variable")
        print("2. Run: python3 main.py --input-dir data/input --summary")
    else:
        print("❌ Some tests failed. Please check the code.")
        sys.exit(1)