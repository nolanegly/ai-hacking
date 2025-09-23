#!/usr/bin/env python3
"""
Test script to verify the new personalData output format.
"""
import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_camel_case_conversion():
    """Test the camelCase conversion function."""
    from agent.utils.output_manager import OutputManager

    output_manager = OutputManager("test_output")

    test_cases = [
        ("First name", "firstName"),
        ("Last name", "lastName"),
        ("Social Security Number", "socialSecurityNumber"),
        ("Phone number", "phoneNumber"),
        ("Email address", "emailAddress"),
        ("Home address", "homeAddress"),
        ("Date of birth", "dateOfBirth"),
        ("Employment status", "employmentStatus"),
        ("Annual income", "annualIncome"),
        ("Employer name", "employerName"),
        ("Job title", "jobTitle"),
        ("Middle name", "middleName"),
        ("Custom field name", "customFieldName"),  # Generic conversion test
    ]

    print("Testing camelCase conversion:")
    print("-" * 40)

    success = True
    for input_field, expected_output in test_cases:
        actual_output = output_manager._convert_to_camel_case(input_field)
        test_passed = actual_output == expected_output
        status = "✅" if test_passed else "❌"

        print(f"{status} '{input_field}' -> '{actual_output}'")

        if not test_passed:
            print(f"   Expected: '{expected_output}'")
            success = False

    return success

def test_personal_data_formatting():
    """Test the new personal data formatting."""
    from agent.utils.output_manager import OutputManager

    # Create mock extraction results in the pipeline format
    mock_results = {
        "personalData": {
            "data": [
                {"field_name": "First name", "field_value": "Jane", "confidence": 0.9},
                {"field_name": "Last name", "field_value": "Goodall", "confidence": 0.9},
                {"field_name": "Middle name", "field_value": "Not found", "confidence": 0.0},
                {"field_name": "Phone number", "field_value": "(555) 987-7777", "confidence": 0.8},
                {"field_name": "Email address", "field_value": "Not found", "confidence": 0.0},
                {"field_name": "Home address", "field_value": "432 Elm St, Othertown, USA 67890", "confidence": 0.8},
                {"field_name": "Annual income", "field_value": "Not found", "confidence": 0.0}
            ],
            "extracted_at": "2024-01-15T10:30:00"
        },
        "extraction_metadata": {
            "filename": "test.txt"
        }
    }

    output_manager = OutputManager("test_output")
    formatted_output = output_manager._format_results(mock_results, include_metadata=False)

    print("\nTesting personal data formatting:")
    print("-" * 40)

    # Check that personalData exists
    if "personalData" not in formatted_output:
        print("❌ personalData section missing from output")
        return False

    personal_data = formatted_output["personalData"]

    # Check that only found fields are included (should exclude "Not found" values)
    expected_fields = ["firstName", "lastName", "phoneNumber", "homeAddress"]
    actual_fields = [list(record.keys())[0] for record in personal_data]  # Get first key (field name)

    print(f"Expected fields: {expected_fields}")
    print(f"Actual fields: {actual_fields}")

    # Verify structure
    expected_structure_checks = [
        (len(personal_data) == 4, f"Should have 4 records, got {len(personal_data)}"),
        (all("confidence" in record for record in personal_data), "All records should have confidence"),
        (personal_data[0]["firstName"] == "Jane", f"First name should be 'Jane', got '{personal_data[0].get('firstName', 'MISSING')}'"),
        (personal_data[1]["lastName"] == "Goodall", f"Last name should be 'Goodall', got '{personal_data[1].get('lastName', 'MISSING')}'"),
        (personal_data[0]["confidence"] == 0.9, f"First record confidence should be 0.9, got {personal_data[0]['confidence']}"),
    ]

    success = True
    for check, message in expected_structure_checks:
        status = "✅" if check else "❌"
        print(f"{status} {message}")
        if not check:
            success = False

    # Print formatted output for inspection
    print("\nFormatted output sample:")
    print(json.dumps(personal_data, indent=2))

    return success

if __name__ == "__main__":
    print("Testing Personal Data Format Changes...")
    print("=" * 50)

    success1 = test_camel_case_conversion()
    print()
    success2 = test_personal_data_formatting()

    print("\n" + "=" * 50)

    if success1 and success2:
        print("🎉 Personal data formatting tests passed!")
        print("\nNew Format Features:")
        print("• Only includes fields with actual data (excludes 'Not found')")
        print("• Uses camelCase field names (firstName, lastName, etc.)")
        print("• Each record is a separate object with field name as key")
        print("• Maintains confidence scores")

        print("\nExample output:")
        print('''
{
  "personalData": [
    {"firstName": "Jane", "confidence": 0.9},
    {"lastName": "Goodall", "confidence": 0.9},
    {"phoneNumber": "(555) 987-7777", "confidence": 0.8}
  ]
}''')
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)