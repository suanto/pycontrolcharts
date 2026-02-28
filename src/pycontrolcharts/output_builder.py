"""
Output builder for creating standardized DataFrames from control chart calculations.

This module provides utilities to build the output DataFrame with all required columns:
point_id, value, label, control limits, sigma lines, spec limits, phase, violations, etc.
"""

from typing import Any
import pandas as pd


def build_output_dataframe(
    values: list[float],
    labels: list[Any],
    control_limits: list[dict[str, float]],
    phases: list[str] | None = None,
    spec_upper: list[float] | None = None,
    spec_lower: list[float] | None = None,
    violations: list[list[dict]] | None = None,
    variation_values: list[float | None] | None = None,
    variation_limits: list[dict[str, float]] | None = None,
    variation_violations: list[list[dict]] | None = None,
) -> pd.DataFrame:
    """
    Build a standardized output DataFrame for a control chart.

    Args:
        values: Data values (measurements, subgroup means, proportions, etc.)
        labels: X-axis labels
        control_limits: List of dicts with keys: ucl, sigma_2_upper, sigma_1_upper, center_line,
                       sigma_1_lower, sigma_2_lower, lcl (one per point or same for all)
        phases: Optional phase labels
        spec_upper: Optional upper specification limit (list, one per point)
        spec_lower: Optional lower specification limit (list, one per point)
        violations: Optional list of violation lists (one per point)
        variation_values: Optional variation values (MR, range, std dev)
        variation_limits: Optional variation control limits
        variation_violations: Optional variation violation lists

    Returns:
        pandas DataFrame with standardized columns
    """
    n_points = len(values)

    # Build base DataFrame
    data = {
        'point_id': list(range(n_points)),
        'value': values,
        'label': labels,
    }

    # Add control limits
    # If control_limits has one element, broadcast it to all points
    if len(control_limits) == 1:
        limits = control_limits[0]
        data['ucl'] = [limits['ucl']] * n_points
        data['sigma_2_upper'] = [limits['sigma_2_upper']] * n_points
        data['sigma_1_upper'] = [limits['sigma_1_upper']] * n_points
        data['center_line'] = [limits['center_line']] * n_points
        data['sigma_1_lower'] = [limits['sigma_1_lower']] * n_points
        data['sigma_2_lower'] = [limits['sigma_2_lower']] * n_points
        data['lcl'] = [limits['lcl']] * n_points
    else:
        # Individual limits for each point
        data['ucl'] = [limits['ucl'] for limits in control_limits]
        data['sigma_2_upper'] = [limits['sigma_2_upper'] for limits in control_limits]
        data['sigma_1_upper'] = [limits['sigma_1_upper'] for limits in control_limits]
        data['center_line'] = [limits['center_line'] for limits in control_limits]
        data['sigma_1_lower'] = [limits['sigma_1_lower'] for limits in control_limits]
        data['sigma_2_lower'] = [limits['sigma_2_lower'] for limits in control_limits]
        data['lcl'] = [limits['lcl'] for limits in control_limits]

    # Add specification limits (now as lists)
    if spec_upper is not None:
        data['spec_upper'] = spec_upper
    else:
        data['spec_upper'] = [float('nan')] * n_points

    if spec_lower is not None:
        data['spec_lower'] = spec_lower
    else:
        data['spec_lower'] = [float('nan')] * n_points

    # Add phase
    data['phase'] = phases if phases is not None else [None] * n_points

    # Add violations
    if violations is not None:
        data['violations'] = violations
    else:
        data['violations'] = [[] for _ in range(n_points)]

    # Add variation columns if provided
    if variation_values is not None:
        data['variation'] = variation_values

        if variation_limits is not None:
            if len(variation_limits) == 1:
                limits = variation_limits[0]
                data['variation_ucl'] = [limits['ucl']] * n_points
                data['variation_cl'] = [limits['center_line']] * n_points
                data['variation_lcl'] = [limits['lcl']] * n_points
            else:
                data['variation_ucl'] = [limits['ucl'] for limits in variation_limits]
                data['variation_cl'] = [
                    limits['center_line'] for limits in variation_limits
                ]
                data['variation_lcl'] = [limits['lcl'] for limits in variation_limits]
        else:
            data['variation_ucl'] = [float('nan')] * n_points
            data['variation_cl'] = [float('nan')] * n_points
            data['variation_lcl'] = [float('nan')] * n_points

        if variation_violations is not None:
            data['variation_violations'] = variation_violations
        else:
            data['variation_violations'] = [[] for _ in range(n_points)]

    return pd.DataFrame(data)


def create_phase_limits(
    phase_data: list[tuple[int, int, str | None, dict[str, float]]], n_points: int
) -> tuple[list[dict[str, float]], list[str | None]]:
    """
    Create per-point control limits and phase labels from phase information.

    Args:
        phase_data: List of (start, end, label, limits_dict) tuples
        n_points: Total number of points

    Returns:
        Tuple of (control_limits_per_point, phase_labels)
    """
    control_limits = []
    phase_labels = []

    for point_id in range(n_points):
        # Find which phase this point belongs to
        for start, end, label, limits in phase_data:
            if start <= point_id < end:
                control_limits.append(limits)
                phase_labels.append(label)
                break

    return control_limits, phase_labels


def create_violation_dict(violation_type: int, description: str) -> dict:
    """
    Create a violation dictionary with type (as integer) and description.

    Args:
        violation_type: RunType enum value (will be converted to int)
        description: Human-readable description of the violation

    Returns:
        Dict with 'type' (int) and 'description' (str)
    """
    return {'type': int(violation_type), 'description': description}
