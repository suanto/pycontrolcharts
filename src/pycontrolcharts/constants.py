"""
SPC (Statistical Process Control) constants for control chart calculations.

This module provides functions to calculate SPC constants based on subgroup size (n).
Constants are used for calculating control limits in various control charts.

References:
    - Wheeler, Donald J. "Understanding Statistical Process Control"
    - Montgomery, Douglas C. "Introduction to Statistical Quality Control"
"""

import math


def calc_c4(n: int) -> float:
    """
    Calculate the c4 constant used in S-charts.

    The c4 constant is used to unbias the standard deviation estimate.
    For n <= 100, uses lookup table. For n > 100, uses formula.

    Args:
        n: Subgroup size

    Returns:
        c4 constant value, or 0 if n < 2
    """
    if n < 2:
        return 0.0

    _c4_table = (
        0,
        0.0000,
        0.7979,
        0.8862,
        0.9213,
        0.9400,
        0.9515,
        0.9594,
        0.9650,
        0.9693,
        0.9727,
        0.9755,
        0.9776,
        0.9794,
        0.9810,
        0.9823,
        0.9835,
        0.9845,
        0.9854,
        0.9862,
        0.9869,
        0.9876,
        0.9882,
        0.9887,
        0.9892,
        0.9896,
        0.9896,
        0.9896,
        0.9896,
        0.9896,
        0.9915,  # 30
        0.9915,
        0.9915,
        0.9915,
        0.9915,
        0.9927,
        0.9927,
        0.9927,
        0.9927,
        0.9927,
        0.9936,
        0.9936,
        0.9936,
        0.9936,
        0.9936,
        0.9943,
        0.9943,
        0.9943,
        0.9943,
        0.9943,
        0.9949,  # 50
        0.9949,
        0.9949,
        0.9949,
        0.9949,
        0.9949,
        0.9949,
        0.9949,
        0.9949,
        0.9949,
        0.9957,
        0.9957,
        0.9957,
        0.9957,
        0.9957,
        0.9957,
        0.9957,
        0.9957,
        0.9957,
        0.9957,
        0.9963,  # 70
        0.9963,
        0.9963,
        0.9963,
        0.9963,
        0.9963,
        0.9963,
        0.9963,
        0.9963,
        0.9963,
        0.9968,
        0.9968,
        0.9968,
        0.9968,
        0.9968,
        0.9968,
        0.9968,
        0.9968,
        0.9968,
        0.9968,
        0.9972,
        0.9972,
        0.9972,
        0.9972,
        0.9972,
        0.9972,
        0.9972,
        0.9972,
        0.9972,
        0.9972,
        0.9975,
    )

    return _c4_table[min(n, 100)]


def calc_d2(n: int) -> float:
    """
    Calculate the d2 constant used in R-charts and XmR charts.

    The d2 constant relates the average range to the process standard deviation.
    Uses a lookup table; subgroup sizes beyond the table use the maximum table value.

    Args:
        n: Subgroup size

    Returns:
        d2 constant value, or 0 if n < 2
    """
    if n < 2:
        return 0.0

    _d2_table = (
        0,
        0.000,
        1.128,
        1.693,
        2.059,
        2.326,
        2.534,
        2.704,
        2.847,
        2.970,
        3.078,
        3.173,
        3.258,
        3.336,
        3.407,
        3.472,
        3.532,
        3.588,
        3.640,
        3.689,
        3.735,
        3.778,
        3.819,
        3.858,
        3.895,
        3.931,
        3.931,
        3.931,
        3.931,
        3.931,
        4.086,  # 30
        4.086,
        4.086,
        4.086,
        4.086,
        4.213,
        4.213,
        4.213,
        4.213,
        4.213,
        4.322,
        4.322,
        4.322,
        4.322,
        4.322,
        4.415,
        4.415,
        4.415,
        4.415,
        4.415,
        4.498,  # 50
        4.498,
        4.498,
        4.498,
        4.498,
        4.498,
        4.498,
        4.498,
        4.498,
        4.498,
        4.639,
        4.639,
        4.639,
        4.639,
        4.639,
        4.639,
        4.639,
        4.639,
        4.639,
        4.639,
        4.755,  # 70
        4.755,
        4.755,
        4.755,
        4.755,
        4.755,
        4.755,
        4.755,
        4.755,
        4.755,
        4.854,
        4.854,
        4.854,
        4.854,
        4.854,
        4.854,
        4.854,
        4.854,
        4.854,
        4.854,
        4.939,
        4.939,
        4.939,
        4.939,
        4.939,
        4.939,
        4.939,
        4.939,
        4.939,
        4.939,
        5.015,
    )

    return _d2_table[min(n, 100)]


def calc_d3(n: int) -> float:
    """
    Calculate the d3 constant used in R-chart calculations.

    The d3 constant is used to calculate standard deviation of the range.
    For n <= 100, uses lookup table.

    Args:
        n: Subgroup size

    Returns:
        d3 constant value, or 0 if n < 0
    """
    if n < 0:
        return 0.0

    _d3_table = (
        0,
        0.0000,
        0.8525,
        0.8884,
        0.8798,
        0.8641,
        0.8480,
        0.8332,
        0.8198,
        0.8078,
        0.7971,
        0.7873,
        0.7785,
        0.7704,
        0.7630,
        0.7562,
        0.7499,
        0.7441,
        0.7386,
        0.7335,
        0.7287,
        0.7272,
        0.7199,
        0.7159,
        0.7121,
        0.7084,
        0.7084,
        0.7084,
        0.7084,
        0.7084,
        0.6927,  # 30
        0.6927,
        0.6927,
        0.6927,
        0.6927,
        0.6799,
        0.6799,
        0.6799,
        0.6799,
        0.6799,
        0.6692,
        0.6692,
        0.6692,
        0.6692,
        0.6692,
        0.6601,
        0.6601,
        0.6601,
        0.6601,
        0.6601,
        0.6521,  # 50
        0.6521,
        0.6521,
        0.6521,
        0.6521,
        0.6521,
        0.6521,
        0.6521,
        0.6521,
        0.6521,
        0.6389,  # 60
        0.6389,
        0.6389,
        0.6389,
        0.6389,
        0.6389,
        0.6389,
        0.6389,
        0.6389,
        0.6389,
        0.6283,  # 70
        0.6283,
        0.6283,
        0.6283,
        0.6283,
        0.6283,
        0.6283,
        0.6283,
        0.6283,
        0.6283,
        0.6194,
        0.6194,
        0.6194,
        0.6194,
        0.6194,
        0.6194,
        0.6194,
        0.6194,
        0.6194,
        0.6194,
        0.6118,
        0.6118,
        0.6118,
        0.6118,
        0.6118,
        0.6118,
        0.6118,
        0.6118,
        0.6118,
        0.6118,
        0.6052,  # 100
    )

    return _d3_table[min(n, 100)]


def calc_a2(n: int) -> float:
    """
    Calculate the A2 constant for X-bar and R charts.

    Used to calculate control limits on the X-bar chart.
    For n <= 15, uses lookup table. For n > 15, calculates using d2.

    Args:
        n: Subgroup size

    Returns:
        A2 constant value, or 0 if n < 0
    """
    if n < 0:
        return 0.0

    _a2_table = (
        0,
        0.000,
        1.880,
        1.023,
        0.729,
        0.577,
        0.483,
        0.419,
        0.373,
        0.337,
        0.308,
        0.285,
        0.266,
        0.249,
        0.235,
        0.223,
    )

    if n <= 15:
        return _a2_table[n]
    else:
        d2 = calc_d2(n)
        return 3 / (d2 * math.sqrt(n))


def calc_a3(n: int) -> float:
    """
    Calculate the A3 constant for X-bar and S charts.

    Used to calculate control limits on the X-bar chart.
    For n <= 15, uses lookup table. For n > 15, calculates using c4.

    Args:
        n: Subgroup size

    Returns:
        A3 constant value, or 0 if n < 0
    """
    if n < 0:
        return 0.0

    _a3_table = (
        0,
        0.000,
        2.659,
        1.954,
        1.628,
        1.427,
        1.287,
        1.182,
        1.099,
        1.032,
        0.975,
        0.927,
        0.886,
        0.850,
        0.817,
        0.789,
    )

    if n <= 15:
        return _a3_table[n]
    else:
        c4 = calc_c4(n)
        return 3 / (c4 * math.sqrt(n))


def calc_b3(n: int) -> float:
    """
    Calculate the B3 constant for S charts (lower control limit).

    Used to calculate the lower control limit on the S chart.
    For n <= 15, uses lookup table. For n > 15, calculates using c4.

    Args:
        n: Subgroup size

    Returns:
        B3 constant value, or 0 if n < 0
    """
    if n < 0:
        return 0.0

    _b3_table = (
        0,
        0.000,
        0.000,
        0.000,
        0.000,
        0.000,
        0.030,
        0.118,
        0.185,
        0.239,
        0.284,
        0.322,
        0.354,
        0.382,
        0.407,
        0.428,
    )

    if n <= 15:
        return _b3_table[n]
    else:
        c4 = calc_c4(n)
        return 1 - ((3 / c4) * math.sqrt(1 - (c4 * c4)))


def calc_b4(n: int) -> float:
    """
    Calculate the B4 constant for S charts (upper control limit).

    Used to calculate the upper control limit on the S chart.
    For n <= 15, uses lookup table. For n > 15, calculates using c4.

    Args:
        n: Subgroup size

    Returns:
        B4 constant value, or 0 if n < 0
    """
    if n < 0:
        return 0.0

    _b4_table = (
        0,
        0.000,
        3.267,
        2.568,
        2.266,
        2.089,
        1.970,
        1.882,
        1.815,
        1.761,
        1.716,
        1.678,
        1.646,
        1.619,
        1.593,
        1.572,
    )

    if n <= 15:
        return _b4_table[n]
    else:
        c4 = calc_c4(n)
        return 1 + ((3 / c4) * math.sqrt(1 - (c4 * c4)))


def calc_d3_limit(n: int) -> float:
    """
    Calculate the D3 constant for R charts (lower control limit).

    Used to calculate the lower control limit on the R chart.
    For n <= 15, uses lookup table. For n > 15, calculates using d2 and d3.

    Args:
        n: Subgroup size

    Returns:
        D3 constant value, or 0 if n < 0
    """
    if n < 0:
        return 0.0

    _d3_limit_table = (
        0,
        0.000,
        0.000,
        0.000,
        0.000,
        0.000,
        0.000,
        0.076,
        0.136,
        0.184,
        0.223,
        0.256,
        0.283,
        0.307,
        0.328,
        0.347,
    )

    if n <= 15:
        return _d3_limit_table[n]
    else:
        d3 = calc_d3(n)
        d2 = calc_d2(n)
        return 1 - ((3 * d3) / d2)


def calc_d4_limit(n: int) -> float:
    """
    Calculate the D4 constant for R charts (upper control limit).

    Used to calculate the upper control limit on the R chart.
    For n <= 15, uses lookup table. For n > 15, calculates using d2 and d3.

    Args:
        n: Subgroup size

    Returns:
        D4 constant value, or 0 if n < 0
    """
    if n < 0:
        return 0.0

    _d4_limit_table = (
        0,
        0.000,
        3.268,
        2.574,
        2.282,
        2.114,
        2.004,
        1.924,
        1.864,
        1.816,
        1.777,
        1.744,
        1.717,
        1.693,
        1.672,
        1.653,
    )

    if n <= 15:
        return _d4_limit_table[n]
    else:
        d3 = calc_d3(n)
        d2 = calc_d2(n)
        return 1 + ((3 * d3) / d2)


# Aliases for backward compatibility and uppercase naming
calc_A2 = calc_a2
calc_A3 = calc_a3
calc_B3 = calc_b3
calc_B4 = calc_b4
calc_D3 = calc_d3_limit
calc_D4 = calc_d4_limit
