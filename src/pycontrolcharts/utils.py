"""
Utility functions for control chart calculations.

This module provides common mathematical and statistical functions used
across different control chart types.
"""

import math


def is_finite(value: float) -> bool:
    """
    Check if a value is finite (not NaN or infinity).

    Args:
        value: The value to check

    Returns:
        True if the value is finite, False otherwise
    """
    return not (math.isnan(value) or math.isinf(value))


def mean(data: list[float]) -> float:
    """
    Calculate the mean (average) of a list of numbers.

    Args:
        data: List of numbers

    Returns:
        Mean value

    Raises:
        ValueError: If data is empty
    """
    if not data:
        raise ValueError('Cannot calculate mean of empty list')

    return sum(data) / len(data)


def calc_std_dev(data: list[float]) -> float:
    """
    Calculate sample standard deviation (using n-1 denominator).

    Args:
        data: List of numbers

    Returns:
        Standard deviation, or 0 if data has 0 or 1 elements
    """
    if not data or len(data) <= 1:
        return 0.0

    avg = mean(data)
    squared_diffs = [(value - avg) ** 2 for value in data]
    variance = sum(squared_diffs) / (len(data) - 1)
    return math.sqrt(variance)


def calc_range(data: list[float]) -> float:
    """
    Calculate the range (max - min) of a list of numbers.

    Args:
        data: List of numbers

    Returns:
        Range value, or 0 if data is empty
    """
    if not data:
        return 0.0

    return max(data) - min(data)


def calc_moving_range(data: list[float]) -> list[float | None]:
    """
    Calculate moving range for each point in the data.

    The moving range is the absolute difference between consecutive values.
    The first element is always None since there's no previous value.

    Args:
        data: List of numbers

    Returns:
        List of moving ranges, with first element as None

    Examples:
        >>> calc_moving_range([10, 12, 11, 13])
        [None, 2.0, 1.0, 2.0]
    """
    if not data:
        return []

    result: list[float | None] = [None]  # First element has no previous value

    for i in range(1, len(data)):
        current = data[i]
        previous = data[i - 1]

        # Skip if either value is non-finite
        if not is_finite(current) or not is_finite(previous):
            result.append(None)
        else:
            result.append(abs(current - previous))

    return result


def find_phase_boundaries(
    phase_at: list[int] | None, data_length: int
) -> list[tuple[int, int]]:
    """
    Convert phase_at indices to phase boundary tuples.

    Note: Chart code currently uses phase labels (via find_phase_boundaries_from_labels
    and get_phase_boundaries) rather than split indices. The phase_at list API is
    retained for alternative or future callers that specify phases by split indices.

    Args:
        phase_at: Optional list of indices where phases split (e.g., [20, 40])
                 If None, returns a single phase covering all data
        data_length: Total length of the data

    Returns:
        List of (start, end) tuples representing phase boundaries
        Boundaries use half-open intervals: [start, end)

    Examples:
        >>> find_phase_boundaries(None, 50)
        [(0, 50)]

        >>> find_phase_boundaries([20, 40], 50)
        [(0, 20), (20, 40), (40, 50)]

    Raises:
        ValueError: If phase_at indices are not sorted or contain invalid values
    """
    if phase_at is None or len(phase_at) == 0:
        # Single phase covering all data
        return [(0, data_length)]

    # Validate and filter phase_at
    valid_indices = []
    for idx in phase_at:
        if idx <= 0 or idx >= data_length:
            # Ignore indices at or before start, or at or after end
            continue
        valid_indices.append(idx)

    # Check if sorted
    if valid_indices != sorted(valid_indices):
        raise ValueError('phase_at indices must be in ascending order')

    # Check for duplicates
    if len(valid_indices) != len(set(valid_indices)):
        raise ValueError('phase_at indices must be unique')

    # If no valid indices, return single phase
    if not valid_indices:
        return [(0, data_length)]

    # Build phase boundaries
    boundaries = []
    start = 0

    for split_point in valid_indices:
        boundaries.append((start, split_point))
        start = split_point

    # Add final phase
    boundaries.append((start, data_length))

    return boundaries


def find_phase_boundaries_from_labels(
    phase_labels: list[str], data_length: int
) -> list[tuple[int, int, str]]:
    """
    Convert phase labels to phase boundary tuples with labels.

    Consecutive datapoints with the same label are grouped into one phase.

    Args:
        phase_labels: List of phase labels (strings), one per datapoint
        data_length: Expected data length (for validation)

    Returns:
        List of (start, end, label) tuples representing phase boundaries.
        Boundaries use half-open intervals: [start, end)

    Examples:
        >>> find_phase_boundaries_from_labels(
        ...     ["phase 1", "phase 1", "phase 2", "phase 2"],
        ...     4
        ... )
        [(0, 2, "phase 1"), (2, 4, "phase 2")]

        >>> find_phase_boundaries_from_labels(
        ...     ["A", "A", "B", "B", "A", "A"],
        ...     6
        ... )
        [(0, 2, "A"), (2, 4, "B"), (4, 6, "A")]

    Raises:
        ValueError: If phase_labels is empty or length doesn't match data_length
    """
    # Validate inputs
    if not phase_labels:
        raise ValueError('phase_labels cannot be empty')

    if len(phase_labels) != data_length:
        raise ValueError(
            f'phase_labels length ({len(phase_labels)}) must match data length ({data_length})'
        )

    # Group consecutive same labels into phases
    boundaries: list[tuple[int, int, str]] = []
    current_label = phase_labels[0]
    start_idx = 0

    for i in range(1, len(phase_labels)):
        if phase_labels[i] != current_label:
            # Label changed, close current phase
            boundaries.append((start_idx, i, current_label))
            current_label = phase_labels[i]
            start_idx = i

    # Add final phase
    boundaries.append((start_idx, len(phase_labels), current_label))

    return boundaries
