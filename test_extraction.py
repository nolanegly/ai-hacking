#!/usr/bin/env python3
"""
Simple test script to verify the extraction functionality works.
"""
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_functionality():
    """Test that the extractor can be initialized and basic methods work."""
    try:
        from agent.core.extractor import PersonalDataExtractor
        import anthropic

        # Test that we can initialize with a mock client
        class MockClient:
            def messages(self):
                pass

        # Test initialization
        mock_client = MockClient()
        extractor = PersonalDataExtractor(mock_client)

        print("✅ PersonalDataExtractor initialized successfully")

        # Test that standard fields are defined
        print(f"✅ Standard fields defined: {len(extractor.STANDARD_FIELDS)} fields")

        # Test empty records creation
        empty_records = extractor._create_empty_records("test.txt")
        print(f"✅ Empty records created: {len(empty_records)} records")

        # Test value cleaning
        cleaned_value = extractor._clean_value("  John Doe  ")
        print(f"✅ Value cleaning works: '{cleaned_value}'")

        return True

    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Document Personal Data Extraction Agent...")
    print("-" * 50)

    success = test_basic_functionality()

    if success:
        print("\n🎉 All basic tests passed!")
        print("\nTo run the full extraction:")
        print("1. Set ANTHROPIC_API_KEY environment variable")
        print("2. Place documents in data/input/ directory")
        print("3. Run: python3 main.py --input-dir data/input")
    else:
        print("\n❌ Some tests failed. Please check the code.")
        sys.exit(1)