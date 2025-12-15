"""
Report Generator Module

Main interface for generating compliance reports in various formats.

Usage:
    from src.validator.validation_engine import ValidationEngine
    from src.reporting.report_generator import ReportGenerator

    # Validate
    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_850_valid.txt", "850")

    # Generate reports
    generator = ReportGenerator(result)

    # Text report
    text_report = generator.generate_text_report()
    print(text_report)

    # JSON export
    json_report = generator.generate_json_report()

    # CSV export
    csv_report = generator.generate_csv_report()

    # Dashboard
    dashboard = generator.generate_dashboard()

    # Save to file
    generator.save_report("output/report.txt", format="text")
"""

import logging
from pathlib import Path
from typing import Optional

from .formatters import TextFormatter, JSONFormatter, CSVFormatter, DashboardFormatter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates compliance reports from validation results.
    """

    def __init__(self, validation_result):
        """
        Initialize the report generator.

        Args:
            validation_result: ValidationResult instance from validation engine
        """
        self.validation_result = validation_result

    def generate_text_report(self) -> str:
        """
        Generate a human-readable text report.

        Returns:
            Formatted text report
        """
        return TextFormatter.format_report(self.validation_result)

    def generate_json_report(self, indent: int = 2) -> str:
        """
        Generate a JSON report.

        Args:
            indent: Number of spaces for indentation

        Returns:
            JSON string
        """
        return JSONFormatter.format_report(self.validation_result, indent=indent)

    def generate_csv_report(self) -> str:
        """
        Generate a CSV report of issues.

        Returns:
            CSV string
        """
        return CSVFormatter.format_report(self.validation_result)

    def generate_dashboard(self) -> str:
        """
        Generate a summary dashboard.

        Returns:
            Dashboard string
        """
        return DashboardFormatter.format_report(self.validation_result)

    def save_report(
        self,
        output_path: str,
        format: str = "text",
        indent: Optional[int] = 2
    ) -> None:
        """
        Save report to a file.

        Args:
            output_path: Path where report should be saved
            format: Report format ('text', 'json', 'csv', 'dashboard')
            indent: Indentation for JSON (only used if format='json')

        Raises:
            ValueError: If format is not supported
        """
        format = format.lower()

        if format == "text":
            content = self.generate_text_report()
        elif format == "json":
            content = self.generate_json_report(indent=indent)
        elif format == "csv":
            content = self.generate_csv_report()
        elif format == "dashboard":
            content = self.generate_dashboard()
        else:
            raise ValueError(
                f"Unsupported format: {format}. "
                f"Supported formats: text, json, csv, dashboard"
            )

        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Report saved: {output_path} ({format} format)")

    def save_all_formats(self, base_path: str, base_name: str = "report") -> dict:
        """
        Save reports in all formats.

        Args:
            base_path: Directory where reports should be saved
            base_name: Base filename (without extension)

        Returns:
            Dictionary mapping format to file path

        Example:
            >>> generator.save_all_formats("output", "validation_report")
            {
                'text': 'output/validation_report.txt',
                'json': 'output/validation_report.json',
                'csv': 'output/validation_report.csv',
                'dashboard': 'output/validation_report_dashboard.txt'
            }
        """
        base_dir = Path(base_path)
        base_dir.mkdir(parents=True, exist_ok=True)

        files = {}

        # Text report
        text_path = base_dir / f"{base_name}.txt"
        self.save_report(str(text_path), format="text")
        files['text'] = str(text_path)

        # JSON report
        json_path = base_dir / f"{base_name}.json"
        self.save_report(str(json_path), format="json")
        files['json'] = str(json_path)

        # CSV report
        csv_path = base_dir / f"{base_name}.csv"
        self.save_report(str(csv_path), format="csv")
        files['csv'] = str(csv_path)

        # Dashboard
        dashboard_path = base_dir / f"{base_name}_dashboard.txt"
        self.save_report(str(dashboard_path), format="dashboard")
        files['dashboard'] = str(dashboard_path)

        logger.info(f"All reports saved to: {base_path}")

        return files

    def print_dashboard(self) -> None:
        """Print the dashboard to console."""
        print(self.generate_dashboard())

    def print_summary(self) -> None:
        """Print a brief summary to console."""
        summary = self.validation_result.get_summary()
        status = summary['compliance_status']

        symbol = "✓" if status['is_compliant'] else "✗"
        status_text = "COMPLIANT" if status['is_compliant'] else "NON-COMPLIANT"

        print(f"\n{symbol} {status_text}")
        print(f"   Errors: {status['errors']}, Warnings: {status['warnings']}")

        if not status['is_compliant']:
            errors = self.validation_result.get_errors()
            print(f"\n   First error: {errors[0].message}" if errors else "")

    def __repr__(self) -> str:
        """String representation of generator."""
        is_compliant = self.validation_result.is_compliant()
        error_count = self.validation_result.error_count()

        return (
            f"ReportGenerator("
            f"compliant={is_compliant}, "
            f"errors={error_count})"
        )
