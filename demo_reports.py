"""
Report Generation Demonstration

Shows all report formats and capabilities.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.validator.validation_engine import ValidationEngine
from src.reporting.report_generator import ReportGenerator


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def demo_text_report():
    """Demonstrate text report format."""
    print_header("TEXT REPORT FORMAT")

    # Validate a document
    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_850_invalid.txt", "850")

    # Generate text report
    generator = ReportGenerator(result)
    text_report = generator.generate_text_report()

    print(text_report)


def demo_dashboard():
    """Demonstrate dashboard format."""
    print_header("DASHBOARD FORMAT")

    # Validate with Walmart rules
    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_850_valid.txt", "850", "walmart")

    # Generate dashboard
    generator = ReportGenerator(result)
    dashboard = generator.generate_dashboard()

    print(dashboard)


def demo_json_export():
    """Demonstrate JSON export."""
    print_header("JSON EXPORT")

    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_850_invalid.txt", "850")

    generator = ReportGenerator(result)
    json_report = generator.generate_json_report()

    # Show first 50 lines
    lines = json_report.split('\n')
    print("\n  First 50 lines of JSON export:\n")
    for line in lines[:50]:
        print(f"  {line}")

    if len(lines) > 50:
        print(f"\n  ... ({len(lines) - 50} more lines)")


def demo_csv_export():
    """Demonstrate CSV export."""
    print_header("CSV EXPORT")

    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_850_invalid.txt", "850")

    generator = ReportGenerator(result)
    csv_report = generator.generate_csv_report()

    print("\n  CSV format (issues as spreadsheet):\n")
    print(csv_report)


def demo_save_reports():
    """Demonstrate saving reports to files."""
    print_header("SAVING REPORTS TO FILES")

    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_850_valid.txt", "850", "walmart")

    generator = ReportGenerator(result)

    # Save all formats
    files = generator.save_all_formats("output", "walmart_validation")

    print("\n  Reports saved:\n")
    for format_name, file_path in files.items():
        print(f"    {format_name:12} → {file_path}")

    print("\n  ✓ All reports saved successfully")


def demo_compliant_document():
    """Demonstrate reporting for compliant document."""
    print_header("COMPLIANT DOCUMENT REPORT")

    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_856_valid.txt", "856")

    generator = ReportGenerator(result)

    # Print dashboard for compliant doc
    generator.print_dashboard()


def demo_comparison():
    """Compare validation results across retailers."""
    print_header("RETAILER COMPARISON")

    engine = ValidationEngine()

    # Validate same document with different retailer rules
    print("\n  Validating edi_850_valid.txt with different retailer rules:\n")

    # No retailer (base rules)
    result_base = engine.validate_file("samples/edi_850_valid.txt", "850")
    print(f"  Base Rules:      {result_base.error_count()} errors, {result_base.warning_count()} warnings")

    # Walmart
    result_walmart = engine.validate_file("samples/edi_850_valid.txt", "850", "walmart")
    print(f"  Walmart Rules:   {result_walmart.error_count()} errors, {result_walmart.warning_count()} warnings")

    # Amazon
    result_amazon = engine.validate_file("samples/edi_850_valid.txt", "850", "amazon")
    print(f"  Amazon Rules:    {result_amazon.error_count()} errors, {result_amazon.warning_count()} warnings")

    # Target
    result_target = engine.validate_file("samples/edi_850_valid.txt", "850", "target")
    print(f"  Target Rules:    {result_target.error_count()} errors, {result_target.warning_count()} warnings")

    print("\n  Conclusion: Retailer-specific rules add stricter validation")


def main():
    """Run all demonstrations."""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 18 + "REPORT GENERATION DEMO" + " " * 28 + "║")
    print("╚" + "═" * 68 + "╝")

    try:
        # Demo each report type
        demo_dashboard()
        demo_text_report()
        demo_json_export()
        demo_csv_export()
        demo_compliant_document()
        demo_save_reports()
        demo_comparison()

        # Summary
        print_header("DEMO COMPLETE")
        print("\n  ✓ All report formats demonstrated")
        print("  ✓ Reports saved to output/ directory")
        print("\n  Available formats:")
        print("    - Text:      Human-readable detailed report")
        print("    - JSON:      Machine-readable export")
        print("    - CSV:       Spreadsheet-compatible issue list")
        print("    - Dashboard: Quick summary visualization")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
