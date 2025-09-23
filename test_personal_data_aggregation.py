#!/usr/bin/env python3
"""
Test script to verify the personal data aggregation functionality.
"""
import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_personal_data_aggregation():
    """Test the personal data aggregation functionality."""
    from agent.utils.output_manager import OutputManager

    # Create mock extraction results from multiple documents
    mock_results = {
        "document1.pdf": {
            "personalData": {
                "data": [
                    {"field_name": "First name", "field_value": "John", "confidence": 0.9},
                    {"field_name": "Last name", "field_value": "Smith", "confidence": 0.8},
                    {"field_name": "Phone number", "field_value": "(555) 123-4567", "confidence": 0.7},
                    {"field_name": "Email address", "field_value": "Not found", "confidence": 0.0}
                ]
            }
        },
        "document2.txt": {
            "personalData": {
                "data": [
                    {"field_name": "First name", "field_value": "John", "confidence": 0.95},  # Same value
                    {"field_name": "Last name", "field_value": "Johnson", "confidence": 0.85},  # Different value
                    {"field_name": "Phone number", "field_value": "(555) 987-6543", "confidence": 0.9},  # Different value
                    {"field_name": "Email address", "field_value": "john@example.com", "confidence": 0.8}
                ]
            }
        },
        "document3.docx": {
            "personalData": {
                "data": [
                    {"field_name": "First name", "field_value": "Jane", "confidence": 0.92},  # Different value
                    {"field_name": "Last name", "field_value": "Smith", "confidence": 0.88},  # Same as doc1
                    {"field_name": "Annual income", "field_value": "$75,000", "confidence": 0.85}
                ]
            }
        }
    }

    output_manager = OutputManager("test_output")
    aggregation_data = output_manager.create_personal_data_aggregation(mock_results)

    print("Testing Personal Data Aggregation:")
    print("-" * 50)

    # Test basic structure
    required_keys = ["aggregated_personal_data", "summary", "generated_at"]
    for key in required_keys:
        if key in aggregation_data:
            print(f"✅ Has required key: {key}")
        else:
            print(f"❌ Missing required key: {key}")
            return False

    aggregated = aggregation_data["aggregated_personal_data"]
    summary = aggregation_data["summary"]

    # Test field aggregation
    expected_fields = ["firstName", "lastName", "phoneNumber", "emailAddress", "annualIncome"]

    print(f"\nExpected fields: {expected_fields}")
    print(f"Actual fields: {list(aggregated.keys())}")

    for field in expected_fields:
        if field in aggregated:
            print(f"✅ Field present: {field}")
        else:
            print(f"❌ Field missing: {field}")
            return False

    # Test firstName aggregation (should have 2 values: John, Jane)
    first_name_data = aggregated.get("firstName", [])
    print(f"\nFirst name aggregation:")
    print(f"  Number of unique values: {len(first_name_data)}")

    expected_first_names = {"John", "Jane"}
    actual_first_names = {entry["value"] for entry in first_name_data}

    if actual_first_names == expected_first_names:
        print(f"✅ Correct firstName values: {actual_first_names}")
    else:
        print(f"❌ Wrong firstName values. Expected: {expected_first_names}, Got: {actual_first_names}")
        return False

    # Test John's instances (should appear in document1.pdf and document2.txt)
    john_entry = next((entry for entry in first_name_data if entry["value"] == "John"), None)
    if john_entry:
        john_files = {inst["file"] for inst in john_entry["instances"]}
        expected_john_files = {"document1.pdf", "document2.txt"}

        if john_files == expected_john_files:
            print(f"✅ John appears in correct files: {john_files}")
        else:
            print(f"❌ John in wrong files. Expected: {expected_john_files}, Got: {john_files}")
            return False

        # Test occurrence count
        if john_entry["occurrences"] == 2:
            print(f"✅ John occurrence count correct: {john_entry['occurrences']}")
        else:
            print(f"❌ John occurrence count wrong: {john_entry['occurrences']}")
            return False

        # Test weighted score (John: 2 occurrences, Jane: 1 occurrence, total: 3)
        # John's weighted score should be 2/3 = 0.667
        expected_weighted_score = round(2/3, 3)
        if abs(john_entry["weightedScore"] - expected_weighted_score) < 0.001:
            print(f"✅ John weighted score correct: {john_entry['weightedScore']}")
        else:
            print(f"❌ John weighted score wrong. Expected: {expected_weighted_score}, Got: {john_entry['weightedScore']}")
            return False
    else:
        print("❌ John entry not found in aggregation")
        return False

    # Test Jane's weighted score (1/3 = 0.333)
    jane_entry = next((entry for entry in first_name_data if entry["value"] == "Jane"), None)
    if jane_entry:
        expected_jane_weighted_score = round(1/3, 3)
        if abs(jane_entry["weightedScore"] - expected_jane_weighted_score) < 0.001:
            print(f"✅ Jane weighted score correct: {jane_entry['weightedScore']}")
        else:
            print(f"❌ Jane weighted score wrong. Expected: {expected_jane_weighted_score}, Got: {jane_entry['weightedScore']}")
            return False
    else:
        print("❌ Jane entry not found in aggregation")
        return False

    # Test summary statistics
    print(f"\nSummary validation:")
    print(f"  Total files processed: {summary['total_files_processed']}")
    print(f"  Fields with data: {summary['fields_with_data']}")
    print(f"  Inconsistencies found: {len(summary['inconsistencies_found'])}")

    # Should have inconsistencies in lastName and phoneNumber
    inconsistent_fields = {inc["field"] for inc in summary["inconsistencies_found"]}
    expected_inconsistent = {"lastName", "phoneNumber"}

    if inconsistent_fields.issuperset(expected_inconsistent):
        print(f"✅ Detected expected inconsistencies: {inconsistent_fields}")
    else:
        print(f"❌ Missing expected inconsistencies. Expected: {expected_inconsistent}, Got: {inconsistent_fields}")
        return False

    # Print sample output
    print(f"\nSample aggregated data (firstName):")
    print(json.dumps(first_name_data, indent=2))

    return True

def test_edge_cases():
    """Test edge cases for aggregation."""
    from agent.utils.output_manager import OutputManager

    # Test with no personal data
    empty_results = {
        "document1.pdf": {
            "tabularData": {"data": []}
        }
    }

    output_manager = OutputManager("test_output")
    aggregation_data = output_manager.create_personal_data_aggregation(empty_results)

    print("\nTesting edge cases:")
    print("-" * 30)

    if len(aggregation_data["aggregated_personal_data"]) == 0:
        print("✅ Handles empty personal data correctly")
    else:
        print("❌ Should return empty aggregation for no personal data")
        return False

    return True

if __name__ == "__main__":
    print("Testing Personal Data Aggregation System...")
    print("=" * 60)

    success1 = test_personal_data_aggregation()
    print()
    success2 = test_edge_cases()

    print("\n" + "=" * 60)

    if success1 and success2:
        print("🎉 Personal data aggregation tests passed!")
        print("\nFeatures tested:")
        print("• Cross-document value aggregation")
        print("• File instance tracking")
        print("• Inconsistency detection")
        print("• Weighted score calculation")
        print("• Summary statistics generation")

        print("\nExample aggregation output:")
        print('''{
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
        {"file": "document3.docx", "confidence": 0.92}
      ],
      "occurrences": 1,
      "weightedScore": 0.333
    }
  ]
}''')
    else:
        print("❌ Some tests failed.")
        sys.exit(1)