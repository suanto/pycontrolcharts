"""p-chart (Proportion Defective) for attribute data."""

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


def p_chart(
    data: list | pd.Series | pd.DataFrame,
    *,
    sample_size_column: str | None = None,
    value_column: str | None = None,
    sample_size: int | list[int] | str | None = None,
    label: str | list | None = None,
    phase: str | list | None = None,
    spec_upper: float | list[float] | str | None = None,
    spec_lower: float | list[float] | str | None = None,
    run_tests: bool | RunTestConfig = True,
) -> pd.DataFrame:
    """
    Create a p-chart (proportion defective) for attribute data.

    Monitors the proportion of defective items with variable or constant sample sizes.

    Args:
        data: Input data (list, Series, or DataFrame)
        sample_size_column: Column name for sample sizes (optional if DataFrame with constant size)
        value_column: Column name for defective counts (required if DataFrame)
        sample_size: Sample size - int (constant), list (variable), or str (column name)
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
        ValueError: If value_column/column not found or length mismatch; or sample_size
            or sample_size_column invalid or missing when required.
        TypeError: If data is not a list, Series, or DataFrame.

    Returns:
        pandas DataFrame with proportion defective data and control limits (standardized
        columns; see User Guide and API reference).

    Examples:
        >>> # List with constant sample size
        >>> df = calc_p(data=[5, 3, 7, 4, 6], sample_size=100)

        >>> # List with variable sample sizes
        >>> df = calc_p(data=[5, 3, 7, 4, 6], sample_size=[100, 100, 120, 110, 100])

        >>> # Series input
        >>> defectives = pd.Series([5, 3, 7, 4, 6])
        >>> df = calc_p(data=defectives, sample_size=100)

        >>> # DataFrame input
        >>> input_df = pd.DataFrame({'defects': [5, 3, 7], 'inspected': [100, 100, 120]})
        >>> df = calc_p(data=input_df, value_column='defects', sample_size_column='inspected')
    """
    # Normalize input
    defect_counts, sizes, labels, phases = normalize_dual_input(
        data,
        None,
        sample_size_column,
        value_column,
        sample_size,
        label,
        phase,
    )

    if not defect_counts:
        return create_empty_chart_dataframe(include_variation=False)

    # Calculate proportions
    if isinstance(sizes, int):
        # Constant sample size
        proportions = [d / sizes for d in defect_counts]
        sizes_list = [sizes] * len(defect_counts)
    else:
        # Variable sample sizes
        proportions = [d / s if s > 0 else 0.0 for d, s in zip(defect_counts, sizes)]
        sizes_list = sizes

    # Determine phase boundaries
    phase_info = get_phase_boundaries(phases, len(proportions))

    # Calculate control limits for each phase
    phase_data = []
    for start, end, phase_label in phase_info:
        phase_defects = defect_counts[start:end]
        phase_sizes = sizes_list[start:end]

        # Calculate grand average proportion for this phase
        total_defects = sum(phase_defects)
        total_inspected = sum(phase_sizes)
        p_bar = total_defects / total_inspected if total_inspected > 0 else 0.0

        # For p-chart, limits vary by sample size, so we create per-point limits
        phase_limits = []
        for i in range(start, end):
            n = sizes_list[i]
            limits = _calc_p_limits(p_bar, n)
            phase_limits.append(limits)

        phase_data.append((start, end, phase_label, phase_limits))

    # Create per-point control limits
    control_limits_per_point = []
    phase_labels = []
    for start, end, phase_label, phase_limits in phase_data:
        control_limits_per_point.extend(phase_limits)
        phase_labels.extend([phase_label] * (end - start))

    # Apply run tests if enabled (per phase so windows do not cross boundaries)
    config = normalize_run_tests_config(run_tests)
    violations = apply_run_tests(
        proportions,
        control_limits_per_point,
        config,
        phase_boundaries=phase_info,
    )

    # Normalize specification limits
    spec_upper_list, spec_lower_list = normalize_spec_limit_pair(
        data, spec_upper, spec_lower, len(proportions)
    )

    # Build output DataFrame (no variation for attribute charts)
    return build_output_dataframe(
        values=proportions,
        labels=labels,
        control_limits=control_limits_per_point,
        phases=phase_labels,
        spec_upper=spec_upper_list,
        spec_lower=spec_lower_list,
        violations=violations,
    )


def _calc_p_limits(proportion: float, sample_size: int) -> dict[str, float]:
    """Calculate p-chart control limits for a single point."""
    if sample_size <= 0:
        return {
            'ucl': 0,
            'sigma_2_upper': 0,
            'sigma_1_upper': 0,
            'center_line': proportion,
            'sigma_1_lower': 0,
            'sigma_2_lower': 0,
            'lcl': 0,
        }

    limit = math.sqrt(proportion * (1 - proportion) / sample_size)

    clx = proportion
    uclx = min(proportion + 3 * limit, 1.0)
    lclx = max(proportion - 3 * limit, 0.0)

    usigma1x = min(proportion + 1 * limit, 1.0)
    usigma2x = min(proportion + 2 * limit, 1.0)
    lsigma1x = max(proportion - 1 * limit, 0.0)
    lsigma2x = max(proportion - 2 * limit, 0.0)

    return {
        'ucl': uclx,
        'sigma_2_upper': usigma2x,
        'sigma_1_upper': usigma1x,
        'center_line': clx,
        'sigma_1_lower': lsigma1x,
        'sigma_2_lower': lsigma2x,
        'lcl': lclx,
        'var_ucl': 0,  # No variation chart
        'var_cl': 0,
        'var_lcl': 0,
    }
