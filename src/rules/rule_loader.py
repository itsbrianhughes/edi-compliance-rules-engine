"""
Rule Loader Module

This module handles loading and merging EDI validation rules from JSON files.

Rule Priority (highest to lowest):
1. Retailer-specific rules
2. Document-specific rules
3. X12 core rules

When rules with the same rule_id exist at multiple levels, higher priority wins.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from copy import deepcopy

from config.settings import (
    X12_CORE_RULES,
    DOC_850_RULES,
    DOC_856_RULES,
    DOC_810_RULES,
    WALMART_RULES,
    AMAZON_RULES,
    TARGET_RULES
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RuleLoader:
    """
    Loads and merges EDI validation rules from JSON files.

    Handles rule priority: Retailer > Document > Core
    """

    def __init__(self):
        """Initialize the rule loader."""
        self.core_rules = {}
        self.document_rules = {}
        self.retailer_rules = {}
        self.merged_rules = {}

    def load_core_rules(self) -> Dict:
        """
        Load X12 core rules.

        Returns:
            Dictionary containing core rules
        """
        logger.info(f"Loading X12 core rules from {X12_CORE_RULES}")
        self.core_rules = self._load_json_file(X12_CORE_RULES)
        return self.core_rules

    def load_document_rules(self, doc_type: str) -> Dict:
        """
        Load document-specific rules for a given transaction type.

        Args:
            doc_type: Transaction set type (e.g., "850", "856", "810")

        Returns:
            Dictionary containing document rules

        Raises:
            ValueError: If document type is not supported
        """
        doc_type = str(doc_type).strip()

        rule_file_map = {
            "850": DOC_850_RULES,
            "856": DOC_856_RULES,
            "810": DOC_810_RULES
        }

        if doc_type not in rule_file_map:
            raise ValueError(
                f"Unsupported document type: {doc_type}. "
                f"Supported types: {list(rule_file_map.keys())}"
            )

        rule_file = rule_file_map[doc_type]
        logger.info(f"Loading {doc_type} document rules from {rule_file}")
        self.document_rules = self._load_json_file(rule_file)
        return self.document_rules

    def load_retailer_rules(self, retailer: str) -> Dict:
        """
        Load retailer-specific override rules.

        Args:
            retailer: Retailer name (e.g., "walmart", "amazon", "target")

        Returns:
            Dictionary containing retailer rules

        Raises:
            ValueError: If retailer is not supported
        """
        retailer = retailer.lower().strip()

        retailer_file_map = {
            "walmart": WALMART_RULES,
            "amazon": AMAZON_RULES,
            "target": TARGET_RULES
        }

        if retailer not in retailer_file_map:
            raise ValueError(
                f"Unsupported retailer: {retailer}. "
                f"Supported retailers: {list(retailer_file_map.keys())}"
            )

        rule_file = retailer_file_map[retailer]
        logger.info(f"Loading {retailer} retailer rules from {rule_file}")
        self.retailer_rules = self._load_json_file(rule_file)
        return self.retailer_rules

    def load_rules(self, doc_type: str, retailer: Optional[str] = None) -> Dict:
        """
        Load and merge all applicable rules.

        Args:
            doc_type: Transaction set type (e.g., "850", "856", "810")
            retailer: Optional retailer name (e.g., "walmart", "amazon")

        Returns:
            Merged ruleset with all applicable rules

        Example:
            >>> loader = RuleLoader()
            >>> rules = loader.load_rules("850", "walmart")
            >>> print(rules['ruleset_info']['name'])
        """
        # Load core rules
        core = self.load_core_rules()

        # Load document rules
        doc = self.load_document_rules(doc_type)

        # Load retailer rules if specified
        ret = {}
        if retailer:
            ret = self.load_retailer_rules(retailer)

        # Merge in priority order: core -> document -> retailer
        self.merged_rules = self._merge_rulesets(core, doc, ret, doc_type, retailer)

        return self.merged_rules

    def _load_json_file(self, file_path: Path) -> Dict:
        """
        Load a JSON rule file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON as dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Rule file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return data
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {file_path}: {e}")
                raise

    def _merge_rulesets(self, core: Dict, doc: Dict, ret: Dict,
                       doc_type: str, retailer: Optional[str]) -> Dict:
        """
        Merge multiple rulesets with proper priority.

        Priority: Retailer > Document > Core

        Args:
            core: Core rules dictionary
            doc: Document rules dictionary
            ret: Retailer rules dictionary
            doc_type: Document type for metadata
            retailer: Retailer name for metadata

        Returns:
            Merged ruleset dictionary
        """
        merged = {
            "ruleset_info": {
                "name": f"Merged Ruleset: {doc_type}",
                "doc_type": doc_type,
                "retailer": retailer if retailer else "none",
                "rulesets_applied": []
            },
            "required_segments": [],
            "element_rules": [],
            "conditional_rules": [],
            "cross_segment_rules": []
        }

        # Track which rulesets were applied
        if core:
            merged["ruleset_info"]["rulesets_applied"].append("x12_core")
        if doc:
            merged["ruleset_info"]["rulesets_applied"].append(f"doc_{doc_type}")
        if ret:
            merged["ruleset_info"]["rulesets_applied"].append(f"retailer_{retailer}")

        # Merge each rule category
        rule_categories = [
            "required_segments",
            "element_rules",
            "conditional_rules",
            "cross_segment_rules"
        ]

        for category in rule_categories:
            # Start with core rules
            category_rules = {}

            # Add core rules
            for rule in core.get(category, []):
                rule_id = rule.get("rule_id")
                if rule_id:
                    category_rules[rule_id] = deepcopy(rule)

            # Override with document rules
            for rule in doc.get(category, []):
                rule_id = rule.get("rule_id")
                if rule_id:
                    category_rules[rule_id] = deepcopy(rule)

            # Override with retailer rules (highest priority)
            for rule in ret.get(category, []):
                rule_id = rule.get("rule_id")
                if rule_id:
                    # Check if rule applies to this document type
                    applies_to = rule.get("applies_to_doc_types", [])
                    if not applies_to or doc_type in applies_to:
                        category_rules[rule_id] = deepcopy(rule)

            # Convert back to list
            merged[category] = list(category_rules.values())

        # Apply retailer overrides
        if ret and "overrides" in ret:
            merged = self._apply_overrides(merged, ret["overrides"])

        # Add optional categories if present
        optional_categories = ["segment_sequences", "business_rules"]
        for category in optional_categories:
            if category in doc:
                merged[category] = doc[category]
            if category in ret:
                merged[category] = merged.get(category, []) + ret[category]

        return merged

    def _apply_overrides(self, ruleset: Dict, overrides: List[Dict]) -> Dict:
        """
        Apply retailer-specific overrides to rules.

        Args:
            ruleset: The merged ruleset
            overrides: List of override specifications

        Returns:
            Ruleset with overrides applied
        """
        for override in overrides:
            rule_id = override.get("rule_id")
            override_type = override.get("override_type")

            if not rule_id or not override_type:
                continue

            # Find the rule to override
            for category in ruleset.keys():
                if not isinstance(ruleset[category], list):
                    continue

                for rule in ruleset[category]:
                    if rule.get("rule_id") == rule_id:
                        if override_type == "severity_escalation":
                            rule["severity"] = override["new_severity"]
                            logger.info(
                                f"Override applied: {rule_id} severity "
                                f"escalated to {override['new_severity']}"
                            )
                        elif override_type == "add_allowed_value":
                            if "validations" in rule and "allowed_values" in rule["validations"]:
                                rule["validations"]["allowed_values"].extend(
                                    override.get("new_allowed_values", [])
                                )
                                logger.info(
                                    f"Override applied: {rule_id} added allowed values"
                                )

        return ruleset

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict]:
        """
        Find a specific rule by its ID in the merged ruleset.

        Args:
            rule_id: The rule identifier to find

        Returns:
            Rule dictionary if found, None otherwise
        """
        if not self.merged_rules:
            return None

        for category in self.merged_rules.keys():
            if not isinstance(self.merged_rules[category], list):
                continue

            for rule in self.merged_rules[category]:
                if rule.get("rule_id") == rule_id:
                    return rule

        return None

    def get_rules_by_segment(self, segment_id: str) -> List[Dict]:
        """
        Get all rules that apply to a specific segment.

        Args:
            segment_id: The segment identifier (e.g., "BEG", "PO1")

        Returns:
            List of rules applying to this segment
        """
        if not self.merged_rules:
            return []

        matching_rules = []

        # Check required_segments
        for rule in self.merged_rules.get("required_segments", []):
            if rule.get("segment_id") == segment_id:
                matching_rules.append(rule)

        # Check element_rules
        for rule in self.merged_rules.get("element_rules", []):
            if rule.get("segment_id") == segment_id:
                matching_rules.append(rule)

        # Check conditional_rules
        for rule in self.merged_rules.get("conditional_rules", []):
            condition = rule.get("condition", {})
            if condition.get("if_segment") == segment_id:
                matching_rules.append(rule)

        return matching_rules

    def get_statistics(self) -> Dict:
        """
        Get statistics about the loaded ruleset.

        Returns:
            Dictionary with rule counts by category
        """
        if not self.merged_rules:
            return {}

        stats = {
            "total_rules": 0,
            "by_category": {},
            "by_severity": {"ERROR": 0, "WARNING": 0, "INFO": 0}
        }

        for category, rules in self.merged_rules.items():
            if isinstance(rules, list):
                count = len(rules)
                stats["by_category"][category] = count
                stats["total_rules"] += count

                # Count by severity
                for rule in rules:
                    severity = rule.get("severity")
                    if severity in stats["by_severity"]:
                        stats["by_severity"][severity] += 1

        return stats

    def to_json(self, indent: int = 2) -> str:
        """
        Export merged rules as JSON string.

        Args:
            indent: Number of spaces for indentation

        Returns:
            JSON string representation
        """
        return json.dumps(self.merged_rules, indent=indent)

    def __repr__(self) -> str:
        """String representation of loader."""
        if not self.merged_rules:
            return "RuleLoader(no rules loaded)"

        info = self.merged_rules.get("ruleset_info", {})
        doc_type = info.get("doc_type", "unknown")
        retailer = info.get("retailer", "none")
        total = sum(
            len(v) for v in self.merged_rules.values()
            if isinstance(v, list)
        )

        return f"RuleLoader(doc={doc_type}, retailer={retailer}, rules={total})"
