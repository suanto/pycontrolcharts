"""
Unit tests for internal calculation functions.

NOTE: These tests are for internal implementation functions and are not
part of the public API test suite. They are useful for implementation
validation but end users should rely on the high-level chart functions.

If you need to test internal functions during development, you can
uncomment and adapt the tests below. However, the public API tests
(test_imr_chart.py, test_r_s_charts.py) should be sufficient for
validating correctness.
"""

import pandas as pd

from pycontrolcharts import calc_xmr


def test_calc_xmr_returns_dataframe():
    """Smoke test: public API calc_xmr is callable and returns a DataFrame."""
    df = calc_xmr([1.0, 2.0, 3.0], run_tests=False)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
