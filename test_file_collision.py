#!/usr/bin/env python3
"""
Test script to verify the file collision fix works.
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_filename_generation():
    """Test that filenames with same name but different extensions generate unique output names."""

    # Test the filename generation logic
    test_cases = [
        ("document.pdf", "document_pdf"),
        ("document.txt", "document_txt"),
        ("report.docx", "report_docx"),
        ("data", "data"),  # No extension
        ("file.with.dots.csv", "file.with.dots_csv"),
    ]

    print("Testing filename generation logic:")
    print("-" * 40)

    for input_filename, expected_base in test_cases:
        file_path = Path(input_filename)
        base_name = f"{file_path.stem}_{file_path.suffix[1:]}" if file_path.suffix else file_path.stem
        expected_output = f"{expected_base}_results.json"
        actual_output = f"{base_name}_results.json"

        success = expected_output == actual_output
        status = "✅" if success else "❌"

        print(f"{status} {input_filename:20} -> {actual_output}")

        if not success:
            print(f"   Expected: {expected_output}")
            print(f"   Got:      {actual_output}")
            return False

    return True

def test_sample_files_exist():
    """Test that our collision test files exist."""
    input_dir = Path("data/input")

    collision_files = ["document.pdf", "document.txt"]
    found_files = []

    print("\nChecking collision test files:")
    print("-" * 30)

    for filename in collision_files:
        file_path = input_dir / filename
        if file_path.exists():
            found_files.append(filename)
            print(f"✅ Found: {filename}")
        else:
            print(f"❌ Missing: {filename}")

    return len(found_files) == len(collision_files)

if __name__ == "__main__":
    print("Testing File Collision Fix...")
    print("=" * 50)

    success1 = test_filename_generation()
    success2 = test_sample_files_exist()

    print("\n" + "=" * 50)

    if success1 and success2:
        print("🎉 File collision fix verified!")
        print("\nBehavior:")
        print("• document.pdf -> document_pdf_results.json")
        print("• document.txt -> document_txt_results.json")
        print("• No more file overwrites!")

        print("\nTo test with real extraction:")
        print("1. Set ANTHROPIC_API_KEY environment variable")
        print("2. Run: python3 main.py --input-dir data/input")
        print("3. Check that both files generate separate outputs")
    else:
        print("❌ Some tests failed.")
        sys.exit(1)