# EDI Parser — Usage Guide

## Overview

The EDI Parser converts raw X12 EDI documents into structured JSON format, making them easy to validate, query, and process.

## Quick Start

### Basic Usage

```python
from src.parser.edi_parser import EDIParser

# Create parser instance
parser = EDIParser()

# Parse from file
result = parser.parse_file("samples/edi_850_valid.txt")

# Access metadata
print(result['metadata']['doc_type'])  # "850"
print(result['metadata']['sender_id'])  # "SENDER"

# Access segments
for segment in result['segments']:
    print(f"Line {segment['line']}: {segment['segment_id']}")
```

### Parse from Text

```python
edi_text = """
ISA*00*          *00*          *ZZ*SENDER*ZZ*RECEIVER*231215*1430*U*00401*000000001*0*P*>~
GS*PO*SENDER*RECEIVER*20231215*1430*1*X*004010~
ST*850*0001~
BEG*00*NE*PO123456**20231215~
SE*3*0001~
GE*1*1~
IEA*1*000000001~
"""

parser = EDIParser()
result = parser.parse_text(edi_text)
```

## Output Structure

The parser returns a dictionary with three main sections:

```json
{
  "metadata": {
    "doc_type": "850",
    "version": "00401",
    "sender_id": "SENDER",
    "receiver_id": "RECEIVER",
    "interchange_date": "231215",
    "interchange_time": "1430",
    "control_numbers": {
      "interchange_control": "000000001",
      "group_control": "1",
      "transaction_control": "0001"
    },
    "functional_group": "PO"
  },
  "segments": [
    {
      "line": 1,
      "segment_id": "ISA",
      "elements": ["ISA", "00", "          ", ...],
      "element_count": 17,
      "raw": "ISA*00*          *00*..."
    },
    ...
  ],
  "statistics": {
    "total_segments": 21,
    "segment_counts": {
      "ISA": 1,
      "GS": 1,
      "ST": 1,
      "BEG": 1,
      "PO1": 2,
      ...
    },
    "has_envelope": true
  }
}
```

### Metadata Fields

| Field | Description | Example |
|-------|-------------|---------|
| `doc_type` | Transaction set type | "850", "856", "810" |
| `version` | X12 version | "00401" |
| `sender_id` | Sender identifier from ISA06 | "SENDER" |
| `receiver_id` | Receiver identifier from ISA08 | "RECEIVER" |
| `interchange_date` | Date from ISA09 | "231215" |
| `interchange_time` | Time from ISA10 | "1430" |
| `control_numbers` | ISA/GS/ST control numbers | {...} |
| `functional_group` | Functional group code from GS01 | "PO", "SH", "IN" |

### Segment Fields

| Field | Description |
|-------|-------------|
| `line` | Line number in original EDI (1-indexed) |
| `segment_id` | Segment identifier (first element) |
| `elements` | Array of all elements (including segment ID) |
| `element_count` | Number of elements |
| `raw` | Original segment string |

### Statistics Fields

| Field | Description |
|-------|-------------|
| `total_segments` | Total number of segments |
| `segment_counts` | Count of each segment type |
| `has_envelope` | True if ISA/GS/ST/SE/GE/IEA present |

## Common Operations

### Find Segments by ID

```python
parser = EDIParser()
parser.parse_file("samples/edi_850_valid.txt")

# Get all PO1 (line item) segments
po1_segments = parser.get_segments_by_id("PO1")

for po1 in po1_segments:
    quantity = po1['elements'][2]
    unit = po1['elements'][3]
    price = po1['elements'][4]
    print(f"Item: {quantity} {unit} @ ${price}")
```

### Get Specific Element Values

```python
parser = EDIParser()
parser.parse_file("samples/edi_850_valid.txt")

# Get PO number from BEG segment
po_number = parser.get_element_value("BEG", 3)
print(f"PO Number: {po_number}")  # "PO123456"

# Get date from BEG segment
po_date = parser.get_element_value("BEG", 5)
print(f"PO Date: {po_date}")  # "20231215"

# Handle repeating segments (get 2nd occurrence)
second_n1 = parser.get_element_value("N1", 2, occurrence=1)
```

### Export to JSON

```python
parser = EDIParser()
parser.parse_file("samples/edi_850_valid.txt")

# Pretty-printed JSON
json_str = parser.to_json(indent=2)
print(json_str)

# Compact JSON
compact_json = parser.to_json(indent=None)

# Save to file
with open("output/parsed_edi.json", "w") as f:
    f.write(json_str)
```

### Access Metadata

```python
parser = EDIParser()
parser.parse_file("samples/edi_850_valid.txt")

metadata = parser.get_metadata()
print(f"Document: {metadata['doc_type']}")
print(f"From: {metadata['sender_id']}")
print(f"To: {metadata['receiver_id']}")
print(f"Control: {metadata['control_numbers']['transaction_control']}")
```

### Access Statistics

```python
parser = EDIParser()
parser.parse_file("samples/edi_850_valid.txt")

stats = parser.get_statistics()
print(f"Total segments: {stats['total_segments']}")
print(f"Complete envelope: {stats['has_envelope']}")

# Count specific segments
po1_count = stats['segment_counts'].get('PO1', 0)
print(f"Number of line items: {po1_count}")
```

## Utility Functions

The `segment_utils` module provides low-level utilities:

### Normalize EDI Text

```python
from src.parser.segment_utils import normalize_edi_text

raw = "  ISA*00*  ~\n\nGS*PO*  ~  "
normalized = normalize_edi_text(raw)
```

### Split Segments

```python
from src.parser.segment_utils import split_segments

edi_text = "ISA*00*TEST~GS*PO*SENDER~ST*850*0001~"
segments = split_segments(edi_text)
# ['ISA*00*TEST', 'GS*PO*SENDER', 'ST*850*0001']
```

### Split Elements

```python
from src.parser.segment_utils import split_elements

segment = "BEG*00*NE*PO123456**20231215"
elements = split_elements(segment)
# ['BEG', '00', 'NE', 'PO123456', '', '20231215']
```

### Get Segment ID

```python
from src.parser.segment_utils import get_segment_id

segment = "BEG*00*NE*PO123456"
seg_id = get_segment_id(segment)
# 'BEG'
```

### Get Element Value

```python
from src.parser.segment_utils import get_element_value

segment = "BEG*00*NE*PO123456**20231215"
po_num = get_element_value(segment, 3)
# 'PO123456'

# With default for missing elements
empty = get_element_value(segment, 4, default="N/A")
# 'N/A'
```

## Error Handling

```python
from src.parser.edi_parser import EDIParser

parser = EDIParser()

try:
    result = parser.parse_file("nonexistent.txt")
except FileNotFoundError as e:
    print(f"File not found: {e}")

try:
    result = parser.parse_text("")
except ValueError as e:
    print(f"Invalid EDI: {e}")
```

## Performance Notes

- **Fast parsing**: ~1000 segments per second on standard hardware
- **Memory efficient**: Processes documents in single pass
- **Line tracking**: Minimal overhead for error reporting
- **No external dependencies**: Pure Python implementation

## Integration with Validation Engine

The parser output is designed to integrate seamlessly with the validation engine (Part 4):

```python
# Parse
parser = EDIParser()
parsed_edi = parser.parse_file("samples/edi_850_valid.txt")

# Validate (Part 4)
from src.validator.validation_engine import ValidationEngine
validator = ValidationEngine()
errors = validator.validate(parsed_edi, ruleset="850")
```

## Example: Extract Line Items from 850

```python
from src.parser.edi_parser import EDIParser

parser = EDIParser()
parser.parse_file("samples/edi_850_valid.txt")

# Get all line items
po1_segments = parser.get_segments_by_id("PO1")

line_items = []
for po1 in po1_segments:
    item = {
        'line_number': po1['line'],
        'sequence': po1['elements'][1],
        'quantity': po1['elements'][2],
        'unit': po1['elements'][3],
        'price': po1['elements'][4],
        'product_id_qualifier': po1['elements'][6],
        'product_id': po1['elements'][7]
    }
    line_items.append(item)

for item in line_items:
    print(f"Line {item['line_number']}: {item['quantity']} {item['unit']} "
          f"of {item['product_id']} @ ${item['price']}")
```

## Example: Extract Shipping Address from 850

```python
from src.parser.edi_parser import EDIParser

parser = EDIParser()
parser.parse_file("samples/edi_850_valid.txt")

# Find ST (Ship To) address
n1_segments = parser.get_segments_by_id("N1")

for idx, n1 in enumerate(n1_segments):
    qualifier = n1['elements'][1]

    if qualifier == "ST":
        # Get N3 and N4 that follow this N1
        all_segments = parser.parsed_data['segments']
        n1_idx = all_segments.index(n1)

        # N3 should be next
        n3 = all_segments[n1_idx + 1]
        n4 = all_segments[n1_idx + 2]

        address = {
            'name': n1['elements'][2],
            'street': n3['elements'][1],
            'city': n4['elements'][1],
            'state': n4['elements'][2],
            'zip': n4['elements'][3]
        }

        print(f"Ship To:")
        print(f"  {address['name']}")
        print(f"  {address['street']}")
        print(f"  {address['city']}, {address['state']} {address['zip']}")
```

## Running Tests

```bash
# Run parser tests
python tests/test_parser.py

# Run demonstration
python demo_parser.py
```

## Next Steps

- **Part 3**: Rule definitions and loading
- **Part 4**: Validation engine integration
- **Part 5**: Error reporting with line numbers
