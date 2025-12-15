# Rule Schema Definition

This document defines the JSON schema for validation rules.

## Rule File Structure

Each rule file (e.g., `doc_850.json`) contains:

```json
{
  "ruleset_info": {
    "name": "X12 850 Purchase Order Rules",
    "version": "1.0",
    "doc_type": "850",
    "scope": "document"
  },
  "required_segments": [...],
  "segment_cardinality": [...],
  "element_rules": [...],
  "conditional_rules": [...],
  "cross_segment_rules": [...]
}
```

## Rule Categories

### 1. Required Segments

**Purpose:** Specify segments that must appear in the document

**Schema:**
```json
{
  "rule_id": "REQ_SEG_BEG",
  "segment_id": "BEG",
  "description": "Beginning Segment for Purchase Order is required",
  "severity": "ERROR",
  "min_occurrences": 1,
  "max_occurrences": 1
}
```

**Fields:**
- `rule_id` — Unique identifier for the rule
- `segment_id` — The X12 segment code (e.g., "BEG", "N1", "PO1")
- `description` — Human-readable explanation
- `severity` — "ERROR", "WARNING", or "INFO"
- `min_occurrences` — Minimum times segment must appear (0 = optional)
- `max_occurrences` — Maximum times segment can appear (null = unlimited)

### 2. Segment Cardinality

**Purpose:** Enforce occurrence limits for repeating segments

**Schema:**
```json
{
  "rule_id": "CARD_PO1",
  "segment_id": "PO1",
  "description": "At least one PO1 line item is required",
  "severity": "ERROR",
  "min_occurrences": 1,
  "max_occurrences": null
}
```

### 3. Element Rules

**Purpose:** Validate individual elements within segments

**Schema:**
```json
{
  "rule_id": "BEG_01_TYPE",
  "segment_id": "BEG",
  "element_position": "01",
  "description": "BEG01 must be a valid transaction set purpose code",
  "severity": "ERROR",
  "validations": {
    "data_type": "ID",
    "min_length": 2,
    "max_length": 2,
    "allowed_values": ["00", "01", "02", "03", "04", "05"]
  }
}
```

**Validation Types:**
- `data_type` — AN (Alphanumeric), N0 (Numeric), ID (Identifier), DT (Date), TM (Time)
- `min_length` / `max_length` — String length constraints
- `allowed_values` — Enumerated list of valid codes
- `regex` — Pattern matching (optional)

### 4. Conditional Rules

**Purpose:** Enforce "if-then" logic (e.g., if segment X exists, then segment Y is required)

**Schema:**
```json
{
  "rule_id": "COND_N1_N4",
  "description": "If N1 segment exists, N4 (city/state/zip) is required",
  "severity": "ERROR",
  "condition": {
    "if_segment": "N1",
    "if_element": "01",
    "if_value": "ST"
  },
  "then": {
    "required_segment": "N4",
    "within_loop": "N1"
  }
}
```

**Logic:**
- `condition` — The triggering scenario
- `then` — The requirement that must be met
- `within_loop` — Scope constraint (segment must appear in same loop)

### 5. Cross-Segment Rules

**Purpose:** Validate relationships between segments (e.g., CTT count must match number of PO1 segments)

**Schema:**
```json
{
  "rule_id": "CROSS_CTT_COUNT",
  "description": "CTT segment count must match actual line item count",
  "severity": "WARNING",
  "segments_involved": ["CTT", "PO1"],
  "validation_logic": {
    "type": "count_match",
    "source_segment": "PO1",
    "target_segment": "CTT",
    "target_element": "01"
  }
}
```

**Common Cross-Segment Validations:**
- `count_match` — Segment count must equal value in another segment
- `reference_match` — Reference number must exist in another segment
- `date_sequence` — Date in segment X must be before/after date in segment Y

## Rule Priority & Merging

When multiple rulesets are loaded (core + document + retailer), rules are merged with this priority:

1. **Retailer Override** (highest priority)
2. **Document-Specific Rules**
3. **X12 Core Rules** (lowest priority)

**Merge Logic:**
- If `rule_id` matches, higher priority rule replaces lower
- If `rule_id` is unique, rule is added to combined ruleset
- `severity` can be escalated (e.g., WARNING → ERROR) but not downgraded

## Example: Complete Ruleset

`src/rules/rule_definitions/doc_850.json` (excerpt):

```json
{
  "ruleset_info": {
    "name": "X12 850 Purchase Order Rules",
    "version": "1.0",
    "doc_type": "850",
    "scope": "document"
  },
  "required_segments": [
    {
      "rule_id": "REQ_SEG_BEG",
      "segment_id": "BEG",
      "description": "Beginning Segment for Purchase Order is required",
      "severity": "ERROR",
      "min_occurrences": 1,
      "max_occurrences": 1
    },
    {
      "rule_id": "REQ_SEG_PO1",
      "segment_id": "PO1",
      "description": "At least one baseline item data segment required",
      "severity": "ERROR",
      "min_occurrences": 1,
      "max_occurrences": null
    }
  ],
  "conditional_rules": [
    {
      "rule_id": "COND_N1_N3_N4",
      "description": "If N1 segment has ST qualifier, N3 and N4 are required",
      "severity": "ERROR",
      "condition": {
        "if_segment": "N1",
        "if_element": "01",
        "if_value": "ST"
      },
      "then": {
        "required_segments": ["N3", "N4"],
        "within_loop": "N1"
      }
    }
  ]
}
```

## Retailer Override Example

`src/rules/rule_definitions/retailer_overrides/walmart.json`:

```json
{
  "ruleset_info": {
    "name": "Walmart EDI Requirements",
    "version": "1.0",
    "retailer": "walmart",
    "scope": "retailer_override"
  },
  "required_segments": [
    {
      "rule_id": "WALMART_REQ_DTM_010",
      "segment_id": "DTM",
      "description": "Walmart requires requested delivery date (DTM*010)",
      "severity": "ERROR",
      "min_occurrences": 1,
      "max_occurrences": 1,
      "element_filters": {
        "01": "010"
      }
    }
  ],
  "element_rules": [
    {
      "rule_id": "WALMART_BEG04_FORMAT",
      "segment_id": "BEG",
      "element_position": "03",
      "description": "Walmart PO numbers must start with WM prefix",
      "severity": "ERROR",
      "validations": {
        "regex": "^WM[0-9]{10}$"
      }
    }
  ]
}
```

## Severity Levels

- **ERROR** — Violates X12 standard or will cause transaction rejection
- **WARNING** — Non-standard but may be accepted; review recommended
- **INFO** — Best practice suggestion; does not affect compliance

## Future Rule Types (V2)

- **Mathematical Rules** — Sum validations, calculated fields
- **Business Logic Rules** — Industry-specific requirements
- **Custom Functions** — User-defined validation scripts
