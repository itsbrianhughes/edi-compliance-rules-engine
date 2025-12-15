"""
Rule Evaluators Module

Contains validator functions for each rule category:
- Required segments
- Element validation
- Conditional rules
- Cross-segment rules
"""

import re
from typing import Dict, List, Optional
from .error_collector import ErrorCollector


class RequiredSegmentValidator:
    """Validates required segment rules."""

    def __init__(self, error_collector: ErrorCollector):
        """
        Initialize the required segment validator.

        Args:
            error_collector: ErrorCollector instance to report violations
        """
        self.error_collector = error_collector

    def validate(self, parsed_edi: Dict, rules: List[Dict]) -> None:
        """
        Validate required segment rules.

        Args:
            parsed_edi: Parsed EDI document
            rules: List of required segment rules
        """
        segments = parsed_edi.get("segments", [])

        for rule in rules:
            segment_id = rule.get("segment_id")
            min_occurrences = rule.get("min_occurrences", 0)
            max_occurrences = rule.get("max_occurrences")
            element_filters = rule.get("element_filters", {})

            # Count matching segments
            matching_segments = self._find_matching_segments(
                segments, segment_id, element_filters
            )
            count = len(matching_segments)

            # Check minimum occurrences
            if count < min_occurrences:
                self.error_collector.add_error(
                    rule_id=rule["rule_id"],
                    severity=rule["severity"],
                    message=f"{rule['description']} (found {count}, expected at least {min_occurrences})",
                    segment_id=segment_id,
                    expected_value=f"min {min_occurrences}",
                    actual_value=str(count)
                )

            # Check maximum occurrences
            if max_occurrences is not None and count > max_occurrences:
                # Report on the first excess segment
                if count > 0:
                    excess_segment = matching_segments[max_occurrences]
                    line_number = excess_segment.get("line")
                else:
                    line_number = None

                self.error_collector.add_error(
                    rule_id=rule["rule_id"],
                    severity=rule["severity"],
                    message=f"{segment_id} appears too many times (found {count}, max {max_occurrences})",
                    segment_id=segment_id,
                    line_number=line_number,
                    expected_value=f"max {max_occurrences}",
                    actual_value=str(count)
                )

    def _find_matching_segments(
        self, segments: List[Dict], segment_id: str, element_filters: Dict
    ) -> List[Dict]:
        """
        Find segments matching ID and optional element filters.

        Args:
            segments: List of parsed segments
            segment_id: Segment ID to match
            element_filters: Dictionary of element position -> required value

        Returns:
            List of matching segments
        """
        matching = []

        for segment in segments:
            if segment["segment_id"] != segment_id:
                continue

            # Check element filters
            if element_filters:
                elements = segment.get("elements", [])
                matches_filters = True

                for position, required_value in element_filters.items():
                    position = int(position)
                    if position >= len(elements) or elements[position] != required_value:
                        matches_filters = False
                        break

                if matches_filters:
                    matching.append(segment)
            else:
                matching.append(segment)

        return matching


class ElementValidator:
    """Validates element-level rules."""

    def __init__(self, error_collector: ErrorCollector):
        """
        Initialize the element validator.

        Args:
            error_collector: ErrorCollector instance to report violations
        """
        self.error_collector = error_collector

    def validate(self, parsed_edi: Dict, rules: List[Dict]) -> None:
        """
        Validate element rules.

        Args:
            parsed_edi: Parsed EDI document
            rules: List of element validation rules
        """
        segments = parsed_edi.get("segments", [])

        for rule in rules:
            segment_id = rule.get("segment_id")
            element_position = int(rule.get("element_position", 0))
            validations = rule.get("validations", {})
            conditional = rule.get("conditional", {})

            # Find matching segments
            matching_segments = [s for s in segments if s["segment_id"] == segment_id]

            for segment in matching_segments:
                # Check if conditional applies
                if conditional and not self._check_conditional(segment, conditional):
                    continue

                elements = segment.get("elements", [])

                # Check if element exists
                if element_position >= len(elements):
                    if validations.get("required"):
                        self.error_collector.add_error(
                            rule_id=rule["rule_id"],
                            severity=rule["severity"],
                            message=f"{segment_id}{element_position:02d} is required but missing",
                            segment_id=segment_id,
                            line_number=segment.get("line"),
                            element_position=element_position
                        )
                    continue

                element_value = elements[element_position].strip()

                # Validate the element
                self._validate_element_value(
                    rule, segment, element_position, element_value, validations
                )

    def _check_conditional(self, segment: Dict, conditional: Dict) -> bool:
        """
        Check if conditional criteria are met.

        Args:
            segment: Segment dictionary
            conditional: Conditional specification

        Returns:
            True if conditional is met
        """
        if_element = conditional.get("if_element")
        equals = conditional.get("equals")

        if if_element:
            elements = segment.get("elements", [])
            if_element_pos = int(if_element)

            if if_element_pos < len(elements):
                return elements[if_element_pos].strip() == equals

        return False

    def _validate_element_value(
        self, rule: Dict, segment: Dict, position: int, value: str, validations: Dict
    ) -> None:
        """
        Validate an element value against validation criteria.

        Args:
            rule: Rule dictionary
            segment: Segment dictionary
            position: Element position
            value: Element value
            validations: Validation criteria
        """
        segment_id = segment["segment_id"]
        line_number = segment.get("line")

        # Check if required but empty
        if validations.get("required") and not value:
            self.error_collector.add_error(
                rule_id=rule["rule_id"],
                severity=rule["severity"],
                message=f"{segment_id}{position:02d} is required but empty",
                segment_id=segment_id,
                line_number=line_number,
                element_position=position,
                actual_value=value
            )
            return

        # Skip further validation if empty and not required
        if not value and not validations.get("required"):
            return

        # Check length
        min_length = validations.get("min_length")
        max_length = validations.get("max_length")

        if min_length and len(value) < min_length:
            self.error_collector.add_error(
                rule_id=rule["rule_id"],
                severity=rule["severity"],
                message=f"{segment_id}{position:02d} is too short (min {min_length}, got {len(value)})",
                segment_id=segment_id,
                line_number=line_number,
                element_position=position,
                expected_value=f"min length {min_length}",
                actual_value=value
            )

        if max_length and len(value) > max_length:
            self.error_collector.add_error(
                rule_id=rule["rule_id"],
                severity=rule["severity"],
                message=f"{segment_id}{position:02d} is too long (max {max_length}, got {len(value)})",
                segment_id=segment_id,
                line_number=line_number,
                element_position=position,
                expected_value=f"max length {max_length}",
                actual_value=value
            )

        # Check allowed values
        allowed_values = validations.get("allowed_values")
        if allowed_values and value not in allowed_values:
            self.error_collector.add_error(
                rule_id=rule["rule_id"],
                severity=rule["severity"],
                message=f"{segment_id}{position:02d} has invalid value '{value}' (allowed: {', '.join(allowed_values[:5])}...)",
                segment_id=segment_id,
                line_number=line_number,
                element_position=position,
                expected_value=f"one of {allowed_values[:5]}",
                actual_value=value
            )

        # Check regex pattern
        regex = validations.get("regex")
        if regex and not re.match(regex, value):
            self.error_collector.add_error(
                rule_id=rule["rule_id"],
                severity=rule["severity"],
                message=f"{segment_id}{position:02d} does not match required pattern (value: '{value}')",
                segment_id=segment_id,
                line_number=line_number,
                element_position=position,
                expected_value=f"pattern: {regex}",
                actual_value=value
            )


class ConditionalRuleValidator:
    """Validates conditional (if-then) rules."""

    def __init__(self, error_collector: ErrorCollector):
        """
        Initialize the conditional rule validator.

        Args:
            error_collector: ErrorCollector instance to report violations
        """
        self.error_collector = error_collector

    def validate(self, parsed_edi: Dict, rules: List[Dict]) -> None:
        """
        Validate conditional rules.

        Args:
            parsed_edi: Parsed EDI document
            rules: List of conditional rules
        """
        segments = parsed_edi.get("segments", [])

        for rule in rules:
            condition = rule.get("condition", {})
            then_clause = rule.get("then", {})

            # Find segments that match the condition
            if_segment_id = condition.get("if_segment")
            if_element = condition.get("if_element")
            if_value = condition.get("if_value")
            if_value_exists = condition.get("if_value_exists")

            for segment in segments:
                if segment["segment_id"] != if_segment_id:
                    continue

                # Check if condition is met
                elements = segment.get("elements", [])
                if_element_pos = int(if_element) if if_element else None

                condition_met = False

                if if_element_pos is not None and if_element_pos < len(elements):
                    element_value = elements[if_element_pos].strip()

                    if if_value and element_value == if_value:
                        condition_met = True
                    elif if_value_exists and element_value:
                        condition_met = True

                if condition_met:
                    # Check "then" requirements
                    self._check_then_clause(
                        rule, segment, segments, then_clause
                    )

    def _check_then_clause(
        self, rule: Dict, trigger_segment: Dict, all_segments: List[Dict], then_clause: Dict
    ) -> None:
        """
        Check if "then" clause requirements are met.

        Args:
            rule: Rule dictionary
            trigger_segment: Segment that triggered the condition
            all_segments: All segments in the document
            then_clause: Then clause specification
        """
        required_segments = then_clause.get("required_segments", [])
        within_loop = then_clause.get("within_loop")
        required_element = then_clause.get("required_element")
        message_override = then_clause.get("message")

        # Check for required segments
        if required_segments:
            trigger_line = trigger_segment.get("line")

            # Find segments in the same loop (simple implementation: next few segments)
            loop_segments = []
            if within_loop:
                # Get segments following the trigger until we hit a different loop
                for seg in all_segments:
                    if seg.get("line", 0) > trigger_line:
                        if seg["segment_id"] == within_loop:
                            # New loop started
                            break
                        loop_segments.append(seg)
                        if len(loop_segments) > 10:  # Safety limit
                            break
            else:
                loop_segments = all_segments

            # Check each required segment
            for req_seg_id in required_segments:
                found = any(s["segment_id"] == req_seg_id for s in loop_segments)

                if not found:
                    message = message_override or f"{req_seg_id} is required when {trigger_segment['segment_id']} is present"
                    self.error_collector.add_error(
                        rule_id=rule["rule_id"],
                        severity=rule["severity"],
                        message=message,
                        segment_id=trigger_segment["segment_id"],
                        line_number=trigger_line,
                        context={"expected_segment": req_seg_id}
                    )

        # Check for required element
        if required_element:
            req_seg_id = required_element.get("segment")
            req_elem_pos = int(required_element.get("element", 0))

            if req_seg_id == trigger_segment["segment_id"]:
                elements = trigger_segment.get("elements", [])
                if req_elem_pos >= len(elements) or not elements[req_elem_pos].strip():
                    message = message_override or f"{req_seg_id}{req_elem_pos:02d} is required"
                    self.error_collector.add_error(
                        rule_id=rule["rule_id"],
                        severity=rule["severity"],
                        message=message,
                        segment_id=req_seg_id,
                        line_number=trigger_segment.get("line"),
                        element_position=req_elem_pos
                    )


class CrossSegmentValidator:
    """Validates cross-segment rules."""

    def __init__(self, error_collector: ErrorCollector):
        """
        Initialize the cross-segment validator.

        Args:
            error_collector: ErrorCollector instance to report violations
        """
        self.error_collector = error_collector

    def validate(self, parsed_edi: Dict, rules: List[Dict]) -> None:
        """
        Validate cross-segment rules.

        Args:
            parsed_edi: Parsed EDI document
            rules: List of cross-segment rules
        """
        segments = parsed_edi.get("segments", [])

        for rule in rules:
            validation_logic = rule.get("validation_logic", {})
            validation_type = validation_logic.get("type")

            if validation_type == "count_match":
                self._validate_count_match(rule, segments, validation_logic)
            elif validation_type == "element_match":
                self._validate_element_match(rule, segments, validation_logic)
            elif validation_type == "element_value_exists":
                self._validate_element_value_exists(rule, segments, validation_logic)

    def _validate_count_match(
        self, rule: Dict, segments: List[Dict], logic: Dict
    ) -> None:
        """
        Validate that a segment's element value matches a count of another segment.

        Args:
            rule: Rule dictionary
            segments: List of segments
            logic: Validation logic specification
        """
        source_segment_id = logic.get("source_segment")
        target_segment_id = logic.get("target_segment")
        target_element = int(logic.get("target_element", 0))

        # Count source segments
        source_count = sum(1 for s in segments if s["segment_id"] == source_segment_id)

        # Find target segment
        target_segments = [s for s in segments if s["segment_id"] == target_segment_id]

        for target_seg in target_segments:
            elements = target_seg.get("elements", [])

            if target_element < len(elements):
                declared_count = elements[target_element].strip()

                try:
                    declared_count_int = int(declared_count)

                    if declared_count_int != source_count:
                        message = logic.get("message") or f"{target_segment_id}{target_element:02d} count mismatch"
                        self.error_collector.add_error(
                            rule_id=rule["rule_id"],
                            severity=rule["severity"],
                            message=message,
                            segment_id=target_segment_id,
                            line_number=target_seg.get("line"),
                            element_position=target_element,
                            expected_value=str(source_count),
                            actual_value=declared_count
                        )
                except ValueError:
                    # Invalid count value
                    self.error_collector.add_error(
                        rule_id=rule["rule_id"],
                        severity=rule["severity"],
                        message=f"{target_segment_id}{target_element:02d} contains invalid count value",
                        segment_id=target_segment_id,
                        line_number=target_seg.get("line"),
                        element_position=target_element,
                        actual_value=declared_count
                    )

    def _validate_element_match(
        self, rule: Dict, segments: List[Dict], logic: Dict
    ) -> None:
        """
        Validate that element values match between segments.

        Args:
            rule: Rule dictionary
            segments: List of segments
            logic: Validation logic specification
        """
        match_pairs = logic.get("match_pairs", [])

        for pair in match_pairs:
            seg1_id = pair.get("segment_1")
            elem1_pos = int(pair.get("element_1", 0))
            seg2_id = pair.get("segment_2")
            elem2_pos = int(pair.get("element_2", 0))

            # Find segments
            seg1_list = [s for s in segments if s["segment_id"] == seg1_id]
            seg2_list = [s for s in segments if s["segment_id"] == seg2_id]

            for seg1, seg2 in zip(seg1_list, seg2_list):
                elem1 = seg1.get("elements", [])
                elem2 = seg2.get("elements", [])

                if elem1_pos < len(elem1) and elem2_pos < len(elem2):
                    val1 = elem1[elem1_pos].strip()
                    val2 = elem2[elem2_pos].strip()

                    if val1 != val2:
                        self.error_collector.add_error(
                            rule_id=rule["rule_id"],
                            severity=rule["severity"],
                            message=f"{seg1_id}{elem1_pos:02d} and {seg2_id}{elem2_pos:02d} must match",
                            segment_id=seg2_id,
                            line_number=seg2.get("line"),
                            element_position=elem2_pos,
                            expected_value=val1,
                            actual_value=val2
                        )

    def _validate_element_value_exists(
        self, rule: Dict, segments: List[Dict], logic: Dict
    ) -> None:
        """
        Validate that at least one segment has a specific element value.

        Args:
            rule: Rule dictionary
            segments: List of segments
            logic: Validation logic specification
        """
        segment_id = logic.get("segment_id")
        element_position = int(logic.get("element_position", 0))
        required_value = logic.get("required_value")

        # Check if any segment has the required value
        found = False
        for segment in segments:
            if segment["segment_id"] == segment_id:
                elements = segment.get("elements", [])
                if element_position < len(elements):
                    if elements[element_position].strip() == required_value:
                        found = True
                        break

        if not found:
            message = logic.get("message") or f"No {segment_id} segment with {segment_id}{element_position:02d}={required_value} found"
            self.error_collector.add_error(
                rule_id=rule["rule_id"],
                severity=rule["severity"],
                message=message,
                segment_id=segment_id,
                expected_value=required_value
            )
