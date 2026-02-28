"""np-chart (Number Defective) for attribute data with constant sample size."""

import math
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


def np_chart(
    data: list | pd.Series | pd.DataFrame,
    *,
    value_column: str | None = None,
    sample_size: int,
    label: str | list | None = None,
    phase: str | list | None = None,
    spec_upper: float | list[float] | str | None = None,
    spec_lower: float | list[float] | str | None = None,
    run_tests: bool | RunTestConfig = True,
) -> pd.DataFrame:
    """
    Create an np-chart (number defective) for attribute data with constant sample size.

    Args:
        data: Input data (list, Series, or DataFrame)
        value_column: Column name for defective counts (required if DataFrame)
        sample_size: Constant sample size for all samples
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
        ValueError: If value_column/column not found or length mismatch.
        TypeError: If data is not a list, Series, or DataFrame.

    Returns:
        pandas DataFrame with defect count data and control limits (standardized columns;
        see User Guide and API reference).

    Examples:
        >>> # List input
        >>> df = calc_np(data=[5, 3, 7, 4, 6], sample_size=100)

        >>> # Series input
        >>> defectives = pd.Series([5, 3, 7, 4, 6])
        >>> df = calc_np(data=defectives, sample_size=100)

        >>> # DataFrame input
        >>> input_df = pd.DataFrame({'defects': [5, 3, 7, 4, 6]})
        >>> df = calc_np(data=input_df, value_column='defects', sample_size=100)
    """
    # Normalize input
    defect_counts, labels, phases = normalize_simple_input(
        data, value_column, label, phase
    )

    if not defect_counts:
        return create_empty_chart_dataframe(include_variation=False)

    # Determine phase boundaries
    phase_info = get_phase_boundaries(phases, len(defect_counts))

    # Calculate control limits for each phase
    phase_data = []
    for start, end, phase_label in phase_info:
        phase_defects = defect_counts[start:end]

        # Calculate average proportion for this phase
        avg_defects = sum(phase_defects) / len(phase_defects)
        p_bar = avg_defects / sample_size

        limits = _calc_np_limits(p_bar, sample_size)
        phase_data.append((start, end, phase_label, limits))

    # Create per-point control limits
    control_limits_per_point, phase_labels = create_phase_limits(
        phase_data, len(defect_counts)
    )

    # Apply run tests (per phase so windows do not cross boundaries)
    config = normalize_run_tests_config(run_tests)
    violations = apply_run_tests(
        defect_counts,
        control_limits_per_point,
        config,
        phase_boundaries=phase_info,
    )

    # Normalize specification limits
    spec_upper_list, spec_lower_list = normalize_spec_limit_pair(
        data, spec_upper, spec_lower, len(defect_counts)
    )

    return build_output_dataframe(
        values=defect_counts,
        labels=labels,
        control_limits=control_limits_per_point,
        phases=phase_labels,
        spec_upper=spec_upper_list,
        spec_lower=spec_lower_list,
        violations=violations,
    )


def _calc_np_limits(p_bar: float, sample_size: int) -> dict[str, float]:
    """Calculate np-chart control limits."""
    np_bar = p_bar * sample_size
    limit = math.sqrt(np_bar * (1 - p_bar))

    clx = np_bar
    uclx = np_bar + 3 * limit
    lclx = max(np_bar - 3 * limit, 0.0)

    return {
        'ucl': uclx,
        'sigma_2_upper': np_bar + 2 * limit,
        'sigma_1_upper': np_bar + 1 * limit,
        'center_line': clx,
        'sigma_1_lower': max(np_bar - 1 * limit, 0.0),
        'sigma_2_lower': max(np_bar - 2 * limit, 0.0),
        'lcl': lclx,
        'var_ucl': 0,
        'var_cl': 0,
        'var_lcl': 0,
    }
