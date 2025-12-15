"""
Utility functions for EDI segment and element manipulation.

This module provides low-level utilities for:
- Splitting segments from raw EDI text
- Extracting elements from segments
- Handling sub-elements
- Normalizing whitespace and delimiters
"""

from typing import List, Dict, Optional
from config.settings import SEGMENT_TERMINATOR, ELEMENT_SEPARATOR, SUBELEMENT_SEPARATOR


def normalize_edi_text(raw_text: str) -> str:
    """
    Normalize raw EDI text by removing extra whitespace and ensuring consistent line endings.

    Args:
        raw_text: Raw EDI document as string

    Returns:
        Normalized EDI text with consistent formatting
    """
    # Remove leading/trailing whitespace
    normalized = raw_text.strip()

    # Ensure consistent line endings (convert all to \n)
    normalized = normalized.replace('\r\n', '\n').replace('\r', '\n')

    # Remove extra blank lines but preserve segment structure
    lines = [line.strip() for line in normalized.split('\n') if line.strip()]

    return '\n'.join(lines)


def split_segments(edi_text: str, segment_terminator: str = SEGMENT_TERMINATOR) -> List[str]:
    """
    Split EDI text into individual segments.

    Args:
        edi_text: Normalized EDI text
        segment_terminator: Character that terminates segments (default: ~)

    Returns:
        List of segment strings (without terminators)
    """
    # Normalize first
    normalized = normalize_edi_text(edi_text)

    # Split by segment terminator
    segments = normalized.split(segment_terminator)

    # Filter out empty segments and strip whitespace
    segments = [seg.strip() for seg in segments if seg.strip()]

    return segments


def split_elements(segment: str, element_separator: str = ELEMENT_SEPARATOR) -> List[str]:
    """
    Split a segment into its elements.

    Args:
        segment: Single EDI segment (e.g., "BEG*00*NE*PO123456**20231215")
        element_separator: Character that separates elements (default: *)

    Returns:
        List of element strings (including empty strings for missing elements)

    Example:
        >>> split_elements("BEG*00*NE*PO123456**20231215")
        ['BEG', '00', 'NE', 'PO123456', '', '20231215']
    """
    # Split by element separator
    # Important: Don't filter empty strings - they represent optional elements
    elements = segment.split(element_separator)

    return elements


def split_subelements(element: str, subelement_separator: str = SUBELEMENT_SEPARATOR) -> List[str]:
    """
    Split an element into sub-elements (composite elements).

    Args:
        element: Single element that may contain sub-elements
        subelement_separator: Character that separates sub-elements (default: :)

    Returns:
        List of sub-element strings, or single-item list if no sub-elements

    Example:
        >>> split_subelements("CODE1:CODE2:CODE3")
        ['CODE1', 'CODE2', 'CODE3']
        >>> split_subelements("SIMPLE_ELEMENT")
        ['SIMPLE_ELEMENT']
    """
    if subelement_separator in element:
        return element.split(subelement_separator)
    return [element]


def get_segment_id(segment: str) -> str:
    """
    Extract the segment ID (first element) from a segment.

    Args:
        segment: EDI segment string

    Returns:
        Segment identifier (e.g., "ISA", "GS", "BEG", "PO1")

    Example:
        >>> get_segment_id("BEG*00*NE*PO123456")
        'BEG'
    """
    elements = split_elements(segment)
    return elements[0] if elements else ""


def get_element_value(segment: str, position: int, default: str = "") -> str:
    """
    Get the value of an element at a specific position in a segment.

    Args:
        segment: EDI segment string
        position: Element position (0-indexed, where 0 is segment ID)
        default: Default value if element doesn't exist or is empty

    Returns:
        Element value or default

    Example:
        >>> get_element_value("BEG*00*NE*PO123456", 3)
        'PO123456'
    """
    elements = split_elements(segment)

    if position < len(elements):
        value = elements[position].strip()
        return value if value else default

    return default


def parse_segment_to_dict(segment: str) -> Dict[str, any]:
    """
    Parse a segment into a dictionary structure.

    Args:
        segment: EDI segment string

    Returns:
        Dictionary with segment_id and elements

    Example:
        >>> parse_segment_to_dict("BEG*00*NE*PO123456**20231215")
        {
            'segment_id': 'BEG',
            'elements': ['BEG', '00', 'NE', 'PO123456', '', '20231215']
        }
    """
    elements = split_elements(segment)

    return {
        'segment_id': elements[0] if elements else "",
        'elements': elements
    }


def count_segment_occurrences(segments: List[str], segment_id: str) -> int:
    """
    Count how many times a specific segment appears in a list of segments.

    Args:
        segments: List of segment strings
        segment_id: The segment ID to count (e.g., "PO1", "N1")

    Returns:
        Count of occurrences
    """
    count = 0
    for segment in segments:
        if get_segment_id(segment) == segment_id:
            count += 1
    return count


def find_segments_by_id(segments: List[str], segment_id: str) -> List[Dict[str, any]]:
    """
    Find all segments with a specific ID and return their parsed dictionaries.

    Args:
        segments: List of segment strings
        segment_id: The segment ID to find

    Returns:
        List of parsed segment dictionaries with index information
    """
    results = []
    for idx, segment in enumerate(segments):
        if get_segment_id(segment) == segment_id:
            parsed = parse_segment_to_dict(segment)
            parsed['index'] = idx
            results.append(parsed)
    return results


def extract_control_numbers(segments: List[str]) -> Dict[str, str]:
    """
    Extract control numbers from ISA, GS, and ST segments.

    Args:
        segments: List of segment strings

    Returns:
        Dictionary with control numbers
    """
    control_numbers = {
        'interchange_control': '',
        'group_control': '',
        'transaction_control': ''
    }

    for segment in segments:
        seg_id = get_segment_id(segment)

        if seg_id == 'ISA':
            # ISA13 is interchange control number
            control_numbers['interchange_control'] = get_element_value(segment, 13)
        elif seg_id == 'GS':
            # GS06 is group control number
            control_numbers['group_control'] = get_element_value(segment, 6)
        elif seg_id == 'ST':
            # ST02 is transaction set control number
            control_numbers['transaction_control'] = get_element_value(segment, 2)

    return control_numbers
