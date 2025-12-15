"""
Main EDI Parser Module

This module provides the primary EDIParser class that converts raw EDI text
into structured JSON format suitable for validation and processing.

The parser:
- Splits EDI into segments
- Extracts elements and sub-elements
- Tracks line numbers for error reporting
- Extracts metadata (document type, control numbers, sender/receiver)
- Produces clean JSON output
"""

import json
from typing import Dict, List, Optional
from pathlib import Path

from .segment_utils import (
    normalize_edi_text,
    split_segments,
    split_elements,
    get_segment_id,
    get_element_value,
    extract_control_numbers
)


class EDIParser:
    """
    Lightweight EDI parser that converts X12 EDI documents to structured JSON.

    This parser handles:
    - Segment splitting
    - Element extraction
    - Line number tracking
    - Metadata extraction
    - JSON structuring

    Example:
        >>> parser = EDIParser()
        >>> result = parser.parse_file("samples/edi_850_valid.txt")
        >>> print(result['metadata']['doc_type'])
        '850'
    """

    def __init__(self):
        """Initialize the EDI parser."""
        self.raw_text = ""
        self.segments = []
        self.parsed_data = {}

    def parse_file(self, file_path: str) -> Dict:
        """
        Parse an EDI file from disk.

        Args:
            file_path: Path to the EDI file

        Returns:
            Parsed EDI document as dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or invalid
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"EDI file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        if not raw_text.strip():
            raise ValueError(f"EDI file is empty: {file_path}")

        return self.parse_text(raw_text)

    def parse_text(self, edi_text: str) -> Dict:
        """
        Parse EDI text directly.

        Args:
            edi_text: Raw EDI document as string

        Returns:
            Parsed EDI document as dictionary with structure:
            {
                'metadata': {...},
                'segments': [...],
                'statistics': {...}
            }

        Raises:
            ValueError: If EDI text is invalid
        """
        if not edi_text or not edi_text.strip():
            raise ValueError("EDI text is empty")

        # Store raw text
        self.raw_text = edi_text

        # Normalize and split into segments
        normalized_text = normalize_edi_text(edi_text)
        self.segments = split_segments(normalized_text)

        if not self.segments:
            raise ValueError("No segments found in EDI text")

        # Build structured data
        self.parsed_data = self._build_parsed_structure()

        return self.parsed_data

    def _build_parsed_structure(self) -> Dict:
        """
        Build the complete parsed data structure.

        Returns:
            Dictionary with metadata, segments, and statistics
        """
        # Extract metadata from envelope segments
        metadata = self._extract_metadata()

        # Parse all segments with line numbers
        parsed_segments = self._parse_all_segments()

        # Calculate statistics
        statistics = self._calculate_statistics(parsed_segments)

        return {
            'metadata': metadata,
            'segments': parsed_segments,
            'statistics': statistics
        }

    def _extract_metadata(self) -> Dict:
        """
        Extract metadata from ISA, GS, and ST segments.

        Returns:
            Dictionary with document metadata
        """
        metadata = {
            'doc_type': '',
            'version': '',
            'sender_id': '',
            'receiver_id': '',
            'interchange_date': '',
            'interchange_time': '',
            'control_numbers': {},
            'functional_group': ''
        }

        for segment_str in self.segments:
            seg_id = get_segment_id(segment_str)

            if seg_id == 'ISA':
                # ISA segment contains interchange-level metadata
                metadata['sender_id'] = get_element_value(segment_str, 6).strip()
                metadata['receiver_id'] = get_element_value(segment_str, 8).strip()
                metadata['interchange_date'] = get_element_value(segment_str, 9)
                metadata['interchange_time'] = get_element_value(segment_str, 10)
                metadata['version'] = get_element_value(segment_str, 12)

            elif seg_id == 'GS':
                # GS segment contains functional group info
                metadata['functional_group'] = get_element_value(segment_str, 1)

            elif seg_id == 'ST':
                # ST segment contains transaction set type
                metadata['doc_type'] = get_element_value(segment_str, 1)

        # Extract control numbers
        metadata['control_numbers'] = extract_control_numbers(self.segments)

        return metadata

    def _parse_all_segments(self) -> List[Dict]:
        """
        Parse all segments into structured dictionaries with line tracking.

        Returns:
            List of parsed segment dictionaries
        """
        parsed_segments = []
        line_number = 1

        for segment_str in self.segments:
            elements = split_elements(segment_str)

            if not elements:
                continue

            segment_dict = {
                'line': line_number,
                'segment_id': elements[0],
                'elements': elements,
                'element_count': len(elements),
                'raw': segment_str
            }

            parsed_segments.append(segment_dict)
            line_number += 1

        return parsed_segments

    def _calculate_statistics(self, segments: List[Dict]) -> Dict:
        """
        Calculate statistics about the parsed document.

        Args:
            segments: List of parsed segment dictionaries

        Returns:
            Dictionary with document statistics
        """
        # Count segments by type
        segment_counts = {}
        for seg in segments:
            seg_id = seg['segment_id']
            segment_counts[seg_id] = segment_counts.get(seg_id, 0) + 1

        return {
            'total_segments': len(segments),
            'segment_counts': segment_counts,
            'has_envelope': self._has_complete_envelope(segments)
        }

    def _has_complete_envelope(self, segments: List[Dict]) -> bool:
        """
        Check if document has complete ISA/GS/ST envelope structure.

        Args:
            segments: List of parsed segments

        Returns:
            True if all envelope segments are present
        """
        segment_ids = {seg['segment_id'] for seg in segments}

        required_envelope = {'ISA', 'GS', 'ST', 'SE', 'GE', 'IEA'}

        return required_envelope.issubset(segment_ids)

    def get_segments_by_id(self, segment_id: str) -> List[Dict]:
        """
        Get all segments with a specific ID.

        Args:
            segment_id: The segment identifier to find (e.g., "PO1", "N1")

        Returns:
            List of matching segment dictionaries
        """
        if not self.parsed_data:
            return []

        return [
            seg for seg in self.parsed_data.get('segments', [])
            if seg['segment_id'] == segment_id
        ]

    def get_element_value(self, segment_id: str, element_position: int,
                         occurrence: int = 0, default: str = "") -> str:
        """
        Get an element value from a specific segment.

        Args:
            segment_id: The segment to find (e.g., "BEG")
            element_position: Position of element (0 = segment ID)
            occurrence: Which occurrence to use if segment repeats (0-indexed)
            default: Default value if not found

        Returns:
            Element value or default
        """
        segments = self.get_segments_by_id(segment_id)

        if occurrence < len(segments):
            segment = segments[occurrence]
            elements = segment['elements']

            if element_position < len(elements):
                value = elements[element_position].strip()
                return value if value else default

        return default

    def to_json(self, indent: int = 2) -> str:
        """
        Export parsed data as JSON string.

        Args:
            indent: Number of spaces for indentation (None for compact)

        Returns:
            JSON string representation
        """
        return json.dumps(self.parsed_data, indent=indent)

    def to_dict(self) -> Dict:
        """
        Get parsed data as dictionary.

        Returns:
            Parsed data dictionary
        """
        return self.parsed_data

    def get_metadata(self) -> Dict:
        """
        Get document metadata.

        Returns:
            Metadata dictionary
        """
        return self.parsed_data.get('metadata', {})

    def get_statistics(self) -> Dict:
        """
        Get document statistics.

        Returns:
            Statistics dictionary
        """
        return self.parsed_data.get('statistics', {})

    def __repr__(self) -> str:
        """String representation of parser."""
        if not self.parsed_data:
            return "EDIParser(unparsed)"

        metadata = self.parsed_data.get('metadata', {})
        doc_type = metadata.get('doc_type', 'unknown')
        seg_count = len(self.parsed_data.get('segments', []))

        return f"EDIParser(doc_type={doc_type}, segments={seg_count})"
