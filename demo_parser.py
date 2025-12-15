"""
EDI Parser Demonstration

This script demonstrates the capabilities of the EDI parser by:
- Parsing sample EDI files
- Displaying metadata and statistics
- Showing segment structure
- Exporting to JSON
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.parser.edi_parser import EDIParser


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def demo_parse_850():
    """Demonstrate parsing an 850 Purchase Order."""
    print_header("Parsing 850 Purchase Order")

    parser = EDIParser()
    result = parser.parse_file("samples/edi_850_valid.txt")

    # Display metadata
    print("\n📋 METADATA:")
    metadata = result['metadata']
    print(f"  Document Type:        {metadata['doc_type']}")
    print(f"  Sender:              {metadata['sender_id']}")
    print(f"  Receiver:            {metadata['receiver_id']}")
    print(f"  Interchange Date:    {metadata['interchange_date']}")
    print(f"  Interchange Time:    {metadata['interchange_time']}")
    print(f"  Control Number:      {metadata['control_numbers']['transaction_control']}")

    # Display statistics
    print("\n📊 STATISTICS:")
    stats = result['statistics']
    print(f"  Total Segments:      {stats['total_segments']}")
    print(f"  Complete Envelope:   {stats['has_envelope']}")

    print("\n  Segment Breakdown:")
    for seg_id, count in sorted(stats['segment_counts'].items()):
        print(f"    {seg_id:8} → {count:3} occurrence(s)")

    # Show specific segments
    print("\n📦 KEY SEGMENTS:")

    # BEG segment
    beg = parser.get_segments_by_id("BEG")[0]
    print(f"\n  BEG (Beginning) - Line {beg['line']}:")
    print(f"    Purpose Code:     {beg['elements'][1]}")
    print(f"    PO Type:          {beg['elements'][2]}")
    print(f"    PO Number:        {beg['elements'][3]}")
    print(f"    Date:             {beg['elements'][5]}")

    # PO1 segments (line items)
    po1_segments = parser.get_segments_by_id("PO1")
    print(f"\n  PO1 (Line Items) - {len(po1_segments)} items:")
    for idx, po1 in enumerate(po1_segments, 1):
        print(f"    Item {idx} (Line {po1['line']}):")
        print(f"      Quantity:       {po1['elements'][2]} {po1['elements'][3]}")
        print(f"      Unit Price:     ${po1['elements'][4]}")
        print(f"      Product ID:     {po1['elements'][7]}")

    # N1 segments (parties)
    n1_segments = parser.get_segments_by_id("N1")
    print(f"\n  N1 (Name/Address) - {len(n1_segments)} parties:")
    for n1 in n1_segments:
        qualifier = n1['elements'][1]
        name = n1['elements'][2]
        entity_id = n1['elements'][4] if len(n1['elements']) > 4 else "N/A"
        print(f"    {qualifier} → {name} ({entity_id})")

    return result


def demo_parse_856():
    """Demonstrate parsing an 856 ASN."""
    print_header("Parsing 856 Advance Ship Notice")

    parser = EDIParser()
    result = parser.parse_file("samples/edi_856_valid.txt")

    metadata = result['metadata']
    print(f"\n  Document Type:  {metadata['doc_type']}")
    print(f"  Sender:         {metadata['sender_id']}")
    print(f"  Total Segments: {result['statistics']['total_segments']}")

    # Show BSN segment
    bsn = parser.get_segments_by_id("BSN")[0]
    print(f"\n  BSN (Beginning Segment for ASN) - Line {bsn['line']}:")
    print(f"    Shipment ID:    {bsn['elements'][2]}")
    print(f"    Date:           {bsn['elements'][3]}")
    print(f"    Time:           {bsn['elements'][4]}")

    return result


def demo_parse_810():
    """Demonstrate parsing an 810 Invoice."""
    print_header("Parsing 810 Invoice")

    parser = EDIParser()
    result = parser.parse_file("samples/edi_810_valid.txt")

    metadata = result['metadata']
    print(f"\n  Document Type:  {metadata['doc_type']}")
    print(f"  Total Segments: {result['statistics']['total_segments']}")

    # Show BIG segment
    big = parser.get_segments_by_id("BIG")[0]
    print(f"\n  BIG (Beginning Segment for Invoice) - Line {big['line']}:")
    print(f"    Invoice Date:   {big['elements'][1]}")
    print(f"    Invoice Number: {big['elements'][2]}")
    print(f"    PO Number:      {big['elements'][4]}")

    # Show TDS segment (total amounts)
    tds = parser.get_segments_by_id("TDS")
    if tds:
        tds_seg = tds[0]
        amount = tds_seg['elements'][1]
        # Format as currency (amount is in cents)
        formatted_amount = f"${int(amount)/100:,.2f}"
        print(f"\n  TDS (Total Monetary Value):")
        print(f"    Invoice Total:  {formatted_amount}")

    return result


def demo_json_export():
    """Demonstrate JSON export."""
    print_header("JSON Export Example")

    parser = EDIParser()
    parser.parse_file("samples/edi_850_valid.txt")

    # Export to JSON
    json_output = parser.to_json(indent=2)

    # Show first 50 lines
    lines = json_output.split('\n')
    print("\n  First 50 lines of JSON output:\n")
    for line in lines[:50]:
        print(f"  {line}")

    if len(lines) > 50:
        print(f"\n  ... ({len(lines) - 50} more lines)")

    # Save to file
    output_path = Path("output/sample_850_parsed.json")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(json_output)

    print(f"\n  ✓ Full JSON saved to: {output_path}")


def demo_invalid_handling():
    """Demonstrate parsing invalid EDI."""
    print_header("Handling Invalid EDI")

    parser = EDIParser()
    result = parser.parse_file("samples/edi_850_invalid.txt")

    print("\n  ℹ️  Parser successfully parses invalid EDI")
    print("     (Validation errors will be caught in Part 4)\n")

    metadata = result['metadata']
    print(f"  Document Type:  {metadata['doc_type']}")
    print(f"  Total Segments: {result['statistics']['total_segments']}")

    # Show what's missing/wrong
    print("\n  Known issues in this file:")
    print("    • Missing N1 qualifier in element 02")
    print("    • Missing N3 address segment")
    print("    • CTT count mismatch")
    print("\n  These will be detected by the validation engine in Part 4.")


def main():
    """Run all demonstrations."""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "EDI PARSER DEMONSTRATION" + " " * 24 + "║")
    print("╚" + "═" * 68 + "╝")

    try:
        # Parse each document type
        demo_parse_850()
        demo_parse_856()
        demo_parse_810()

        # Show JSON export
        demo_json_export()

        # Show invalid handling
        demo_invalid_handling()

        # Summary
        print_header("Summary")
        print("\n  ✓ Parser successfully handles all EDI document types")
        print("  ✓ Metadata extraction working")
        print("  ✓ Segment parsing working")
        print("  ✓ Line number tracking working")
        print("  ✓ JSON export working")
        print("  ✓ Invalid documents parsed (ready for validation)")
        print("\n  🚀 Parser is ready for Part 3: Rules Engine\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
