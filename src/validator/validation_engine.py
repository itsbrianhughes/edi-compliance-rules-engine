"""
Main Validation Engine

Orchestrates all validators and produces compliance reports.

Usage:
    from src.parser.edi_parser import EDIParser
    from src.rules.rule_loader import RuleLoader
    from src.validator.validation_engine import ValidationEngine

    # Parse EDI
    parser = EDIParser()
    parsed_edi = parser.parse_file("samples/edi_850_valid.txt")

    # Load rules
    loader = RuleLoader()
    rules = loader.load_rules("850", "walmart")

    # Validate
    engine = ValidationEngine()
    result = engine.validate(parsed_edi, rules)

    # Check compliance
    if result.is_compliant():
        print("✓ Document is compliant")
    else:
        print(f"✗ Found {result.error_count()} errors")
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from .error_collector import ErrorCollector
from .rule_evaluators import (
    RequiredSegmentValidator,
    ElementValidator,
    ConditionalRuleValidator,
    CrossSegmentValidator
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationResult:
    """
    Represents the result of a validation run.
    """

    def __init__(
        self,
        error_collector: ErrorCollector,
        parsed_edi: Dict,
        rules: Dict,
        validation_time: float
    ):
        """
        Initialize validation result.

        Args:
            error_collector: ErrorCollector with all errors
            parsed_edi: Parsed EDI document
            rules: Rules that were applied
            validation_time: Time taken to validate (seconds)
        """
        self.error_collector = error_collector
        self.parsed_edi = parsed_edi
        self.rules = rules
        self.validation_time = validation_time
        self.timestamp = datetime.now()

    def is_compliant(self) -> bool:
        """
        Check if document is compliant (no ERROR-level violations).

        Returns:
            True if compliant (no ERRORs)
        """
        return not self.error_collector.has_errors()

    def error_count(self) -> int:
        """
        Get count of ERROR-level violations.

        Returns:
            Number of ERROR violations
        """
        return len(self.error_collector.errors)

    def warning_count(self) -> int:
        """
        Get count of WARNING-level violations.

        Returns:
            Number of WARNING violations
        """
        return len(self.error_collector.warnings)

    def total_issues(self) -> int:
        """
        Get total count of all issues (ERROR + WARNING + INFO).

        Returns:
            Total number of issues
        """
        return len(self.error_collector)

    def get_errors(self):
        """Get all ERROR-level violations."""
        return self.error_collector.errors

    def get_warnings(self):
        """Get all WARNING-level violations."""
        return self.error_collector.warnings

    def get_all_issues(self):
        """Get all issues (ERROR + WARNING + INFO)."""
        return self.error_collector.get_all_errors()

    def get_summary(self) -> Dict:
        """
        Get validation summary.

        Returns:
            Dictionary with summary information
        """
        metadata = self.parsed_edi.get("metadata", {})
        stats = self.error_collector.get_statistics()

        return {
            "document_info": {
                "doc_type": metadata.get("doc_type"),
                "sender": metadata.get("sender_id"),
                "receiver": metadata.get("receiver_id"),
                "control_number": metadata.get("control_numbers", {}).get("transaction_control")
            },
            "validation_info": {
                "timestamp": self.timestamp.isoformat(),
                "validation_time_seconds": round(self.validation_time, 3),
                "rules_applied": self.rules.get("ruleset_info", {}).get("name"),
                "retailer": self.rules.get("ruleset_info", {}).get("retailer")
            },
            "compliance_status": {
                "is_compliant": self.is_compliant(),
                "total_issues": self.total_issues(),
                "errors": self.error_count(),
                "warnings": self.warning_count()
            },
            "error_statistics": stats
        }

    def to_dict(self) -> Dict:
        """
        Convert result to dictionary format.

        Returns:
            Complete validation result as dictionary
        """
        return {
            "summary": self.get_summary(),
            "issues": [error.to_dict() for error in self.get_all_issues()]
        }

    def __repr__(self) -> str:
        """String representation of result."""
        status = "COMPLIANT" if self.is_compliant() else "NON-COMPLIANT"
        return (
            f"ValidationResult("
            f"status={status}, "
            f"errors={self.error_count()}, "
            f"warnings={self.warning_count()})"
        )


class ValidationEngine:
    """
    Main validation engine that orchestrates all validators.
    """

    def __init__(self):
        """Initialize the validation engine."""
        self.error_collector = None
        self.validators_initialized = False

    def validate(
        self,
        parsed_edi: Dict,
        rules: Dict,
        retailer: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate a parsed EDI document against rules.

        Args:
            parsed_edi: Parsed EDI document from EDIParser
            rules: Merged ruleset from RuleLoader
            retailer: Optional retailer name (for logging)

        Returns:
            ValidationResult with all errors and statistics

        Example:
            >>> engine = ValidationEngine()
            >>> result = engine.validate(parsed_edi, rules)
            >>> if result.is_compliant():
            ...     print("Document is compliant")
        """
        start_time = datetime.now()

        # Initialize error collector
        self.error_collector = ErrorCollector()

        # Initialize validators
        required_seg_validator = RequiredSegmentValidator(self.error_collector)
        element_validator = ElementValidator(self.error_collector)
        conditional_validator = ConditionalRuleValidator(self.error_collector)
        cross_segment_validator = CrossSegmentValidator(self.error_collector)

        # Log validation start
        doc_type = parsed_edi.get("metadata", {}).get("doc_type")
        retailer_info = f" ({retailer})" if retailer else ""
        logger.info(f"Starting validation: {doc_type}{retailer_info}")

        # Run validators for each rule category
        self._validate_category(
            required_seg_validator,
            parsed_edi,
            rules.get("required_segments", []),
            "Required Segments"
        )

        self._validate_category(
            element_validator,
            parsed_edi,
            rules.get("element_rules", []),
            "Element Rules"
        )

        self._validate_category(
            conditional_validator,
            parsed_edi,
            rules.get("conditional_rules", []),
            "Conditional Rules"
        )

        self._validate_category(
            cross_segment_validator,
            parsed_edi,
            rules.get("cross_segment_rules", []),
            "Cross-Segment Rules"
        )

        # Calculate validation time
        end_time = datetime.now()
        validation_time = (end_time - start_time).total_seconds()

        # Log completion
        stats = self.error_collector.get_statistics()
        logger.info(
            f"Validation complete: {stats['by_severity']['ERROR']} errors, "
            f"{stats['by_severity']['WARNING']} warnings "
            f"({validation_time:.3f}s)"
        )

        # Return result
        return ValidationResult(
            error_collector=self.error_collector,
            parsed_edi=parsed_edi,
            rules=rules,
            validation_time=validation_time
        )

    def _validate_category(
        self, validator, parsed_edi: Dict, rules: list, category_name: str
    ) -> None:
        """
        Run a specific validator category.

        Args:
            validator: Validator instance
            parsed_edi: Parsed EDI document
            rules: Rules for this category
            category_name: Name of category (for logging)
        """
        if not rules:
            logger.debug(f"No rules for {category_name}, skipping")
            return

        logger.debug(f"Validating {len(rules)} {category_name} rules")

        try:
            validator.validate(parsed_edi, rules)
        except Exception as e:
            logger.error(f"Error during {category_name} validation: {e}")
            # Add a system error
            self.error_collector.add_error(
                rule_id="SYSTEM_ERROR",
                severity="ERROR",
                message=f"System error during {category_name} validation: {str(e)}"
            )

    def validate_file(
        self,
        edi_file_path: str,
        doc_type: str,
        retailer: Optional[str] = None
    ) -> ValidationResult:
        """
        Convenience method to parse and validate a file in one call.

        Args:
            edi_file_path: Path to EDI file
            doc_type: Document type (e.g., "850", "856", "810")
            retailer: Optional retailer name

        Returns:
            ValidationResult

        Example:
            >>> engine = ValidationEngine()
            >>> result = engine.validate_file("samples/edi_850_valid.txt", "850", "walmart")
        """
        from src.parser.edi_parser import EDIParser
        from src.rules.rule_loader import RuleLoader

        # Parse file
        parser = EDIParser()
        parsed_edi = parser.parse_file(edi_file_path)

        # Load rules
        loader = RuleLoader()
        rules = loader.load_rules(doc_type, retailer)

        # Validate
        return self.validate(parsed_edi, rules, retailer)

    def __repr__(self) -> str:
        """String representation of engine."""
        return "ValidationEngine()"
