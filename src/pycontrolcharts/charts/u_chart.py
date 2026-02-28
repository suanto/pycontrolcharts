"""u-chart (Defects per Unit) for attribute data with variable area of opportunity."""

import math
import pandas as pd

from pycontrolcharts.models import RunTestConfig
from pycontrolcharts.input_handlers import normalize_dual_input
from pycontrolcharts.output_builder import build_output_dataframe
from pycontrolcharts.core import apply_run_tests
from pycontrolcharts.chart_helpers import (
    normalize_run_tests_config,
    create_empty_chart_dataframe,
    get_phase_boundaries,
    normalize_spec_limit_pair,
)


def u_chart(
    data: list | pd.Series | pd.DataFrame,
    *,
    area_column: str | None = None,
    value_column: str | None = None,
    area: int | list[int] | str | None = None,
    label: str | list | None = None,
    phase: str | list | None = None,
    spec_upper: float | list[float] | str | None = None,
    spec_lower: float | list[float] | str | None = None,
    run_tests: bool | RunTestConfig = True,
) -> pd.DataFrame:
    """
    Create a u-chart (defects per unit) for attribute data with variable areas of opportunity.

    Args:
        data: Input data (list, Series, or DataFrame)
        area_column: Column name for areas of opportunity (optional if DataFrame with constant area)
        value_column: Column name for defect counts (required if DataFrame)
        area: Area of opportunity - int (constant), list (variable), or str (column name)
        label: Column name or list for x-axis labels
        phase: Column name or list for phase labels
        spec_upper: Upper specification limit - float (broadcast to all),
                   list (per-point), or str (column name)
        spec_lower: Lower specification limit - float (broadcast to all),
                   list (per-point), or str (column name)
        run_tests: Enable run tests
            - True (default): Enable all tests with Nelson rules defaults
            - False: Disable all run tests
            - RunTestConfig: Custom configuration object

    Raises:
        ValueError: If value_column/area_column/column not found or length mismatch;
            or area or area_column invalid or missing when required.
        TypeError: If data is not a list, Series, or DataFrame.

    Returns:
        pandas DataFrame with defects per unit data and control limits (standardized
        columns; see User Guide and API reference).

    Examples:
        >>> # List with constant area
        >>> df = calc_u(data=[5, 3, 7, 4, 6], area=50)

        >>> # List with variable areas
        >>> df = calc_u(data=[5, 3, 7, 4, 6], area=[50, 50, 60, 55, 50])

        >>> # Series input
        >>> defects = pd.Series([5, 3, 7, 4, 6])
        >>> df = calc_u(data=defects, area=50)

        >>> # DataFrame input
        >>> input_df = pd.DataFrame({'defects': [5, 3, 7], 'units': [50, 50, 60]})
        >>> df = calc_u(data=input_df, value_column='defects', area_column='units')
    """
    # Normalize input
    defect_counts, area_sizes, labels, phases = normalize_dual_input(
        data, None, area_column, value_column, area, label, phase
    )

    if not defect_counts:
        return create_empty_chart_dataframe(include_variation=False)

    # Handle constant area
    if isinstance(area_sizes, int):
        area_list = [area_sizes] * len(defect_counts)
    else:
        area_list = area_sizes

    # Calculate defects per unit
    u_values = [d / a if a > 0 else 0.0 for d, a in zip(defect_counts, area_list)]

    # Determine phase boundaries
    phase_info = get_phase_boundaries(phases, len(u_values))

    # Calculate control limits for each phase
    phase_data = []
    for start, end, phase_label in phase_info:
        phase_defects = defect_counts[start:end]
        phase_areas = area_list[start:end]

        # Calculate grand average u-bar for this phase
        total_defects = sum(phase_defects)
        total_area = sum(phase_areas)
        u_bar = total_defects / total_area if total_area > 0 else 0.0

        # For u-chart, limits vary by area size, so we create per-point limits
        phase_limits = []
        for i in range(start, end):
            n = area_list[i]
            limits = _calc_u_limits(u_bar, n)
            phase_limits.append(limits)

        phase_data.append((start, end, phase_label, phase_limits))

    # Create per-point control limits
    control_limits_per_point = []
    phase_labels = []
    for start, end, phase_label, phase_limits in phase_data:
        control_limits_per_point.extend(phase_limits)
        phase_labels.extend([phase_label] * (end - start))

    # Apply run tests (per phase so windows do not cross boundaries)
    config = normalize_run_tests_config(run_tests)
    violations = apply_run_tests(
        u_values,
        control_limits_per_point,
        config,
        phase_boundaries=phase_info,
    )

    # Normalize specification limits
    spec_upper_list, spec_lower_list = normalize_spec_limit_pair(
        data, spec_upper, spec_lower, len(u_values)
    )

    return build_output_dataframe(
        values=u_values,
        labels=labels,
        control_limits=control_limits_per_point,
        phases=phase_labels,
        spec_upper=spec_upper_list,
        spec_lower=spec_lower_list,
        violations=violations,
    )


def _calc_u_limits(u_bar: float, area: int) -> dict[str, float]:
    """Calculate u-chart control limits for a single point."""
    if area <= 0:
        return {
            'ucl': 0,
            'sigma_2_upper': 0,
            'sigma_1_upper': 0,
            'center_line': u_bar,
            'sigma_1_lower': 0,
            'sigma_2_lower': 0,
            'lcl': 0,
            'var_ucl': 0,
            'var_cl': 0,
            'var_lcl': 0,
        }

    limit = math.sqrt(u_bar / area)

    clx = u_bar
    uclx = u_bar + 3 * limit
    lclx = max(u_bar - 3 * limit, 0.0)

    return {
        'ucl': uclx,
        'sigma_2_upper': u_bar + 2 * limit,
        'sigma_1_upper': u_bar + 1 * limit,
        'center_line': clx,
        'sigma_1_lower': max(u_bar - 1 * limit, 0.0),
        'sigma_2_lower': max(u_bar - 2 * limit, 0.0),
        'lcl': lclx,
        'var_ucl': 0,
        'var_cl': 0,
        'var_lcl': 0,
    }
