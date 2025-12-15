"""
Installation Verification Script

Verifies that all components of the EDI Compliance Rules Engine
are properly installed and functional.

Usage:
    python verify_installation.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def check_python_version():
    """Verify Python version."""
    print("\n✓ Checking Python version...")
    major, minor = sys.version_info[:2]
    print(f"  Python {major}.{minor}")

    if major < 3 or (major == 3 and minor < 8):
        print("  ❌ Python 3.8 or higher required")
        return False

    print("  ✅ Python version OK")
    return True


def check_imports():
    """Verify all required modules can be imported."""
    print("\n✓ Checking required imports...")

    imports_to_check = [
        ("json", "JSON support"),
        ("pathlib", "Path handling"),
        ("re", "Regular expressions"),
        ("csv", "CSV support"),
        ("datetime", "Date/time handling"),
        ("logging", "Logging"),
    ]

    all_ok = True

    for module_name, description in imports_to_check:
        try:
            __import__(module_name)
            print(f"  ✅ {module_name:15} - {description}")
        except ImportError as e:
            print(f"  ❌ {module_name:15} - {description} - {e}")
            all_ok = False

    return all_ok


def check_dependencies():
    """Verify external dependencies."""
    print("\n✓ Checking external dependencies...")

    dependencies = [
        ("streamlit", "Streamlit web framework"),
        ("pytest", "Testing framework (optional)"),
    ]

    all_ok = True

    for package, description in dependencies:
        try:
            __import__(package)
            print(f"  ✅ {package:15} - {description}")
        except ImportError:
            if package == "pytest":
                print(f"  ⚠️  {package:15} - {description} - Optional, skipping")
            else:
                print(f"  ❌ {package:15} - {description} - Missing")
                all_ok = False

    return all_ok


def check_project_structure():
    """Verify project directory structure."""
    print("\n✓ Checking project structure...")

    required_dirs = [
        "src",
        "src/parser",
        "src/rules",
        "src/rules/rule_definitions",
        "src/rules/rule_definitions/retailer_overrides",
        "src/validator",
        "src/reporting",
        "src/ui",
        "samples",
        "tests",
        "docs",
        "config",
    ]

    all_ok = True

    for dir_path in required_dirs:
        if Path(dir_path).is_dir():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} - Missing")
            all_ok = False

    return all_ok


def check_required_files():
    """Verify required files exist."""
    print("\n✓ Checking required files...")

    required_files = [
        "src/parser/edi_parser.py",
        "src/parser/segment_utils.py",
        "src/rules/rule_loader.py",
        "src/rules/rule_definitions/x12_core.json",
        "src/rules/rule_definitions/doc_850.json",
        "src/rules/rule_definitions/doc_856.json",
        "src/rules/rule_definitions/doc_810.json",
        "src/rules/rule_definitions/retailer_overrides/walmart.json",
        "src/rules/rule_definitions/retailer_overrides/amazon.json",
        "src/rules/rule_definitions/retailer_overrides/target.json",
        "src/validator/validation_engine.py",
        "src/validator/rule_evaluators.py",
        "src/validator/error_collector.py",
        "src/reporting/report_generator.py",
        "src/reporting/formatters.py",
        "src/ui/streamlit_app.py",
        "samples/edi_850_valid.txt",
        "samples/edi_856_valid.txt",
        "samples/edi_810_valid.txt",
        "config/settings.py",
    ]

    all_ok = True

    for file_path in required_files:
        if Path(file_path).is_file():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - Missing")
            all_ok = False

    return all_ok


def check_modules_import():
    """Verify all custom modules can be imported."""
    print("\n✓ Checking custom module imports...")

    modules = [
        ("src.parser.edi_parser", "EDI Parser"),
        ("src.parser.segment_utils", "Segment Utilities"),
        ("src.rules.rule_loader", "Rule Loader"),
        ("src.validator.validation_engine", "Validation Engine"),
        ("src.validator.rule_evaluators", "Rule Evaluators"),
        ("src.validator.error_collector", "Error Collector"),
        ("src.reporting.report_generator", "Report Generator"),
        ("src.reporting.formatters", "Report Formatters"),
        ("config.settings", "Configuration"),
    ]

    all_ok = True

    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"  ✅ {module_name:35} - {description}")
        except Exception as e:
            print(f"  ❌ {module_name:35} - {description} - {e}")
            all_ok = False

    return all_ok


def check_sample_files():
    """Verify sample files can be parsed."""
    print("\n✓ Checking sample file parsing...")

    try:
        from src.parser.edi_parser import EDIParser

        parser = EDIParser()

        samples = [
            ("samples/edi_850_valid.txt", "850 Purchase Order"),
            ("samples/edi_856_valid.txt", "856 ASN"),
            ("samples/edi_810_valid.txt", "810 Invoice"),
        ]

        all_ok = True

        for file_path, description in samples:
            try:
                result = parser.parse_file(file_path)
                seg_count = result['statistics']['total_segments']
                print(f"  ✅ {file_path:30} - {description} ({seg_count} segments)")
            except Exception as e:
                print(f"  ❌ {file_path:30} - {description} - {e}")
                all_ok = False

        return all_ok

    except Exception as e:
        print(f"  ❌ Failed to import parser: {e}")
        return False


def check_validation():
    """Verify validation engine works."""
    print("\n✓ Checking validation engine...")

    try:
        from src.validator.validation_engine import ValidationEngine

        engine = ValidationEngine()

        # Test validation
        result = engine.validate_file("samples/edi_850_valid.txt", "850")

        print(f"  ✅ Validation engine functional")
        print(f"     - Compliant: {result.is_compliant()}")
        print(f"     - Errors: {result.error_count()}")
        print(f"     - Warnings: {result.warning_count()}")
        print(f"     - Validation time: {result.validation_time:.3f}s")

        return True

    except Exception as e:
        print(f"  ❌ Validation engine failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_reporting():
    """Verify report generation works."""
    print("\n✓ Checking report generation...")

    try:
        from src.validator.validation_engine import ValidationEngine
        from src.reporting.report_generator import ReportGenerator

        engine = ValidationEngine()
        result = engine.validate_file("samples/edi_850_valid.txt", "850")

        generator = ReportGenerator(result)

        # Test all formats
        formats = {
            "Text": generator.generate_text_report(),
            "JSON": generator.generate_json_report(),
            "CSV": generator.generate_csv_report(),
            "Dashboard": generator.generate_dashboard(),
        }

        all_ok = True

        for format_name, report in formats.items():
            if report and len(report) > 0:
                print(f"  ✅ {format_name} report generated ({len(report)} chars)")
            else:
                print(f"  ❌ {format_name} report failed")
                all_ok = False

        return all_ok

    except Exception as e:
        print(f"  ❌ Report generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_streamlit_app():
    """Verify Streamlit app can be imported."""
    print("\n✓ Checking Streamlit application...")

    try:
        # Just check if the file exists and has no syntax errors
        with open("src/ui/streamlit_app.py", 'r') as f:
            code = f.read()

        # Try to compile (will catch syntax errors)
        compile(code, "src/ui/streamlit_app.py", "exec")

        print(f"  ✅ Streamlit app file OK ({len(code)} chars)")
        print(f"  ℹ️  Run 'streamlit run src/ui/streamlit_app.py' to test UI")

        return True

    except Exception as e:
        print(f"  ❌ Streamlit app check failed: {e}")
        return False


def main():
    """Run all verification checks."""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 18 + "INSTALLATION VERIFICATION" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")

    print("\n  Verifying EDI Compliance Rules Engine installation...")

    checks = [
        ("Python Version", check_python_version),
        ("Standard Library", check_imports),
        ("External Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Required Files", check_required_files),
        ("Module Imports", check_modules_import),
        ("Sample File Parsing", check_sample_files),
        ("Validation Engine", check_validation),
        ("Report Generation", check_reporting),
        ("Streamlit App", check_streamlit_app),
    ]

    results = {}

    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"\n❌ {check_name} check crashed: {e}")
            import traceback
            traceback.print_exc()
            results[check_name] = False

    # Summary
    print_header("VERIFICATION SUMMARY")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print()
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {check_name}")

    print(f"\n  Overall: {passed}/{total} checks passed")

    if passed == total:
        print("\n  🎉 All checks passed! Installation is complete.")
        print("\n  Next steps:")
        print("    1. Run tests: python tests/test_validator.py")
        print("    2. Try demos: python demo_ui_workflow.py")
        print("    3. Launch UI: streamlit run src/ui/streamlit_app.py")
        print()
        return True
    else:
        print("\n  ⚠️  Some checks failed. Please review errors above.")
        print("\n  Common fixes:")
        print("    1. Install dependencies: pip install -r requirements.txt")
        print("    2. Check Python version: python --version (need 3.8+)")
        print("    3. Verify project structure is complete")
        print()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
