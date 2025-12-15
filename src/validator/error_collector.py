"""
Error Collector Module

Collects and manages validation errors with context information.

Each error includes:
- Severity (ERROR, WARNING, INFO)
- Rule ID
- Segment information (ID, line number)
- Human-readable message
"""

from typing import List, Dict, Optional
from datetime import datetime


class ValidationError:
    """
    Represents a single validation error.
    """

    def __init__(
        self,
        rule_id: str,
        severity: str,
        message: str,
        segment_id: Optional[str] = None,
        line_number: Optional[int] = None,
        element_position: Optional[int] = None,
        expected_value: Optional[str] = None,
        actual_value: Optional[str] = None,
        context: Optional[Dict] = None
    ):
        """
        Initialize a validation error.

        Args:
            rule_id: Unique identifier of the rule that was violated
            severity: ERROR, WARNING, or INFO
            message: Human-readable error message
            segment_id: Segment identifier (e.g., "BEG", "PO1")
            line_number: Line number in the EDI file
            element_position: Element position within segment (0-indexed)
            expected_value: What was expected
            actual_value: What was found
            context: Additional context information
        """
        self.rule_id = rule_id
        self.severity = severity.upper()
        self.message = message
        self.segment_id = segment_id
        self.line_number = line_number
        self.element_position = element_position
        self.expected_value = expected_value
        self.actual_value = actual_value
        self.context = context or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        """
        Convert error to dictionary format.

        Returns:
            Dictionary representation of the error
        """
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "segment_id": self.segment_id,
            "line_number": self.line_number,
            "element_position": self.element_position,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "context": self.context
        }

    def __repr__(self) -> str:
        """String representation of error."""
        location = f"Line {self.line_number}" if self.line_number else "Unknown location"
        segment = f" ({self.segment_id})" if self.segment_id else ""
        return f"[{self.severity}] {location}{segment}: {self.message}"


class ErrorCollector:
    """
    Collects and organizes validation errors.

    Provides methods to add errors and generate statistics.
    """

    def __init__(self):
        """Initialize the error collector."""
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.info: List[ValidationError] = []

    def add_error(
        self,
        rule_id: str,
        severity: str,
        message: str,
        segment_id: Optional[str] = None,
        line_number: Optional[int] = None,
        element_position: Optional[int] = None,
        expected_value: Optional[str] = None,
        actual_value: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> None:
        """
        Add a validation error.

        Args:
            rule_id: Rule identifier
            severity: ERROR, WARNING, or INFO
            message: Error message
            segment_id: Segment identifier
            line_number: Line number in EDI file
            element_position: Element position
            expected_value: Expected value
            actual_value: Actual value
            context: Additional context
        """
        error = ValidationError(
            rule_id=rule_id,
            severity=severity,
            message=message,
            segment_id=segment_id,
            line_number=line_number,
            element_position=element_position,
            expected_value=expected_value,
            actual_value=actual_value,
            context=context
        )

        # Add to appropriate list
        if severity.upper() == "ERROR":
            self.errors.append(error)
        elif severity.upper() == "WARNING":
            self.warnings.append(error)
        else:
            self.info.append(error)

    def get_all_errors(self) -> List[ValidationError]:
        """
        Get all errors (ERROR, WARNING, INFO combined).

        Returns:
            List of all validation errors
        """
        return self.errors + self.warnings + self.info

    def get_errors_by_severity(self, severity: str) -> List[ValidationError]:
        """
        Get errors of a specific severity.

        Args:
            severity: ERROR, WARNING, or INFO

        Returns:
            List of errors with specified severity
        """
        severity = severity.upper()
        if severity == "ERROR":
            return self.errors
        elif severity == "WARNING":
            return self.warnings
        elif severity == "INFO":
            return self.info
        return []

    def get_errors_by_segment(self, segment_id: str) -> List[ValidationError]:
        """
        Get all errors for a specific segment.

        Args:
            segment_id: Segment identifier (e.g., "BEG")

        Returns:
            List of errors for this segment
        """
        return [
            error for error in self.get_all_errors()
            if error.segment_id == segment_id
        ]

    def get_errors_by_line(self, line_number: int) -> List[ValidationError]:
        """
        Get all errors for a specific line number.

        Args:
            line_number: Line number in EDI file

        Returns:
            List of errors for this line
        """
        return [
            error for error in self.get_all_errors()
            if error.line_number == line_number
        ]

    def has_errors(self) -> bool:
        """
        Check if there are any ERROR-severity violations.

        Returns:
            True if there are ERROR-level violations
        """
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """
        Check if there are any WARNING-severity violations.

        Returns:
            True if there are WARNING-level violations
        """
        return len(self.warnings) > 0

    def get_statistics(self) -> Dict:
        """
        Get error statistics.

        Returns:
            Dictionary with error counts and breakdown
        """
        all_errors = self.get_all_errors()

        # Count by severity
        severity_counts = {
            "ERROR": len(self.errors),
            "WARNING": len(self.warnings),
            "INFO": len(self.info)
        }

        # Count by segment
        segment_counts = {}
        for error in all_errors:
            if error.segment_id:
                segment_counts[error.segment_id] = segment_counts.get(error.segment_id, 0) + 1

        # Count by rule
        rule_counts = {}
        for error in all_errors:
            rule_counts[error.rule_id] = rule_counts.get(error.rule_id, 0) + 1

        return {
            "total_errors": len(all_errors),
            "by_severity": severity_counts,
            "by_segment": segment_counts,
            "by_rule": rule_counts,
            "is_compliant": len(self.errors) == 0
        }

    def to_dict(self) -> Dict:
        """
        Convert all errors to dictionary format.

        Returns:
            Dictionary with all errors and statistics
        """
        return {
            "statistics": self.get_statistics(),
            "errors": [error.to_dict() for error in self.get_all_errors()]
        }

    def clear(self) -> None:
        """Clear all collected errors."""
        self.errors = []
        self.warnings = []
        self.info = []

    def __len__(self) -> int:
        """Return total number of errors (all severities)."""
        return len(self.get_all_errors())

    def __repr__(self) -> str:
        """String representation of collector."""
        stats = self.get_statistics()
        return (
            f"ErrorCollector("
            f"errors={stats['by_severity']['ERROR']}, "
            f"warnings={stats['by_severity']['WARNING']}, "
            f"info={stats['by_severity']['INFO']})"
        )
