"""
Shared fixtures for plotting tests. Builds minimal valid chart DataFrames without calc_*.
"""

import pandas as pd


def minimal_chart_df(
    n: int = 5,
    *,
    include_variation: bool = True,
    include_sigma: bool = False,
    include_spec: bool = False,
    include_violations: bool = False,
    include_phase: bool = False,
) -> pd.DataFrame:
    """
    Build minimal valid chart_df for plotting tests.

    Use this instead of calc_* so plotting tests do not depend on calculation correctness.
    """
    base: dict = {
        'label': list(range(n)),
        'value': [10.0] * n,
        'ucl': [15.0] * n,
        'lcl': [5.0] * n,
        'center_line': [10.0] * n,
    }
    if include_variation:
        base['variation'] = [1.0] * n
        base['variation_ucl'] = [3.0] * n
        base['variation_cl'] = [1.0] * n
        base['variation_lcl'] = [0.0] * n
    if include_sigma:
        base['sigma_2_upper'] = [14.0] * n
        base['sigma_1_upper'] = [12.0] * n
        base['sigma_1_lower'] = [8.0] * n
        base['sigma_2_lower'] = [6.0] * n
    if include_spec:
        base['spec_upper'] = [20.0] * n
        base['spec_lower'] = [0.0] * n
    if include_violations:
        # First point has violation, rest do not
        base['violations'] = [[{'type': 1, 'description': 'Point beyond UCL'}]] + [
            [] for _ in range(n - 1)
        ]
        if include_variation:
            # Second point has variation violation (when n >= 2)
            base['variation_violations'] = (
                (
                    [[]]
                    + [[{'type': 2, 'description': 'Below LCL'}]]
                    + [[] for _ in range(n - 2)]
                )
                if n >= 2
                else [[]] * n
            )
    if include_phase:
        # Two phases: first half A, second half B
        mid = (n + 1) // 2
        base['phase'] = ['A'] * mid + ['B'] * (n - mid)
    return pd.DataFrame(base)
