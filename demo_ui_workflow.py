"""
UI Workflow Demonstration

Demonstrates the exact workflow that the Streamlit UI executes,
validating that all components integrate correctly.

This simulates what happens when a user:
1. Selects document type and retailer
2. Provides EDI input (file, paste, or sample)
3. Clicks "Run Validation"
4. Views results and downloads reports
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.parser.edi_parser import EDIParser
from src.rules.rule_loader import RuleLoader
from src.validator.validation_engine import ValidationEngine
from src.reporting.report_generator import ReportGenerator


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def simulate_file_upload_workflow():
    """
    Simulates: User uploads file → selects 850 + Walmart → validates
    """
    print_header("WORKFLOW 1: File Upload → Walmart 850 Validation")

    # Step 1: User configuration
    doc_type = "850"
    retailer = "walmart"
    file_path = "samples/edi_850_valid.txt"

    print(f"\n  Configuration:")
    print(f"    Document Type: {doc_type}")
    print(f"    Retailer: {retailer.upper()}")
    print(f"    Input Method: Upload File")
    print(f"    File: {file_path}")

    # Step 2: Parse EDI (happens when user clicks "Run Validation")
    print(f"\n  ⚙️  Parsing EDI document...")
    parser = EDIParser()
    parsed_edi = parser.parse_file(file_path)
    print(f"    ✓ Parsed {parsed_edi['statistics']['total_segments']} segments")

    # Step 3: Load rules
    print(f"\n  ⚙️  Loading validation rules...")
    loader = RuleLoader()
    rules = loader.load_rules(doc_type, retailer)
    print(f"    ✓ Loaded rules for {doc_type} + {retailer.upper()}")

    # Step 4: Validate
    print(f"\n  ⚙️  Running validation...")
    engine = ValidationEngine()
    result = engine.validate(parsed_edi, rules, retailer)
    print(f"    ✓ Validation complete in {result.validation_time:.3f}s")

    # Step 5: Generate reports (stored in session state)
    generator = ReportGenerator(result)

    # Step 6: Display results (like UI tabs)
    print(f"\n  📊 RESULTS:")
    if result.is_compliant():
        print(f"    ✅ COMPLIANT - Document passed all validation rules")
    else:
        print(f"    ❌ NON-COMPLIANT - {result.error_count()} error(s) found")

    print(f"\n  Quick Stats:")
    print(f"    Errors:   {result.error_count()}")
    print(f"    Warnings: {result.warning_count()}")
    print(f"    Total:    {result.total_issues()}")

    # Step 7: Show dashboard (Tab 1)
    print(f"\n  Dashboard Preview:")
    dashboard = generator.generate_dashboard()
    dashboard_lines = dashboard.split('\n')[:15]
    for line in dashboard_lines:
        print(f"    {line}")
    print(f"    ... (dashboard continues)")

    # Step 8: Download reports (Tab 4)
    print(f"\n  💾 Downloads Available:")
    print(f"    ✓ Text Report:   validation_report_{doc_type}.txt")
    print(f"    ✓ JSON Report:   validation_report_{doc_type}.json")
    print(f"    ✓ CSV Report:    validation_report_{doc_type}.csv")
    print(f"    ✓ Dashboard:     validation_dashboard_{doc_type}.txt")

    return result


def simulate_paste_text_workflow():
    """
    Simulates: User pastes text → selects 856 (no retailer) → validates
    """
    print_header("WORKFLOW 2: Paste Text → 856 ASN Validation")

    # Step 1: User configuration
    doc_type = "856"
    retailer = None

    print(f"\n  Configuration:")
    print(f"    Document Type: {doc_type}")
    print(f"    Retailer: None (Base Rules Only)")
    print(f"    Input Method: Paste Text")

    # Step 2: User pastes EDI text (read from sample for demo)
    print(f"\n  📋 Reading pasted EDI content...")
    with open("samples/edi_856_valid.txt", 'r') as f:
        edi_text = f.read()

    lines = edi_text.split('\n')
    print(f"    ✓ {len(lines)} lines pasted")

    # Step 3: Parse text (not file)
    print(f"\n  ⚙️  Parsing EDI text...")
    parser = EDIParser()
    parsed_edi = parser.parse_text(edi_text)
    print(f"    ✓ Parsed {parsed_edi['statistics']['total_segments']} segments")

    # Step 4: Load rules
    print(f"\n  ⚙️  Loading validation rules...")
    loader = RuleLoader()
    rules = loader.load_rules(doc_type, retailer)
    print(f"    ✓ Loaded rules for document type {doc_type}")

    # Step 5: Validate
    print(f"\n  ⚙️  Running validation...")
    engine = ValidationEngine()
    result = engine.validate(parsed_edi, rules, retailer)
    print(f"    ✓ Validation complete")

    # Step 6: Display results
    generator = ReportGenerator(result)

    print(f"\n  📊 RESULTS:")
    if result.is_compliant():
        print(f"    ✅ COMPLIANT")
    else:
        print(f"    ❌ NON-COMPLIANT - {result.error_count()} errors")

    print(f"\n  Quick Stats:")
    print(f"    Errors:   {result.error_count()}")
    print(f"    Warnings: {result.warning_count()}")

    # Step 7: Show issues list (Tab 3)
    if result.total_issues() > 0:
        print(f"\n  📋 Issues List (filtering by ERROR):")
        errors = result.get_errors()
        for idx, error in enumerate(errors[:3], 1):
            print(f"    {idx}. [Line {error.line_number}] {error.message}")
        if len(errors) > 3:
            print(f"    ... ({len(errors) - 3} more errors)")
    else:
        print(f"\n  ✅ No issues found - document is fully compliant!")

    return result


def simulate_sample_file_workflow():
    """
    Simulates: User selects sample → 850 Invalid → Target → validates
    """
    print_header("WORKFLOW 3: Sample File → 850 Invalid → Target")

    # Step 1: User configuration
    doc_type = "850"
    retailer = "target"
    sample_file = "samples/edi_850_invalid.txt"

    print(f"\n  Configuration:")
    print(f"    Document Type: {doc_type}")
    print(f"    Retailer: {retailer.upper()}")
    print(f"    Input Method: Use Sample File")
    print(f"    Selected: 850 - Invalid PO")

    # Step 2: Load sample file
    print(f"\n  ✅ Loaded: 850 - Invalid PO")

    try:
        with open(sample_file, 'r') as f:
            edi_text = f.read()
    except FileNotFoundError:
        print(f"  ❌ Sample file not found: {sample_file}")
        return None

    # Step 3: Preview (expandable section in UI)
    print(f"\n  📝 Preview EDI Content:")
    preview_lines = edi_text.split('\n')[:5]
    for line in preview_lines:
        print(f"    {line}")
    print(f"    ... ({len(edi_text.split(chr(10))) - 5} more lines)")

    # Step 4: Parse, load rules, validate
    print(f"\n  ⚙️  Running validation...")
    parser = EDIParser()
    parsed_edi = parser.parse_text(edi_text)

    loader = RuleLoader()
    rules = loader.load_rules(doc_type, retailer)

    engine = ValidationEngine()
    result = engine.validate(parsed_edi, rules, retailer)

    # Step 5: Display results
    generator = ReportGenerator(result)

    print(f"\n  📊 RESULTS:")
    if result.is_compliant():
        print(f"    ✅ COMPLIANT")
    else:
        print(f"    ❌ NON-COMPLIANT - {result.error_count()} error(s) found")

    print(f"\n  Quick Stats:")
    print(f"    Errors:   {result.error_count()}")
    print(f"    Warnings: {result.warning_count()}")
    print(f"    Total:    {result.total_issues()}")

    # Step 6: Show detailed report (Tab 2)
    print(f"\n  📝 Detailed Report Preview:")
    text_report = generator.generate_text_report()
    report_lines = text_report.split('\n')[:25]
    for line in report_lines:
        print(f"    {line}")
    print(f"    ... (report continues)")

    return result


def simulate_download_all_formats():
    """
    Simulates: User clicks all download buttons (Tab 4)
    """
    print_header("WORKFLOW 4: Download All Report Formats")

    # Validate a document first
    print(f"\n  ⚙️  Validating sample document...")
    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_810_valid.txt", "810", "amazon")

    generator = ReportGenerator(result)

    # Save all formats (like clicking all download buttons)
    print(f"\n  💾 Saving all report formats...")
    files = generator.save_all_formats("output", "demo_ui_validation")

    print(f"\n  ✓ Reports saved:")
    for format_name, file_path in files.items():
        file_size = Path(file_path).stat().st_size
        print(f"    {format_name:12} → {file_path} ({file_size:,} bytes)")

    return files


def simulate_retailer_comparison():
    """
    Simulates: User validates same document with different retailers
    """
    print_header("WORKFLOW 5: Retailer Comparison")

    doc_type = "850"
    sample_file = "samples/edi_850_valid.txt"

    print(f"\n  Validating {sample_file} with different retailer rules:")
    print()

    engine = ValidationEngine()

    # Base rules
    result_base = engine.validate_file(sample_file, doc_type)
    print(f"    None (Base):  {result_base.error_count()} errors, {result_base.warning_count()} warnings")

    # Walmart
    result_walmart = engine.validate_file(sample_file, doc_type, "walmart")
    print(f"    Walmart:      {result_walmart.error_count()} errors, {result_walmart.warning_count()} warnings")

    # Amazon
    result_amazon = engine.validate_file(sample_file, doc_type, "amazon")
    print(f"    Amazon:       {result_amazon.error_count()} errors, {result_amazon.warning_count()} warnings")

    # Target
    result_target = engine.validate_file(sample_file, doc_type, "target")
    print(f"    Target:       {result_target.error_count()} errors, {result_target.warning_count()} warnings")

    print(f"\n  📊 Observation:")
    print(f"    Retailer-specific rules add stricter validation requirements")
    print(f"    Same document may pass base rules but fail retailer rules")


def main():
    """Run all UI workflow demonstrations."""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "UI WORKFLOW DEMONSTRATION" + " " * 23 + "║")
    print("╚" + "═" * 68 + "╝")

    print("\n  This demonstrates the exact workflow executed by the Streamlit UI.")
    print("  Each scenario simulates user interactions with the web interface.")

    try:
        # Workflow 1: File upload
        simulate_file_upload_workflow()

        # Workflow 2: Paste text
        simulate_paste_text_workflow()

        # Workflow 3: Sample file
        simulate_sample_file_workflow()

        # Workflow 4: Download all formats
        simulate_download_all_formats()

        # Workflow 5: Retailer comparison
        simulate_retailer_comparison()

        # Summary
        print_header("DEMONSTRATION COMPLETE")
        print("\n  ✓ All UI workflows validated successfully")
        print("\n  The Streamlit UI executes these exact steps:")
        print("    1. Parse EDI (file/text/sample)")
        print("    2. Load rules (document + retailer)")
        print("    3. Run validation")
        print("    4. Generate reports (4 formats)")
        print("    5. Display results (4 tabs)")
        print("    6. Enable downloads")
        print("\n  To launch the UI:")
        print("    streamlit run src/ui/streamlit_app.py")
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
