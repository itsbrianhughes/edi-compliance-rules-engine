# Quick Start Guide

Get up and running with the EDI Compliance Rules Engine in under 5 minutes.

## Installation (2 minutes)

```bash
# Clone repository
git clone https://github.com/itsbrianhughes/PROJECT-4-EDI-COMPLIANCE-RULES-ENGINE.git
cd PROJECT-4-EDI-COMPLIANCE-RULES-ENGINE

# Install dependencies
pip install -r requirements.txt
```

## Quick Validation Examples

### Example 1: Validate a Valid Purchase Order (Programmatic)

```python
from src.validator.validation_engine import ValidationEngine

# Create validation engine
engine = ValidationEngine()

# Validate 850 PO with base rules
result = engine.validate_file("samples/edi_850_valid.txt", "850")

# Check results
print(f"Compliant: {result.is_compliant()}")
print(f"Errors: {result.error_count()}")
print(f"Warnings: {result.warning_count()}")
```

**Output:**
```
INFO:src.rules.rule_loader:Loading X12 core rules from ...
INFO:src.rules.rule_loader:Loading 850 document rules from ...
INFO:src.validator.validation_engine:Starting validation: 850
INFO:src.validator.validation_engine:Validation complete: 0 errors, 0 warnings (0.001s)
Compliant: True
Errors: 0
Warnings: 0
```

### Example 2: Validate with Walmart Rules

```python
from src.validator.validation_engine import ValidationEngine

engine = ValidationEngine()

# Same document, but with Walmart's stricter rules
result = engine.validate_file("samples/edi_850_valid.txt", "850", "walmart")

print(f"Compliant: {result.is_compliant()}")
print(f"Errors: {result.error_count()}")

if not result.is_compliant():
    print("\nFirst 3 errors:")
    for error in result.get_errors()[:3]:
        print(f"  - Line {error.line_number}: {error.message}")
```

**Output:**
```
INFO:src.rules.rule_loader:Loading X12 core rules from ...
INFO:src.rules.rule_loader:Loading 850 document rules from ...
INFO:src.rules.rule_loader:Loading walmart retailer rules from ...
INFO:src.rules.rule_loader:Override applied: 850_COND_N1_ST_ADDRESS severity escalated to ERROR
INFO:src.validator.validation_engine:Starting validation: 850 (walmart)
INFO:src.validator.validation_engine:Validation complete: 9 errors, 0 warnings (0.001s)
Compliant: False
Errors: 9

First 3 errors:
  - Line 12: PO1 element 06 (Product/Service ID) is required but missing or empty
  - Line 12: PO1 element 07 (Product/Service ID Qualifier) is required but missing or empty
  - Line 16: PO1 element 06 (Product/Service ID) is required but missing or empty
```

### Example 3: Generate Full Report

```python
from src.validator.validation_engine import ValidationEngine
from src.reporting.report_generator import ReportGenerator

# Validate
engine = ValidationEngine()
result = engine.validate_file("samples/edi_850_invalid.txt", "850", "target")

# Generate report
generator = ReportGenerator(result)

# Print dashboard
print(generator.generate_dashboard())
```

**Output:**
```
╔════════════════════════════════════════════════════════════════════╗
║                    VALIDATION DASHBOARD                            ║
╚════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│ STATUS: ✗ NON-COMPLIANT                                          │
└─────────────────────────────────────────────────────────────────┘

┌─── QUICK STATS ─────────────────────────────────────────────────┐
│  Total Issues:    7                                            │
│  Errors:          7                                            │
│  Warnings:        0                                            │
└─────────────────────────────────────────────────────────────────┘

┌─── DOCUMENT INFO ───────────────────────────────────────────────┐
│  Type:          850                                              │
│  Sender:        SENDER                                           │
│  Receiver:      RECEIVER                                         │
└─────────────────────────────────────────────────────────────────┘

┌─── TOP SEGMENTS WITH ISSUES ────────────────────────────────────┐
│  N1       │███████████                   │   3    │
│  PO1      │███████                       │   2    │
│  CTT      │███                           │   1    │
│  BEG      │███                           │   1    │
└─────────────────────────────────────────────────────────────────┘

┌─── VALIDATION INFO ─────────────────────────────────────────────┐
│  Time:           0.000s                                          │
│  Retailer:      TARGET                                           │
└─────────────────────────────────────────────────────────────────┘

┌─── RECOMMENDED ACTIONS ─────────────────────────────────────────┐
│  1. Review ERROR-level violations (blocking issues)            │
│  2. Address mandatory segment/element requirements             │
│  3. Verify retailer-specific formatting rules                  │
│  4. Re-validate after corrections                              │
└─────────────────────────────────────────────────────────────────┘
```

### Example 4: Export All Report Formats

```python
from src.validator.validation_engine import ValidationEngine
from src.reporting.report_generator import ReportGenerator

# Validate
engine = ValidationEngine()
result = engine.validate_file("samples/edi_856_valid.txt", "856", "amazon")

# Generate all reports
generator = ReportGenerator(result)
files = generator.save_all_formats("output", "amazon_856_validation")

print("Reports saved:")
for format_name, file_path in files.items():
    print(f"  {format_name}: {file_path}")
```

**Output:**
```
INFO:src.reporting.report_generator:Report saved: output/amazon_856_validation.txt (text format)
INFO:src.reporting.report_generator:Report saved: output/amazon_856_validation.json (json format)
INFO:src.reporting.report_generator:Report saved: output/amazon_856_validation.csv (csv format)
INFO:src.reporting.report_generator:Report saved: output/amazon_856_validation_dashboard.txt (dashboard format)
INFO:src.reporting.report_generator:All reports saved to: output
Reports saved:
  text: output/amazon_856_validation.txt
  json: output/amazon_856_validation.json
  csv: output/amazon_856_validation.csv
  dashboard: output/amazon_856_validation_dashboard.txt
```

## Web UI Examples

### Launch Web UI

```bash
streamlit run src/ui/streamlit_app.py
```

**Output:**
```
Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

### Web UI Workflow

1. **Open browser** → Navigate to `http://localhost:8501`

2. **Configure validation**
   - Select Document Type: `850 - Purchase Order`
   - Select Retailer: `Walmart`

3. **Upload EDI file**
   - Click "Browse files" or drag-and-drop
   - Select your EDI file

4. **Run validation**
   - Click "🚀 Run Validation" button
   - Wait for spinner (usually < 1 second)

5. **View results**
   - **Dashboard tab**: Visual summary
   - **Detailed Report tab**: Full text report
   - **Issues List tab**: Interactive issue browser with filters
   - **Downloads tab**: Download all 4 report formats

## Testing Examples

### Run All Tests

```bash
# Parser tests
python tests/test_parser.py
```

**Output:**
```
==================================================
Running Parser Tests
==================================================

✓ test_normalize_edi_text passed
✓ test_split_segments passed
✓ test_split_elements passed
✓ test_get_segment_id passed
✓ test_parse_850_valid passed
✓ test_parse_850_invalid passed
✓ test_parse_856_valid passed
✓ test_parse_810_valid passed
✓ test_metadata_extraction passed
✓ test_performance passed

==================================================
✓ All tests passed!
==================================================
```

### Run Demonstrations

```bash
# Parser demonstration
python demo_parser.py
```

**Output:**
```
╔════════════════════════════════════════════════════════════════════╗
║                    EDI PARSER DEMONSTRATION                        ║
╚════════════════════════════════════════════════════════════════════╝

======================================================================
  DEMO 1: Parse 850 Purchase Order
======================================================================

  Parsing: samples/edi_850_valid.txt

  ✓ Parsed successfully

  Document Metadata:
    Document Type:    850
    Sender:           SENDER
    Receiver:         RECEIVER
    Control Number:   0001
    Envelope:         Complete ✓

  Statistics:
    Total Segments:   21
    ISA: 1, GS: 1, ST: 1, BEG: 1, REF: 1, DTM: 1, ...

  First 5 Segments:
    1. ISA (16 elements) - ISA*00*          *00*          *ZZ*SENDER...
    2. GS (8 elements) - GS*PO*SENDER*RECEIVER*20231215*1430*1*X*004010~
    3. ST (2 elements) - ST*850*0001~
    4. BEG (5 elements) - BEG*00*NE*PO123456**20231215~
    5. REF (2 elements) - REF*DP*DEPT001~
...
```

## Batch Processing Example

Validate multiple files in a loop:

```python
from src.validator.validation_engine import ValidationEngine
from pathlib import Path

engine = ValidationEngine()

# Define files to validate
validations = [
    ("samples/edi_850_valid.txt", "850", "walmart"),
    ("samples/edi_850_valid.txt", "850", "amazon"),
    ("samples/edi_850_valid.txt", "850", "target"),
    ("samples/edi_856_valid.txt", "856", None),
    ("samples/edi_810_valid.txt", "810", None),
]

print("Batch Validation Results:")
print("-" * 70)

for file_path, doc_type, retailer in validations:
    result = engine.validate_file(file_path, doc_type, retailer)

    retailer_str = retailer.upper() if retailer else "Base"
    status = "✅ PASS" if result.is_compliant() else "❌ FAIL"

    print(f"{status}  {Path(file_path).name:25} | {doc_type} + {retailer_str:8} | "
          f"{result.error_count()} errors, {result.warning_count()} warnings")

print("-" * 70)
```

**Output:**
```
Batch Validation Results:
----------------------------------------------------------------------
✅ PASS  edi_850_valid.txt        | 850 + Base     | 0 errors, 0 warnings
❌ FAIL  edi_850_valid.txt        | 850 + WALMART  | 9 errors, 0 warnings
✅ PASS  edi_850_valid.txt        | 850 + AMAZON   | 0 errors, 0 warnings
❌ FAIL  edi_850_valid.txt        | 850 + TARGET   | 9 errors, 0 warnings
✅ PASS  edi_856_valid.txt        | 856 + Base     | 0 errors, 0 warnings
✅ PASS  edi_810_valid.txt        | 810 + Base     | 0 errors, 0 warnings
----------------------------------------------------------------------
```

## Parsing Example

Parse and explore EDI structure:

```python
from src.parser.edi_parser import EDIParser

parser = EDIParser()
parsed = parser.parse_file("samples/edi_850_valid.txt")

# Access metadata
metadata = parsed['metadata']
print(f"Document Type: {metadata['doc_type']}")
print(f"Sender: {metadata['sender']}")
print(f"Receiver: {metadata['receiver']}")

# Access segments
segments = parsed['segments']
print(f"\nTotal Segments: {len(segments)}")

# Find all PO1 (line item) segments
po1_segments = [s for s in segments if s['segment_id'] == 'PO1']
print(f"Line Items: {len(po1_segments)}")

for po1 in po1_segments:
    quantity = po1['elements'][1]
    uom = po1['elements'][2]
    unit_price = po1['elements'][4]
    product_id = po1['elements'][9]

    print(f"  - {product_id}: {quantity} {uom} @ ${unit_price} each")
```

**Output:**
```
Document Type: 850
Sender: SENDER
Receiver: RECEIVER

Total Segments: 21
Line Items: 2
  - WIDGET123: 100 EA @ $12.50 each
  - GADGET456: 50 EA @ $25.00 each
```

## Rule Exploration Example

Explore loaded rules:

```python
from src.rules.rule_loader import RuleLoader

loader = RuleLoader()

# Load 850 + Walmart rules
rules = loader.load_rules("850", "walmart")

# Count rules by category
print("Rule Counts:")
print(f"  Required Segments: {len(rules.get('required_segments', []))}")
print(f"  Element Rules: {len(rules.get('element_rules', []))}")
print(f"  Conditional Rules: {len(rules.get('conditional_rules', []))}")
print(f"  Cross-Segment Rules: {len(rules.get('cross_segment_rules', []))}")

# Show severity distribution
from collections import Counter

all_rules = []
for category in ['required_segments', 'element_rules', 'conditional_rules', 'cross_segment_rules']:
    all_rules.extend(rules.get(category, []))

severities = Counter(rule.get('severity', 'N/A') for rule in all_rules)

print("\nSeverity Distribution:")
for severity, count in severities.items():
    print(f"  {severity}: {count}")
```

**Output:**
```
INFO:src.rules.rule_loader:Loading X12 core rules from ...
INFO:src.rules.rule_loader:Loading 850 document rules from ...
INFO:src.rules.rule_loader:Loading walmart retailer rules from ...
INFO:src.rules.rule_loader:Override applied: 850_COND_N1_ST_ADDRESS severity escalated to ERROR

Rule Counts:
  Required Segments: 6
  Element Rules: 31
  Conditional Rules: 4
  Cross-Segment Rules: 3

Severity Distribution:
  ERROR: 45
  WARNING: 11
```

## Common Workflows

### Workflow 1: Pre-Transmission Validation

```python
"""
Validate EDI before sending to trading partner
"""
from src.validator.validation_engine import ValidationEngine
from src.reporting.report_generator import ReportGenerator

# Validate before sending
engine = ValidationEngine()
result = engine.validate_file("my_purchase_order.txt", "850", "walmart")

if result.is_compliant():
    print("✅ Document is ready for transmission")
    # Proceed with sending
else:
    print(f"❌ Document has {result.error_count()} errors")
    print("Please fix the following issues:\n")

    for error in result.get_errors():
        print(f"Line {error.line_number}: {error.message}")

    # Generate report for developers
    generator = ReportGenerator(result)
    generator.save_report("output/pre_transmission_report.txt", format="text")
    print("\nDetailed report saved to: output/pre_transmission_report.txt")
```

### Workflow 2: Trading Partner Onboarding

```python
"""
Test documents against retailer requirements during onboarding
"""
from src.validator.validation_engine import ValidationEngine

engine = ValidationEngine()

retailers = ["walmart", "amazon", "target"]
test_file = "samples/edi_850_valid.txt"

print("Trading Partner Compatibility Check")
print("=" * 50)

for retailer in retailers:
    result = engine.validate_file(test_file, "850", retailer)

    if result.is_compliant():
        print(f"✅ {retailer.upper():8} - Compatible")
    else:
        print(f"❌ {retailer.upper():8} - {result.error_count()} issues to fix")

print("=" * 50)
```

### Workflow 3: Quality Assurance

```python
"""
Validate all EDI files in a directory
"""
from src.validator.validation_engine import ValidationEngine
from pathlib import Path

engine = ValidationEngine()
edi_dir = Path("incoming_edi")

results = []

for edi_file in edi_dir.glob("*.txt"):
    # Determine doc type from filename (e.g., "850_PO_12345.txt")
    doc_type = edi_file.name[:3]

    result = engine.validate_file(str(edi_file), doc_type)
    results.append((edi_file.name, result.is_compliant(), result.error_count()))

# Summary report
print("Quality Assurance Report")
print("=" * 60)
passed = sum(1 for _, compliant, _ in results if compliant)
total = len(results)

for filename, compliant, errors in results:
    status = "✅" if compliant else "❌"
    print(f"{status} {filename:30} ({errors} errors)")

print("=" * 60)
print(f"Pass Rate: {passed}/{total} ({passed/total*100:.1f}%)")
```

## Next Steps

Now that you've seen the basics:

1. **Explore the Web UI** - Try different document types and retailers
2. **Review Documentation** - Check `docs/` for detailed guides
3. **Customize Rules** - Add your own validation rules in `src/rules/rule_definitions/`
4. **Integrate into Workflow** - Use the validation engine in your EDI pipeline
5. **Deploy to Production** - See `docs/deployment_guide.md`

## Getting Help

- **Documentation**: See `docs/` directory
- **Examples**: Run demo scripts (`demo_*.py`)
- **Tests**: Check `tests/` for usage patterns
- **Issues**: Report bugs on GitHub

## Quick Reference

| Task | Command |
|------|---------|
| Run Web UI | `streamlit run src/ui/streamlit_app.py` |
| Run Tests | `python tests/test_validator.py` |
| Validate File (CLI) | `python -c "from src.validator.validation_engine import ValidationEngine; engine = ValidationEngine(); result = engine.validate_file('file.txt', '850'); print(result.is_compliant())"` |
| Generate Reports | `python demo_reports.py` |
| View UI Demo | `python demo_ui_workflow.py` |

---

**You're ready to start validating! 🚀**
