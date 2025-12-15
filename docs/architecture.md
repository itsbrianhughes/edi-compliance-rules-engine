# EDI Compliance Rules Engine — Architecture

## System Overview

The EDI Compliance Rules Engine is a modular validation system built on a layered architecture pattern.

```
┌─────────────────────────────────────────────────────────┐
│                     INPUT LAYER                         │
│  (Raw EDI text input — file upload or paste)           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    PARSER LAYER                         │
│  • Segment splitting (by ~)                            │
│  • Element extraction (by *)                           │
│  • JSON structuring                                    │
│  • Line number tracking for error reporting           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    RULES LAYER                          │
│  • X12 Core Rules (x12_core.json)                      │
│  • Document-Specific Rules (doc_850.json, etc.)        │
│  • Retailer Override Rules (walmart.json, etc.)        │
│  • Rule Loading & Merging Logic                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 VALIDATION ENGINE                       │
│  • Required Segment Validator                          │
│  • Cardinality Validator                              │
│  • Element Type/Length Validator                      │
│  • Conditional Rule Evaluator                         │
│  • Cross-Segment Validator                            │
│  • Error Collector                                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   REPORTING LAYER                       │
│  • Error Aggregation                                   │
│  • Severity Classification (INFO/WARNING/ERROR)        │
│  • Human-Readable Summary                             │
│  • JSON Export                                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                      UI LAYER                           │
│  • File Upload Interface (Streamlit)                   │
│  • Result Display                                      │
│  • Report Download                                     │
└─────────────────────────────────────────────────────────┘
```

## Module Responsibilities

### `src/parser/`
**Purpose:** Convert raw EDI text into structured, queryable JSON

**Key Components:**
- `edi_parser.py` — Main parser class
- `segment_utils.py` — Segment/element splitting utilities

**Outputs:**
```json
{
  "segments": [
    {
      "id": "ISA",
      "elements": ["00", "          ", "00", ...],
      "line": 1
    },
    ...
  ],
  "metadata": {
    "doc_type": "850",
    "control_number": "0001"
  }
}
```

### `src/rules/`
**Purpose:** Define and load validation rules in a data-driven way

**Key Components:**
- `rule_loader.py` — Load and merge rulesets
- `rule_definitions/` — JSON rule files organized by scope:
  - `x12_core.json` — Universal X12 requirements
  - `doc_850.json` — 850-specific rules
  - `retailer_overrides/walmart.json` — Retailer-specific rules

**Rule Priority:** Retailer > Document > Core

### `src/validator/`
**Purpose:** Execute rules against parsed EDI and collect errors

**Key Components:**
- `validation_engine.py` — Orchestrates all validators
- `rule_evaluators.py` — Individual rule evaluation functions
- `error_collector.py` — Aggregates errors with context

**Validation Categories:**
1. Required segments
2. Segment cardinality (min/max occurrences)
3. Element data types and lengths
4. Conditional rules (if X, then Y required)
5. Cross-segment dependencies

### `src/reporting/`
**Purpose:** Format validation results for human and machine consumption

**Key Components:**
- `report_generator.py` — Main report builder
- `formatters.py` — Output format handlers (JSON, CSV, text)

**Report Structure:**
```json
{
  "summary": {
    "file": "edi_850_invalid.txt",
    "doc_type": "850",
    "total_errors": 5,
    "severity_counts": {
      "ERROR": 3,
      "WARNING": 2,
      "INFO": 0
    }
  },
  "errors": [
    {
      "severity": "ERROR",
      "segment": "N1",
      "line": 7,
      "rule_id": "N1_REQ_QUALIFIER",
      "message": "N1 segment missing required qualifier in element 02"
    }
  ]
}
```

### `src/ui/`
**Purpose:** Provide web interface for validation

**Key Components:**
- `streamlit_app.py` — Main Streamlit app

**Features:**
- File upload
- EDI text paste
- Retailer selection
- Result visualization
- Report download

## Design Principles

### 1. Modularity
Each layer can be tested and modified independently

### 2. Data-Driven Rules
No hardcoded validation logic — all rules in JSON files

### 3. Extensibility
- Add new document types: create `doc_XXX.json`
- Add new retailers: create `retailer_overrides/XXX.json`
- Add new validation types: extend `rule_evaluators.py`

### 4. Clear Error Context
Every error includes:
- Severity level
- Segment ID
- Line number
- Rule ID
- Human-readable message

### 5. Separation of Concerns
- Parser knows nothing about rules
- Validator knows nothing about output format
- Rules know nothing about UI

## Data Flow Example

**Input:** `edi_850_invalid.txt`

1. **Parser** reads file → JSON structure
2. **Rule Loader** loads `x12_core.json` + `doc_850.json` + `walmart.json`
3. **Validator** runs each rule category:
   - Checks for missing N1*92 qualifier → ERROR
   - Checks CTT segment count mismatch → WARNING
4. **Report Generator** creates summary + error list
5. **UI** displays results, allows download

## Future Enhancements (Post-V1)

- Database storage for validation history
- Batch file processing
- Custom rule builder UI
- API endpoint for programmatic validation
- Integration with ERP/WMS systems
