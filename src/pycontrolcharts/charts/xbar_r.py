"""X-bar and R (Mean and Range) control chart."""

from typing import Literal, Callable
import pandas as pd
import math

from pycontrolcharts.models import RunTestConfig
from pycontrolcharts.input_handlers import (
    normalize_simple_input,
    normalize_subgroup_input,
)
from pycontrolcharts.output_builder import build_output_dataframe, create_phase_limits
from pycontrolcharts.core import apply_run_tests
from pycontrolcharts.chart_helpers import (
    normalize_run_tests_config,
    create_empty_chart_dataframe,
    get_phase_boundaries,
    normalize_spec_limit_pair,
)
from pycontrolcharts.utils import mean, calc_range, calc_std_dev
from pycontrolcharts.constants import (
    calc_a2,
    calc_d2,
    calc_D3,
    calc_D4,
    calc_a3,
    calc_c4,
    calc_B3,
    calc_B4,
)


def xbar_r_chart(
    data: list | pd.Series | pd.DataFrame,
    *,
    subgroup_size: int | None = None,
    subgroup: str | None = None,
    value_column: str | None = None,
    label: str | list | None = None,
    phase: str | list | None = None,
    spec_upper: float | list[float] | str | None = None,
    spec_lower: float | list[float] | str | None = None,
    run_tests: bool | RunTestConfig = True,
) -> pd.DataFrame:
    """
    Create an X-bar and R (Mean and Range) control chart.

    Returns a DataFrame with ONE ROW PER SUBGROUP containing both the subgroup mean
    and subgroup range in the same row.

    Args:
        data: Input data (list, Series, or DataFrame)
        subgroup_size: Size of each rational subgroup (must be >= 2).
                      Use for fixed-size subgroups. Mutually exclusive with 'subgroup'.
        subgroup: Column name in DataFrame identifying subgroup membership.
                 Use for variable-size subgroups. Mutually exclusive with 'subgroup_size'.
        value_column: Column name for values (required if DataFrame)
        label: Column name or list for x-axis labels (for subgroups)
        phase: Column name or list for phase labels (one per subgroup)
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
        ValueError: If value_column/column not found or length mismatch; or if neither
            subgroup_size nor subgroup is provided, or subgroup size < 2.
        TypeError: If data is not list/Series/DataFrame, or subgroup is used with
            non-DataFrame input.

    Returns:
        pandas DataFrame with one row per subgroup; standardized columns (see User Guide
        and API reference): point_id, value, variation, control limits, violations, etc.

    Example (fixed subgroups):
        >>> data = [10, 11, 12, 9, 10, 11, 11, 12, 10, 10, 11, 12]
        >>> df = calc_xbar_r(data, subgroup_size=3)
        >>> print(len(df))  # 4 subgroups
        >>> print(df['value'].tolist())     # [11.0, 10.0, 11.0, 11.0] - subgroup means
        >>> print(df['variation'].tolist()) # [2.0, 2.0, 2.0, 2.0] - subgroup ranges

    Example (variable subgroups):
        >>> df = pd.DataFrame({
        ...     'measurement': [10, 11, 12, 9, 10, 11, 13],
        ...     'batch': ['A', 'A', 'A', 'B', 'B', 'C', 'C']
        ... })
        >>> result = calc_xbar_r(df, value_column='measurement', subgroup='batch')
        >>> print(len(result))  # 3 subgroups (A, B, C)
    """
    return _xbar_variation_chart(
        data=data,
        variation_type='range',
        subgroup_size=subgroup_size,
        subgroup=subgroup,
        value_column=value_column,
        label=label,
        phase=phase,
        spec_upper=spec_upper,
        spec_lower=spec_lower,
        run_tests=run_tests,
    )


def _xbar_variation_chart(
    data: list | pd.Series | pd.DataFrame,
    variation_type: Literal['range', 'stddev'],
    *,
    subgroup_size: int | None = None,
    subgroup: str | None = None,
    value_column: str | None = None,
    label: str | list | None = None,
    phase: str | list | None = None,
    spec_upper: float | list[float] | str | None = None,
    spec_lower: float | list[float] | str | None = None,
    run_tests: bool | RunTestConfig = True,
) -> pd.DataFrame:
    """
    Internal implementation for X-bar charts with variation (R or S).

    Args:
        data: Input data (list, Series, or DataFrame)
        variation_type: 'range' for X-bar/R chart, 'stddev' for X-bar/S chart
        subgroup_size: Size of each rational subgroup (must be >= 2)
        subgroup: Column name in DataFrame identifying subgroup membership
        value_column: Column name for values (required if DataFrame)
        label: Column name or list for x-axis labels
        phase: Column name or list for phase labels
        spec_upper: Upper specification limit
        spec_lower: Lower specification limit
        run_tests: Enable run tests

    Returns:
        pandas DataFrame with control chart data
    """
    # Select appropriate functions and constants based on variation type
    if variation_type == 'range':
        calc_variation = calc_range
        calc_A = calc_a2
        calc_center = calc_d2
        calc_lower_limit = calc_D3
        calc_upper_limit = calc_D4
    else:  # stddev
        calc_variation = calc_std_dev
        calc_A = calc_a3
        calc_center = calc_c4
        calc_lower_limit = calc_B3
        calc_upper_limit = calc_B4
    # Validate that exactly one of subgroup_size or subgroup is provided
    if subgroup_size is None and subgroup is None:
        raise ValueError("Either 'subgroup_size' or 'subgroup' must be provided")

    if subgroup_size is not None and subgroup is not None:
        raise ValueError(
            "Cannot specify both 'subgroup_size' and 'subgroup' - use only one"
        )

    # Branch based on subgroup type
    if subgroup is not None:
        # Variable subgroups path
        if not isinstance(data, pd.DataFrame):
            raise TypeError("data must be a DataFrame when using 'subgroup' parameter")

        if value_column is None:
            raise ValueError(
                "'value_column' parameter required when using 'subgroup' with DataFrame"
            )

        # Extract variable-sized subgroups
        subgroup_data, labels, subgroup_phases, subgroup_sizes = (
            normalize_subgroup_input(data, value_column, subgroup, label, phase)
        )

        # Handle empty data
        if not subgroup_data or len(subgroup_data) == 0:
            return create_empty_chart_dataframe(include_variation=True)

        # Filter empty subgroups and calculate means/variations
        subgroup_means = []
        subgroup_variations = []
        filtered_labels = []
        filtered_sizes = []
        filtered_phases: list | None = [] if subgroup_phases is not None else None

        for i, sg_values in enumerate(subgroup_data):
            if len(sg_values) == 0:
                continue
            subgroup_means.append(mean(sg_values))
            if len(sg_values) < 2:
                subgroup_variations.append(float('nan'))
            else:
                subgroup_variations.append(calc_variation(sg_values))
            filtered_labels.append(labels[i])
            filtered_sizes.append(subgroup_sizes[i])
            if filtered_phases is not None:
                filtered_phases.append(subgroup_phases[i])

        labels = filtered_labels
        subgroup_sizes = filtered_sizes
        subgroup_phases = filtered_phases
        avg_subgroup_size = mean(subgroup_sizes)
        num_subgroups = len(subgroup_means)

    else:
        # Fixed subgroups path
        values, labels_input, phases = normalize_simple_input(
            data, value_column, label, phase
        )

        if subgroup_size < 2:
            raise ValueError('Subgroup size must be at least 2')

        avg_subgroup_size = subgroup_size

        # Calculate number of subgroups
        num_subgroups = len(values) // subgroup_size

        if num_subgroups == 0:
            # Return empty DataFrame
            return create_empty_chart_dataframe(include_variation=True)

        # Calculate subgroup means and variations
        subgroup_means = []
        subgroup_variations = []

        for i in range(num_subgroups):
            start_idx = i * subgroup_size
            end_idx = start_idx + subgroup_size
            subgroup_data = values[start_idx:end_idx]

            subgroup_means.append(mean(subgroup_data))
            subgroup_variations.append(calc_variation(subgroup_data))

        # Handle labels - if provided, must match number of subgroups
        if isinstance(label, list):
            if len(label) != num_subgroups:
                raise ValueError(
                    f'Label list length ({len(label)}) must match number of subgroups ({num_subgroups})'
                )
            labels = label
        else:
            labels = list(range(1, num_subgroups + 1))

        # Handle phases - if provided, must match number of subgroups
        if phases is not None:
            if len(phases) != len(values):
                raise ValueError('Phase list must match raw data length')
            # Take first phase of each subgroup
            subgroup_phases = [phases[i * subgroup_size] for i in range(num_subgroups)]
        else:
            subgroup_phases = None

    # Common logic for both paths
    if num_subgroups == 0:
        # Return empty DataFrame
        return create_empty_chart_dataframe(include_variation=True)

    # Determine phase boundaries (in terms of subgroup indices)
    if subgroup_phases is not None:
        phase_info = get_phase_boundaries(subgroup_phases, num_subgroups)
    else:
        phase_info = get_phase_boundaries(None, num_subgroups)

    # Calculate control limits for each phase
    phase_data = []
    for start, end, phase_label in phase_info:
        phase_means = subgroup_means[start:end]
        phase_variations = subgroup_variations[start:end]

        limits = _calc_xbar_variation_limits(
            phase_means,
            phase_variations,
            avg_subgroup_size,
            calc_A,
            calc_center,
            calc_lower_limit,
            calc_upper_limit,
        )
        phase_data.append((start, end, phase_label, limits))

    # Create per-subgroup control limits and phase labels
    control_limits_per_point, phase_labels = create_phase_limits(
        phase_data, num_subgroups
    )

    # Apply run tests if enabled (per phase so windows do not cross boundaries)
    config = normalize_run_tests_config(run_tests)
    violations = apply_run_tests(
        subgroup_means,
        control_limits_per_point,
        config,
        phase_boundaries=phase_info,
    )

    # Apply run tests to variation
    var_limits = [
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
        subgroup_variations, var_limits, config, phase_boundaries=phase_info
    )

    # Normalize specification limits
    spec_upper_list, spec_lower_list = normalize_spec_limit_pair(
        data, spec_upper, spec_lower, num_subgroups
    )

    # Build output DataFrame
    return build_output_dataframe(
        values=subgroup_means,
        labels=labels,
        control_limits=control_limits_per_point,
        phases=phase_labels,
        spec_upper=spec_upper_list,
        spec_lower=spec_lower_list,
        violations=violations,
        variation_values=subgroup_variations,
        variation_limits=var_limits,
        variation_violations=variation_violations,
    )


def _calc_xbar_variation_limits(
    means: list[float],
    variations: list[float],
    subgroup_size: int | float,
    calc_A: Callable[[int], float],
    calc_center: Callable[[int], float],
    calc_lower_limit: Callable[[int], float],
    calc_upper_limit: Callable[[int], float],
) -> dict[str, float]:
    """
    Calculate X-bar control limits for a single phase (unified for R and S charts).

    Args:
        means: List of subgroup means
        variations: List of subgroup variations (ranges or std devs)
        subgroup_size: Subgroup size (can be average for variable subgroups)
        calc_A: Function to calculate A constant (A2 for R, A3 for S)
        calc_center: Function to calculate center constant (d2 for R, c4 for S)
        calc_lower_limit: Function to calculate lower limit constant (D3 for R, B3 for S)
        calc_upper_limit: Function to calculate upper limit constant (D4 for R, B4 for S)

    Returns:
        Dictionary with all control limit values
    """
    grand_average = mean(means)
    # Filter out NaN variations before calculating average
    valid_variations = [v for v in variations if not math.isnan(v)]
    if valid_variations:
        avg_variation = mean(valid_variations)
    else:
        avg_variation = 0.0

    # Round subgroup size to nearest integer for constant lookup
    n = round(subgroup_size)
    if n < 2:
        n = 2  # Minimum valid subgroup size

    A = calc_A(n)
    center = calc_center(n)
    lower_limit = calc_lower_limit(n)
    upper_limit = calc_upper_limit(n)

    # Data chart limits
    uclx = grand_average + A * avg_variation
    clx = grand_average
    lclx = grand_average - A * avg_variation

    # Sigma lines
    usigma1x = grand_average + (1 / (center * math.sqrt(n))) * avg_variation
    usigma2x = grand_average + (2 / (center * math.sqrt(n))) * avg_variation
    lsigma1x = grand_average - (1 / (center * math.sqrt(n))) * avg_variation
    lsigma2x = grand_average - (2 / (center * math.sqrt(n))) * avg_variation

    # Variation chart limits
    var_ucl = upper_limit * avg_variation
    var_cl = avg_variation
    var_lcl = lower_limit * avg_variation

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
