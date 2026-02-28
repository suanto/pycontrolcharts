"""XmR (Individuals and Moving Range) control chart."""

import pandas as pd

from pycontrolcharts.models import RunTestConfig
from pycontrolcharts.input_handlers import normalize_simple_input
from pycontrolcharts.output_builder import build_output_dataframe, create_phase_limits
from pycontrolcharts.core import apply_run_tests
from pycontrolcharts.chart_helpers import (
    normalize_run_tests_config,
    create_empty_chart_dataframe,
    get_phase_boundaries,
    normalize_spec_limit_pair,
)
from pycontrolcharts.utils import mean, calc_moving_range, is_finite
from pycontrolcharts.constants import calc_d2, calc_D4


def xmr_chart(
    data: list | pd.Series | pd.DataFrame,
    *,
    value_column: str | None = None,
    label: str | list | None = None,
    phase: str | list | None = None,
    spec_upper: float | list[float] | str | None = None,
    spec_lower: float | list[float] | str | None = None,
    run_tests: bool | RunTestConfig = True,
) -> pd.DataFrame:
    """
    Create an XmR (Individuals and Moving Range) control chart.

    Returns a pandas DataFrame with all chart data, control limits, and violations
    in a single table.

    Args:
        data: Input data (list, Series, or DataFrame)
        value_column: Column name for values (required if DataFrame)
        label: Column name or list for x-axis labels
        phase: Column name or list for phase labels (optional)
        spec_upper: Upper specification limit - float (broadcast to all),
                   list (per-point), or str (column name)
        spec_lower: Lower specification limit - float (broadcast to all),
                   list (per-point), or str (column name)
        run_tests: Enable run tests
            - True (default): Enable all tests with Nelson rules defaults
              (test1=beyond limits, test2=9 consecutive same side,
               test3=6 consecutive trending, test5=2 of 3 beyond 2σ,
               test6=4 of 5 beyond 1σ)
            - False: Disable all run tests
            - RunTestConfig: Custom configuration object

    Raises:
        ValueError: If data is DataFrame and value_column is missing or column not found;
            or if label/phase/spec list lengths do not match data length.
        TypeError: If data is not a list, Series, or DataFrame.

    Returns:
        pandas DataFrame with standardized columns (see User Guide and API reference):
        point_id, value, label, control/sigma limits, spec_upper/spec_lower, phase,
        violations; plus variation, variation_ucl/cl/lcl, variation_violations.

    Example:
        >>> import pandas as pd
        >>> from pycontrolcharts import calc_xmr
        >>>
        >>> data = [39, 41, 41, 41, 43, 44, 41, 42, 40, 41, 44, 40]
        >>> df = calc_xmr(data)
        >>>
        >>> print(df['center_line'].iloc[0])  # 41.42
        >>> print(df['ucl'].iloc[0])          # 46.01
    """
    # Normalize input
    values, labels, phases = normalize_simple_input(data, value_column, label, phase)

    if not values:
        return create_empty_chart_dataframe(include_variation=True)

    # Normalize specification limits
    spec_upper_list, spec_lower_list = normalize_spec_limit_pair(
        data, spec_upper, spec_lower, len(values)
    )

    # Calculate moving ranges
    mr_list = calc_moving_range(values)

    # Determine phase boundaries
    phase_info = get_phase_boundaries(phases, len(values))

    # Calculate control limits for each phase
    phase_data = []
    for start, end, phase_label in phase_info:
        phase_values = values[start:end]
        phase_mrs = mr_list[start + 1 : end]  # only within-phase MRs

        # Calculate limits for this phase
        limits = _calc_xmr_limits(phase_values, phase_mrs)
        phase_data.append((start, end, phase_label, limits))

    # Create per-point control limits and phase labels
    control_limits_per_point, phase_labels = create_phase_limits(
        phase_data, len(values)
    )

    # Apply run tests if enabled (per phase so windows do not cross boundaries)
    config = normalize_run_tests_config(run_tests)
    violations = apply_run_tests(
        values, control_limits_per_point, config, phase_boundaries=phase_info
    )

    # Apply run tests to variation (moving ranges)
    # First point of each phase has no within-phase MR -> None/nan
    valid_mr_values = [mr if mr is not None else float('nan') for mr in mr_list]
    for start, end, _ in phase_info:
        valid_mr_values[start] = float('nan')
    valid_mr_limits = [
        {
            'center_line': limits['var_cl'],
            'ucl': limits['var_ucl'],
            'lcl': limits['var_lcl'],
            'sigma_1_upper': limits['var_cl']
            + (limits['var_ucl'] - limits['var_cl']) / 3,
            'sigma_1_lower': limits['var_lcl'],
            'sigma_2_upper': limits['var_cl']
            + 2 * (limits['var_ucl'] - limits['var_cl']) / 3,
            'sigma_2_lower': limits['var_lcl'],
        }
        for limits in control_limits_per_point
    ]
    variation_violations = apply_run_tests(
        valid_mr_values, valid_mr_limits, config, phase_boundaries=phase_info
    )

    # Build output DataFrame
    return build_output_dataframe(
        values=values,
        labels=labels,
        control_limits=control_limits_per_point,
        phases=phase_labels,
        spec_upper=spec_upper_list,
        spec_lower=spec_lower_list,
        violations=violations,
        variation_values=valid_mr_values,
        variation_limits=valid_mr_limits,
        variation_violations=variation_violations,
    )


def _calc_xmr_limits(
    values: list[float], moving_ranges: list[float | None]
) -> dict[str, float]:
    """
    Calculate XmR control limits for a single phase.

    Args:
        values: Individual measurements
        moving_ranges: Moving range values

    Returns:
        Dictionary with all control limit values
    """
    # Moving range subgroup size is always 2
    n = 2
    d2 = calc_d2(n)
    D4 = calc_D4(n)

    # Calculate average moving range (skip None values)
    valid_mrs = [mr for mr in moving_ranges if mr is not None and is_finite(mr)]
    if not valid_mrs:
        # No valid moving ranges - return zero limits
        avg_mr = 0.0
    else:
        avg_mr = mean(valid_mrs)

    # Data chart limits
    clx = mean(values)
    uclx = clx + (3 / d2) * avg_mr
    lclx = clx - (3 / d2) * avg_mr

    # Sigma lines
    usigma2x = clx + (2 / d2) * avg_mr
    usigma1x = clx + (1 / d2) * avg_mr
    lsigma2x = clx - (2 / d2) * avg_mr
    lsigma1x = clx - (1 / d2) * avg_mr

    # Variation chart limits
    var_ucl = D4 * avg_mr
    var_cl = avg_mr
    var_lcl = 0.0  # Always 0 for moving range

    return {
        'ucl': uclx,
        'sigma_2_upper': usigma2x,
        'sigma_1_upper': usigma1x,
        'center_line': clx,
        'sigma_1_lower': lsigma1x,
        'sigma_2_lower': lsigma2x,
        'lcl': lclx,
        'var_ucl': var_ucl,
        'var_cl': var_cl,
        'var_lcl': var_lcl,
    }
