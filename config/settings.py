"""
Configuration settings for EDI Compliance Rules Engine
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Directory paths
SRC_DIR = PROJECT_ROOT / "src"
RULES_DIR = SRC_DIR / "rules" / "rule_definitions"
SAMPLES_DIR = PROJECT_ROOT / "samples"
OUTPUT_DIR = PROJECT_ROOT / "output"
TESTS_DIR = PROJECT_ROOT / "tests"

# Rule definition paths
X12_CORE_RULES = RULES_DIR / "x12_core.json"
DOC_850_RULES = RULES_DIR / "doc_850.json"
DOC_856_RULES = RULES_DIR / "doc_856.json"
DOC_810_RULES = RULES_DIR / "doc_810.json"

# Retailer override paths
RETAILER_OVERRIDES_DIR = RULES_DIR / "retailer_overrides"
WALMART_RULES = RETAILER_OVERRIDES_DIR / "walmart.json"
AMAZON_RULES = RETAILER_OVERRIDES_DIR / "amazon.json"
TARGET_RULES = RETAILER_OVERRIDES_DIR / "target.json"

# Validation settings
SEVERITY_LEVELS = ["INFO", "WARNING", "ERROR"]
DEFAULT_SEVERITY = "ERROR"

# Parser settings
SEGMENT_TERMINATOR = "~"
ELEMENT_SEPARATOR = "*"
SUBELEMENT_SEPARATOR = ":"

# Output settings
DEFAULT_OUTPUT_FORMAT = "json"  # json, csv, txt
INCLUDE_TIMESTAMPS = True
