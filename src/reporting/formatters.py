"""
Report Formatters Module

Provides formatters for different output types:
- Human-readable text
- JSON
- CSV
- Summary dashboard
"""

import json
import csv
from io import StringIO
from typing import Dict, List
from datetime import datetime


class TextFormatter:
    """
    Formats validation results as human-readable text.
    """

    @staticmethod
    def format_report(validation_result) -> str:
        """
        Generate a human-readable text report.

        Args:
            validation_result: ValidationResult instance

        Returns:
            Formatted text report as string
        """
        summary = validation_result.get_summary()
        issues = validation_result.get_all_issues()

        lines = []

        # Header
        lines.append("=" * 70)
        lines.append("EDI COMPLIANCE VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append("")

        # Document Information
        doc_info = summary['document_info']
        lines.append("DOCUMENT INFORMATION")
        lines.append("-" * 70)
        lines.append(f"  Document Type:     {doc_info.get('doc_type', 'N/A')}")
        lines.append(f"  Sender:            {doc_info.get('sender', 'N/A')}")
        lines.append(f"  Receiver:          {doc_info.get('receiver', 'N/A')}")
        lines.append(f"  Control Number:    {doc_info.get('control_number', 'N/A')}")
        lines.append("")

        # Validation Information
        val_info = summary['validation_info']
        lines.append("VALIDATION INFORMATION")
        lines.append("-" * 70)
        lines.append(f"  Timestamp:         {val_info.get('timestamp', 'N/A')}")
        lines.append(f"  Validation Time:   {val_info.get('validation_time_seconds', 0):.3f}s")
        lines.append(f"  Rules Applied:     {val_info.get('rules_applied', 'N/A')}")
        if val_info.get('retailer') and val_info['retailer'] != 'none':
            lines.append(f"  Retailer:          {val_info['retailer'].upper()}")
        lines.append("")

        # Compliance Status
        status = summary['compliance_status']
        compliance_symbol = "✓" if status['is_compliant'] else "✗"
        compliance_text = "COMPLIANT" if status['is_compliant'] else "NON-COMPLIANT"

        lines.append("COMPLIANCE STATUS")
        lines.append("-" * 70)
        lines.append(f"  Status:            {compliance_symbol} {compliance_text}")
        lines.append(f"  Total Issues:      {status['total_issues']}")
        lines.append(f"    Errors:          {status['errors']}")
        lines.append(f"    Warnings:        {status['warnings']}")
        lines.append("")

        # Issues by Segment (if any)
        if issues:
            stats = summary['error_statistics']
            by_segment = stats.get('by_segment', {})

            if by_segment:
                lines.append("ISSUES BY SEGMENT")
                lines.append("-" * 70)
                for segment, count in sorted(by_segment.items()):
                    lines.append(f"  {segment:10} {count:3} issue(s)")
                lines.append("")

        # Detailed Issues
        if issues:
            lines.append("DETAILED ISSUES")
            lines.append("=" * 70)
            lines.append("")

            # Group by severity
            errors = [i for i in issues if i.severity == "ERROR"]
            warnings = [i for i in issues if i.severity == "WARNING"]
            info = [i for i in issues if i.severity == "INFO"]

            if errors:
                lines.append(f"ERRORS ({len(errors)})")
                lines.append("-" * 70)
                for idx, error in enumerate(errors, 1):
                    lines.extend(TextFormatter._format_issue(idx, error))
                lines.append("")

            if warnings:
                lines.append(f"WARNINGS ({len(warnings)})")
                lines.append("-" * 70)
                for idx, warning in enumerate(warnings, 1):
                    lines.extend(TextFormatter._format_issue(idx, warning))
                lines.append("")

            if info:
                lines.append(f"INFORMATIONAL ({len(info)})")
                lines.append("-" * 70)
                for idx, item in enumerate(info, 1):
                    lines.extend(TextFormatter._format_issue(idx, item))
                lines.append("")
        else:
            lines.append("NO ISSUES FOUND")
            lines.append("")
            lines.append("✓ All validation rules passed successfully.")
            lines.append("")

        # Footer
        lines.append("=" * 70)
        lines.append("END OF REPORT")
        lines.append("=" * 70)

        return "\n".join(lines)

    @staticmethod
    def _format_issue(number: int, issue) -> List[str]:
        """
        Format a single issue.

        Args:
            number: Issue number
            issue: ValidationError instance

        Returns:
            List of formatted lines
        """
        lines = []

        # Issue header
        location = f"Line {issue.line_number}" if issue.line_number else "Unknown location"
        segment = f" | Segment: {issue.segment_id}" if issue.segment_id else ""
        element = f" | Element: {issue.element_position:02d}" if issue.element_position is not None else ""

        lines.append(f"{number}. {location}{segment}{element}")
        lines.append(f"   Rule:    {issue.rule_id}")
        lines.append(f"   Message: {issue.message}")

        if issue.expected_value or issue.actual_value:
            if issue.expected_value:
                lines.append(f"   Expected: {issue.expected_value}")
            if issue.actual_value:
                lines.append(f"   Actual:   {issue.actual_value}")

        lines.append("")  # Blank line between issues

        return lines


class JSONFormatter:
    """
    Formats validation results as JSON.
    """

    @staticmethod
    def format_report(validation_result, indent: int = 2) -> str:
        """
        Generate a JSON report.

        Args:
            validation_result: ValidationResult instance
            indent: Number of spaces for indentation

        Returns:
            JSON string
        """
        report_dict = validation_result.to_dict()

        # Add formatted timestamp
        report_dict['generated_at'] = datetime.now().isoformat()

        return json.dumps(report_dict, indent=indent)


class CSVFormatter:
    """
    Formats validation results as CSV.
    """

    @staticmethod
    def format_report(validation_result) -> str:
        """
        Generate a CSV report of issues.

        Args:
            validation_result: ValidationResult instance

        Returns:
            CSV string
        """
        issues = validation_result.get_all_issues()

        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Severity',
            'Rule ID',
            'Segment',
            'Line Number',
            'Element Position',
            'Message',
            'Expected Value',
            'Actual Value'
        ])

        # Write issues
        for issue in issues:
            writer.writerow([
                issue.severity,
                issue.rule_id,
                issue.segment_id or '',
                issue.line_number or '',
                issue.element_position if issue.element_position is not None else '',
                issue.message,
                issue.expected_value or '',
                issue.actual_value or ''
            ])

        return output.getvalue()


class DashboardFormatter:
    """
    Formats validation results as a summary dashboard.
    """

    @staticmethod
    def format_report(validation_result) -> str:
        """
        Generate a summary dashboard (text-based).

        Args:
            validation_result: ValidationResult instance

        Returns:
            Dashboard string
        """
        summary = validation_result.get_summary()

        lines = []

        # Header
        lines.append("╔" + "═" * 68 + "╗")
        lines.append("║" + " " * 20 + "VALIDATION DASHBOARD" + " " * 28 + "║")
        lines.append("╚" + "═" * 68 + "╝")
        lines.append("")

        # Status Box
        status = summary['compliance_status']
        is_compliant = status['is_compliant']

        if is_compliant:
            status_line = "│ STATUS: ✓ COMPLIANT                                             │"
            color_border = "┌─────────────────────────────────────────────────────────────────┐"
        else:
            status_line = "│ STATUS: ✗ NON-COMPLIANT                                          │"
            color_border = "┌─────────────────────────────────────────────────────────────────┐"

        lines.append(color_border)
        lines.append(status_line)
        lines.append("└─────────────────────────────────────────────────────────────────┘")
        lines.append("")

        # Quick Stats
        lines.append("┌─── QUICK STATS ─────────────────────────────────────────────────┐")
        lines.append(f"│  Total Issues:  {status['total_issues']:3}                                            │")
        lines.append(f"│  Errors:        {status['errors']:3}                                            │")
        lines.append(f"│  Warnings:      {status['warnings']:3}                                            │")
        lines.append("└─────────────────────────────────────────────────────────────────┘")
        lines.append("")

        # Document Info
        doc_info = summary['document_info']
        lines.append("┌─── DOCUMENT INFO ───────────────────────────────────────────────┐")
        lines.append(f"│  Type:          {doc_info.get('doc_type', 'N/A'):10}                                 │")
        lines.append(f"│  Sender:        {(doc_info.get('sender', 'N/A')[:20]):20}                   │")
        lines.append(f"│  Receiver:      {(doc_info.get('receiver', 'N/A')[:20]):20}                   │")
        lines.append("└─────────────────────────────────────────────────────────────────┘")
        lines.append("")

        # Issues by Segment (Top 5)
        stats = summary['error_statistics']
        by_segment = stats.get('by_segment', {})

        if by_segment:
            lines.append("┌─── TOP SEGMENTS WITH ISSUES ────────────────────────────────────┐")

            sorted_segments = sorted(by_segment.items(), key=lambda x: x[1], reverse=True)[:5]

            for seg_id, count in sorted_segments:
                bar = "█" * min(count, 30)
                lines.append(f"│  {seg_id:8} │{bar:30}│ {count:3}    │")

            lines.append("└─────────────────────────────────────────────────────────────────┘")
            lines.append("")

        # Validation Info
        val_info = summary['validation_info']
        lines.append("┌─── VALIDATION INFO ─────────────────────────────────────────────┐")
        lines.append(f"│  Time:          {val_info.get('validation_time_seconds', 0):6.3f}s                                 │")

        if val_info.get('retailer') and val_info['retailer'] != 'none':
            retailer = val_info['retailer'].upper()
            lines.append(f"│  Retailer:      {retailer:20}                   │")

        lines.append("└─────────────────────────────────────────────────────────────────┘")
        lines.append("")

        # Action Items
        if not is_compliant:
            lines.append("┌─── RECOMMENDED ACTIONS ─────────────────────────────────────────┐")
            lines.append("│  1. Review ERROR-level violations (blocking issues)            │")
            lines.append("│  2. Address mandatory segment/element requirements             │")
            lines.append("│  3. Verify retailer-specific formatting rules                  │")
            lines.append("│  4. Re-validate after corrections                              │")
            lines.append("└─────────────────────────────────────────────────────────────────┘")
        else:
            lines.append("┌─── NEXT STEPS ──────────────────────────────────────────────────┐")
            lines.append("│  ✓ Document passed all validation rules                        │")
            lines.append("│  ✓ Ready for transmission                                      │")
            lines.append("└─────────────────────────────────────────────────────────────────┘")

        return "\n".join(lines)
