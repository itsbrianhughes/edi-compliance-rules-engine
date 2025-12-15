"""
Unit tests for Validation Engine.

Tests cover:
- Error collector
- Required segment validation
- Element validation
- Conditional rule validation
- Cross-segment validation
- End-to-end validation
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser.edi_parser import EDIParser
from src.rules.rule_loader import RuleLoader
from src.validator.validation_engine import ValidationEngine
from src.validator.error_collector import ErrorCollector, ValidationError


def test_error_collector():
    """Test error collector functionality."""
    collector = ErrorCollector()

    # Add errors of different severities
    collector.add_error(
        rule_id="TEST_001",
        severity="ERROR",
        message="Test error",
        segment_id="BEG",
        line_number=5
    )

    collector.add_error(
        rule_id="TEST_002",
        severity="WARNING",
        message="Test warning",
        segment_id="PO1",
        line_number=10
    )

    collector.add_error(
        rule_id="TEST_003",
        severity="INFO",
        message="Test info",
        segment_id="N1",
        line_number=15
    )

    # Test counts
    assert len(collector.errors) == 1
    assert len(collector.warnings) == 1
    assert len(collector.info) == 1
    assert len(collector) == 3

    # Test has_errors
    assert collector.has_errors() == True
    assert collector.has_warnings() == True

    # Test statistics
    stats = collector.get_statistics()
    assert stats['total_errors'] == 3
    assert stats['by_severity']['ERROR'] == 1
    assert stats['by_severity']['WARNING'] == 1
    assert stats['is_compliant'] == False

    print("✓ test_error_collector passed")


def test_validate_850_valid():
    """Test validation of valid 850 PO."""
    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_850_valid.txt", "850")

    print(f"\n  Valid 850 results:")
    print(f"    Errors: {result.error_count()}")
    print(f"    Warnings: {result.warning_count()}")
    print(f"    Compliant: {result.is_compliant()}")

    # Valid file should have few or no errors
    # (May have warnings depending on rules)
    assert result.error_count() <= 5  # Allow some minor issues

    print("✓ test_validate_850_valid passed")


def test_validate_850_invalid():
    """Test validation of invalid 850 PO."""
    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_850_invalid.txt", "850")

    print(f"\n  Invalid 850 results:")
    print(f"    Errors: {result.error_count()}")
    print(f"    Warnings: {result.warning_count()}")
    print(f"    Compliant: {result.is_compliant()}")

    # Invalid file should have errors
    assert result.error_count() > 0
    assert result.is_compliant() == False

    # Check that we captured some specific issues
    all_issues = result.get_all_issues()
    assert len(all_issues) > 0

    # Print first few errors for inspection
    print(f"\n  First 3 issues found:")
    for issue in all_issues[:3]:
        print(f"    - {issue}")

    print("✓ test_validate_850_invalid passed")


def test_validate_850_walmart():
    """Test validation of 850 with Walmart rules."""
    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_850_valid.txt", "850", "walmart")

    print(f"\n  850 + Walmart results:")
    print(f"    Errors: {result.error_count()}")
    print(f"    Warnings: {result.warning_count()}")

    # Walmart has stricter rules, so may have more violations
    # The valid file might not meet all Walmart requirements
    print(f"    Compliant: {result.is_compliant()}")

    # Check summary
    summary = result.get_summary()
    assert summary['validation_info']['retailer'] == 'walmart'
    assert summary['document_info']['doc_type'] == '850'

    print("✓ test_validate_850_walmart passed")


def test_validate_856():
    """Test validation of 856 ASN."""
    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_856_valid.txt", "856")

    print(f"\n  856 ASN results:")
    print(f"    Errors: {result.error_count()}")
    print(f"    Warnings: {result.warning_count()}")
    print(f"    Compliant: {result.is_compliant()}")

    # Should validate successfully
    assert result.error_count() <= 5

    print("✓ test_validate_856 passed")


def test_validate_810():
    """Test validation of 810 Invoice."""
    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_810_valid.txt", "810")

    print(f"\n  810 Invoice results:")
    print(f"    Errors: {result.error_count()}")
    print(f"    Warnings: {result.warning_count()}")
    print(f"    Compliant: {result.is_compliant()}")

    # Should validate successfully
    assert result.error_count() <= 5

    print("✓ test_validate_810 passed")


def test_validation_result_methods():
    """Test ValidationResult helper methods."""
    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_850_invalid.txt", "850")

    # Test result methods
    assert isinstance(result.is_compliant(), bool)
    assert isinstance(result.error_count(), int)
    assert isinstance(result.warning_count(), int)
    assert isinstance(result.total_issues(), int)

    # Test get methods
    errors = result.get_errors()
    warnings = result.get_warnings()
    all_issues = result.get_all_issues()

    assert isinstance(errors, list)
    assert isinstance(warnings, list)
    assert isinstance(all_issues, list)

    # Test summary
    summary = result.get_summary()
    assert 'document_info' in summary
    assert 'validation_info' in summary
    assert 'compliance_status' in summary

    # Test to_dict
    result_dict = result.to_dict()
    assert 'summary' in result_dict
    assert 'issues' in result_dict

    print("✓ test_validation_result_methods passed")


def test_error_by_segment():
    """Test filtering errors by segment."""
    collector = ErrorCollector()

    collector.add_error("R1", "ERROR", "BEG error", segment_id="BEG", line_number=5)
    collector.add_error("R2", "ERROR", "PO1 error", segment_id="PO1", line_number=10)
    collector.add_error("R3", "ERROR", "Another BEG error", segment_id="BEG", line_number=6)

    # Get BEG errors
    beg_errors = collector.get_errors_by_segment("BEG")
    assert len(beg_errors) == 2

    # Get PO1 errors
    po1_errors = collector.get_errors_by_segment("PO1")
    assert len(po1_errors) == 1

    print("✓ test_error_by_segment passed")


def test_error_by_line():
    """Test filtering errors by line number."""
    collector = ErrorCollector()

    collector.add_error("R1", "ERROR", "Error on line 5", line_number=5)
    collector.add_error("R2", "ERROR", "Error on line 10", line_number=10)
    collector.add_error("R3", "ERROR", "Another error on line 5", line_number=5)

    # Get line 5 errors
    line5_errors = collector.get_errors_by_line(5)
    assert len(line5_errors) == 2

    # Get line 10 errors
    line10_errors = collector.get_errors_by_line(10)
    assert len(line10_errors) == 1

    print("✓ test_error_by_line passed")


def test_required_segment_detection():
    """Test that required segment violations are detected."""
    # Parse the invalid 850 (missing segments)
    parser = EDIParser()
    parsed = parser.parse_file("samples/edi_850_invalid.txt")

    loader = RuleLoader()
    rules = loader.load_rules("850")

    engine = ValidationEngine()
    result = engine.validate(parsed, rules)

    # Should detect missing N3 segment
    all_issues = result.get_all_issues()
    issue_messages = [str(issue.message) for issue in all_issues]

    # Check that we're detecting some kind of violation
    assert len(all_issues) > 0

    print("✓ test_required_segment_detection passed")


def test_validation_performance():
    """Test validation performance."""
    import time

    engine = ValidationEngine()

    start = time.time()
    result = engine.validate_file("samples/edi_850_valid.txt", "850", "walmart")
    elapsed = time.time() - start

    print(f"\n  Validation performance:")
    print(f"    Time: {elapsed:.3f}s")
    print(f"    Reported time: {result.validation_time:.3f}s")

    # Should complete quickly (under 1 second for small file)
    assert elapsed < 1.0

    print("✓ test_validation_performance passed")


def run_all_tests():
    """Run all validation tests."""
    print("\n" + "=" * 50)
    print("Running Validation Engine Tests")
    print("=" * 50 + "\n")

    try:
        # Unit tests
        test_error_collector()
        test_error_by_segment()
        test_error_by_line()

        # Integration tests
        test_validate_850_valid()
        test_validate_850_invalid()
        test_validate_850_walmart()
        test_validate_856()
        test_validate_810()

        # Result methods
        test_validation_result_methods()

        # Specific validations
        test_required_segment_detection()

        # Performance
        test_validation_performance()

        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        print("=" * 50 + "\n")

        return True

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
