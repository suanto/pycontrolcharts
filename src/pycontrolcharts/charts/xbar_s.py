"""X-bar and S (Mean and Standard Deviation) control chart."""

from pycontrolcharts.models import RunTestConfig
import pandas as pd

# Import the unified implementation from xbar_r module
from pycontrolcharts.charts.xbar_r import _xbar_variation_chart


def xbar_s_chart(
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
    Create an X-bar and S (Mean and Standard Deviation) control chart.

    Returns a DataFrame with ONE ROW PER SUBGROUP containing both the subgroup mean
    and subgroup standard deviation in the same row.

    Recommended when subgroup size >= 10 or when better estimates of variation are needed.

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
        >>> df = calc_xbar_s(data, subgroup_size=3)
        >>> print(len(df))  # 4 subgroups

    Example (variable subgroups):
        >>> df = pd.DataFrame({
        ...     'measurement': [10, 11, 12, 9, 10, 11, 13],
        ...     'batch': ['A', 'A', 'A', 'B', 'B', 'C', 'C']
        ... })
        >>> result = calc_xbar_s(df, value_column='measurement', subgroup='batch')
        >>> print(len(result))  # 3 subgroups (A, B, C)
    """
    return _xbar_variation_chart(
        data=data,
        variation_type='stddev',
        subgroup_size=subgroup_size,
        subgroup=subgroup,
        value_column=value_column,
        label=label,
        phase=phase,
        spec_upper=spec_upper,
        spec_lower=spec_lower,
        run_tests=run_tests,
    )
