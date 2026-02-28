"""
Data models for control charts.

This module defines the minimal data structures used in pycontrolcharts.
The library now returns pandas DataFrames directly instead of complex nested objects.
"""

from dataclasses import dataclass
from enum import IntEnum, Enum


class RunType(IntEnum):
    """
    Run test violation types.

    Based on Western Electric and Nelson run test rules.
    Values are used as integers in DataFrame violations column.
    """

    OVER_UCL = 1  # Point beyond upper control limit
    UNDER_LCL = 2  # Point beyond lower control limit
    X_OVER_AVG = 3  # N consecutive points above center line
    X_UNDER_AVG = 4  # N consecutive points below center line
    X_INCREASING = 5  # N consecutive increasing points
    X_DECREASING = 6  # N consecutive decreasing points
    X_OVER_2SIGMA = 7  # 2 of 3 points beyond +2σ
    X_UNDER_2SIGMA = 8  # 2 of 3 points beyond -2σ
    X_UNDER_1SIGMA = 9  # 4 of 5 points beyond -1σ
    X_OVER_1SIGMA = 10  # 4 of 5 points beyond +1σ


@dataclass
class RunTestConfig:
    """
    Configuration for which run tests to apply and their thresholds.

    Simplified configuration for run tests. Pass True to use defaults,
    False to disable, or a RunTestConfig object to customize.

    Attributes:
        test1: Test 1 - Points beyond control limits (enabled by default)
        test2: Test 2 - N consecutive points on same side of center (enabled by default)
        test3: Test 3 - N consecutive increasing or decreasing points (enabled by default)
        test5: Test 5 - 2 of 3 points beyond 2-sigma (enabled by default)
        test6: Test 6 - 4 of 5 points beyond 1-sigma (enabled by default)
        test2_n: Threshold for test 2 (default 9 per Nelson)
        test3_n: Threshold for test 3 (default 6 per Nelson)
    """

    test1: bool = True
    test2: bool = True
    test3: bool = True
    test5: bool = True
    test6: bool = True
    test2_n: int = 9
    test3_n: int = 6


@dataclass
class CustomLimits:
    """
    Custom control limits for run tests (no limit calculation from data).

    Main chart limits are required; sigma lines, spec limits, and variation
    chart limits are optional. When sigma lines are not provided, output
    columns are NaN and run tests 5 and 6 are not performed.

    Attributes:
        center_line: Process center line (required).
        ucl: Upper control limit (required).
        lcl: Lower control limit (required).
        sigma_1_upper: Upper 1σ line; optional; test 6 not performed when missing.
        sigma_1_lower: Lower 1σ line; optional; test 6 not performed when missing.
        sigma_2_upper: Upper 2σ line; optional; test 5 not performed when missing.
        sigma_2_lower: Lower 2σ line; optional; test 5 not performed when missing.
        spec_upper: Upper specification limit (single value, broadcast to all points).
        spec_lower: Lower specification limit (single value, broadcast to all points).
        variation_ucl: UCL for variation chart (e.g. moving range); optional.
        variation_cl: Center line for variation chart; optional.
        variation_lcl: LCL for variation chart; optional.
    """

    center_line: float
    ucl: float
    lcl: float
    sigma_1_upper: float | None = None
    sigma_1_lower: float | None = None
    sigma_2_upper: float | None = None
    sigma_2_lower: float | None = None
    spec_upper: float | None = None
    spec_lower: float | None = None
    variation_ucl: float | None = None
    variation_cl: float | None = None
    variation_lcl: float | None = None


class ChartType(str, Enum):
    """
    Supported control chart types. Used by plot_control_chart() to select rendering.
    """

    XMR = 'xmr'  # Individuals and Moving Range
    XBAR_R = 'xbar_r'  # Mean and Range
    XBAR_S = 'xbar_s'  # Mean and Standard Deviation
    P = 'p'  # Proportion defective
    NP = 'np'  # Number defective
    C = 'c'  # Count of defects
    U = 'u'  # Defects per unit
