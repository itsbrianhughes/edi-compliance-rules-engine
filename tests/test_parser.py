"""
Unit tests for EDI Parser module.

Tests cover:
- Segment splitting
- Element extraction
- Metadata extraction
- Line number tracking
- JSON output
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser.edi_parser import EDIParser
from src.parser.segment_utils import (
    split_segments,
    split_elements,
    get_segment_id,
    get_element_value,
    normalize_edi_text
)


def test_normalize_edi_text():
    """Test EDI text normalization."""
    raw = "  ISA*00*  ~\n\nGS*PO*  ~  \n\n"
    normalized = normalize_edi_text(raw)
    assert "ISA*00*" in normalized
    assert "GS*PO*" in normalized
    print("✓ test_normalize_edi_text passed")


def test_split_segments():
    """Test segment splitting."""
    edi_text = "ISA*00*TEST~GS*PO*SENDER~ST*850*0001~"
    segments = split_segments(edi_text)
    assert len(segments) == 3
    assert segments[0].startswith("ISA")
    assert segments[1].startswith("GS")
    assert segments[2].startswith("ST")
    print("✓ test_split_segments passed")


def test_split_elements():
    """Test element splitting."""
    segment = "BEG*00*NE*PO123456**20231215"
    elements = split_elements(segment)
    assert len(elements) == 6
    assert elements[0] == "BEG"
    assert elements[3] == "PO123456"
    assert elements[4] == ""  # Empty element
    assert elements[5] == "20231215"
    print("✓ test_split_elements passed")


def test_get_segment_id():
    """Test segment ID extraction."""
    segment = "BEG*00*NE*PO123456"
    seg_id = get_segment_id(segment)
    assert seg_id == "BEG"
    print("✓ test_get_segment_id passed")


def test_get_element_value():
    """Test element value extraction."""
    segment = "BEG*00*NE*PO123456**20231215"
    value = get_element_value(segment, 3)
    assert value == "PO123456"

    # Test empty element
    empty_value = get_element_value(segment, 4, default="N/A")
    assert empty_value == "N/A"
    print("✓ test_get_element_value passed")


def test_parse_850_valid():
    """Test parsing valid 850 document."""
    parser = EDIParser()
    result = parser.parse_file("samples/edi_850_valid.txt")

    # Check metadata
    assert result['metadata']['doc_type'] == "850"
    assert result['metadata']['sender_id'] == "SENDER"
    assert result['metadata']['receiver_id'] == "RECEIVER"

    # Check segments were parsed
    assert len(result['segments']) > 0

    # Check line numbers are tracked
    first_segment = result['segments'][0]
    assert 'line' in first_segment
    assert first_segment['line'] == 1

    # Check statistics
    assert result['statistics']['total_segments'] > 0
    assert result['statistics']['has_envelope'] == True

    print("✓ test_parse_850_valid passed")
    print(f"  - Parsed {result['statistics']['total_segments']} segments")
    print(f"  - Document type: {result['metadata']['doc_type']}")


def test_get_segments_by_id():
    """Test finding segments by ID."""
    parser = EDIParser()
    parser.parse_file("samples/edi_850_valid.txt")

    # Find all PO1 segments
    po1_segments = parser.get_segments_by_id("PO1")
    assert len(po1_segments) == 2  # Sample has 2 line items

    # Find BEG segment
    beg_segments = parser.get_segments_by_id("BEG")
    assert len(beg_segments) == 1

    print("✓ test_get_segments_by_id passed")


def test_get_element_value_method():
    """Test getting element values from parsed document."""
    parser = EDIParser()
    parser.parse_file("samples/edi_850_valid.txt")

    # Get PO number from BEG segment
    po_number = parser.get_element_value("BEG", 3)
    assert po_number == "PO123456"

    # Get date
    date_value = parser.get_element_value("BEG", 5)
    assert date_value == "20231215"

    print("✓ test_get_element_value_method passed")


def test_parse_invalid_850():
    """Test parsing invalid 850 document."""
    parser = EDIParser()
    result = parser.parse_file("samples/edi_850_invalid.txt")

    # Should still parse, even if invalid
    assert result['metadata']['doc_type'] == "850"
    assert len(result['segments']) > 0

    print("✓ test_parse_invalid_850 passed")


def test_to_json():
    """Test JSON export."""
    parser = EDIParser()
    parser.parse_file("samples/edi_850_valid.txt")

    json_str = parser.to_json()
    assert '"doc_type": "850"' in json_str
    assert '"segments"' in json_str

    print("✓ test_to_json passed")


def run_all_tests():
    """Run all parser tests."""
    print("\n" + "=" * 50)
    print("Running EDI Parser Tests")
    print("=" * 50 + "\n")

    try:
        # Unit tests
        test_normalize_edi_text()
        test_split_segments()
        test_split_elements()
        test_get_segment_id()
        test_get_element_value()

        # Integration tests
        test_parse_850_valid()
        test_get_segments_by_id()
        test_get_element_value_method()
        test_parse_invalid_850()
        test_to_json()

        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        print("=" * 50 + "\n")

        return True

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
