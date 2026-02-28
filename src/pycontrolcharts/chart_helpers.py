"""
Common helper functions used across all control chart implementations.

These functions extract repeated patterns to maintain consistency
and reduce code duplication across chart types.
"""

import pandas as pd

from pycontrolcharts.models import RunTestConfig
from pycontrolcharts.input_handlers import normalize_spec_limits
from pycontrolcharts.utils import (
    find_phase_boundaries,
    find_phase_boundaries_from_labels,
)


def normalize_run_tests_config(run_tests: bool | RunTestConfig) -> RunTestConfig | None:
    """
    Convert run_tests parameter to RunTestConfig object or None.

    Args:
        run_tests: Boolean or RunTestConfig object
            - True: Returns default RunTestConfig()
            - False: Returns None (disables all tests)
            - RunTestConfig: Returns the provided config object

    Returns:
        RunTestConfig object or None

    Example:
        >>> config = normalize_run_tests_config(True)
        >>> isinstance(config, RunTestConfig)
        True

        >>> config = normalize_run_tests_config(False)
        >>> config is None
        True
    """
    if run_tests is True:
        return RunTestConfig()
    elif run_tests is False:
        return None
    else:
        return run_tests


def create_empty_chart_dataframe(include_variation: bool = False) -> pd.DataFrame:
    """
    Create an empty DataFrame with standard chart columns.

    Args:
        include_variation: If True, includes variation chart columns
                          (for variables charts like XmR, X-bar/R, X-bar/S)
                          If False, returns attribute chart columns only

    Returns:
        Empty pandas DataFrame with appropriate columns

    Example:
        >>> df = create_empty_chart_dataframe(include_variation=False)
        >>> 'violations' in df.columns
        True
        >>> 'variation' in df.columns
        False

        >>> df = create_empty_chart_dataframe(include_variation=True)
        >>> 'variation' in df.columns
        True
    """
    columns = [
        'point_id',
        'value',
        'label',
        'ucl',
        'sigma_2_upper',
        'sigma_1_upper',
        'center_line',
        'sigma_1_lower',
        'sigma_2_lower',
        'lcl',
        'spec_upper',
        'spec_lower',
        'phase',
        'violations',
    ]

    if include_variation:
        columns.extend(
            [
                'variation',
                'variation_ucl',
                'variation_cl',
                'variation_lcl',
                'variation_violations',
            ]
        )

    return pd.DataFrame(columns=columns)


def get_phase_boundaries(
    phases: list[str] | None, data_length: int
) -> list[tuple[int, int, str | None]]:
    """
    Convert phase labels to phase boundary tuples.

    This is a convenience wrapper that handles both labeled and unlabeled phases.

    Args:
        phases: List of phase labels (one per data point) or None
        data_length: Total number of data points

    Returns:
        List of (start_idx, end_idx, phase_label) tuples
        Indices are half-open intervals: [start, end)

    Example:
        >>> # Single phase (no labels)
        >>> boundaries = get_phase_boundaries(None, 10)
        >>> boundaries
        [(0, 10, None)]

        >>> # Multiple labeled phases
        >>> phases = ['A', 'A', 'A', 'B', 'B']
        >>> boundaries = get_phase_boundaries(phases, 5)
        >>> boundaries
        [(0, 3, 'A'), (3, 5, 'B')]
    """
    if phases is not None:
        return find_phase_boundaries_from_labels(phases, data_length)
    else:
        boundaries = find_phase_boundaries(None, data_length)
        return [(start, end, None) for start, end in boundaries]


def normalize_spec_limit_pair(
    data: list | pd.Series | pd.DataFrame,
    spec_upper: float | list[float] | str | None,
    spec_lower: float | list[float] | str | None,
    data_length: int,
) -> tuple[list[float] | None, list[float] | None]:
    """
    Normalize both specification limits at once.

    This is a convenience wrapper around normalize_spec_limits that handles
    both upper and lower limits together.

    Args:
        data: Input data (used to extract spec limits if they're column names)
        spec_upper: Upper spec limit - float, list, column name, or None
        spec_lower: Lower spec limit - float, list, column name, or None
        data_length: Number of data points (for validation)

    Returns:
        Tuple of (spec_upper_list, spec_lower_list)
        Each is a list of floats (one per point) or None

    Example:
        >>> upper, lower = normalize_spec_limit_pair(
        ...     data=[1, 2, 3],
        ...     spec_upper=10.0,
        ...     spec_lower=0.0,
        ...     data_length=3
        ... )
        >>> upper
        [10.0, 10.0, 10.0]
        >>> lower
        [0.0, 0.0, 0.0]
    """
    df_data = data if isinstance(data, pd.DataFrame) else None
    spec_upper_list = normalize_spec_limits(
        df_data, spec_upper, data_length, 'spec_upper'
    )
    spec_lower_list = normalize_spec_limits(
        df_data, spec_lower, data_length, 'spec_lower'
    )
    return spec_upper_list, spec_lower_list
