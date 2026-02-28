"""
Unit tests for statistical constants.

These tests verify that all constant calculation functions produce
the correct values according to standard SPC tables.
"""

import pytest
from pycontrolcharts.constants import (
    calc_c4,
    calc_d2,
    calc_d3,
    calc_a2,
    calc_a3,
    calc_b3,
    calc_b4,
    calc_d3_limit,
    calc_d4_limit,
)


def test_c4_n2():
    assert calc_c4(2) == pytest.approx(0.7979, abs=0.0001)


def test_c4_n3():
    assert calc_c4(3) == pytest.approx(0.8862, abs=0.0001)


def test_c4_n5():
    assert calc_c4(5) == pytest.approx(0.9400, abs=0.0001)


def test_c4_n10():
    assert calc_c4(10) == pytest.approx(0.9727, abs=0.0001)


def test_c4_n25():
    assert calc_c4(25) == pytest.approx(0.9896, abs=0.0001)


def test_c4_less_than_2():
    assert calc_c4(1) == 0.0
    assert calc_c4(0) == 0.0


def test_d2_n2():
    assert calc_d2(2) == pytest.approx(1.128, abs=0.001)


def test_d2_n3():
    assert calc_d2(3) == pytest.approx(1.693, abs=0.001)


def test_d2_n5():
    assert calc_d2(5) == pytest.approx(2.326, abs=0.001)


def test_d2_n10():
    assert calc_d2(10) == pytest.approx(3.078, abs=0.001)


def test_d2_n25():
    assert calc_d2(25) == pytest.approx(3.931, abs=0.001)


def test_d2_less_than_2():
    assert calc_d2(1) == 0.0


def test_d3_n2():
    assert calc_d3(2) == pytest.approx(0.8525, abs=0.0001)


def test_d3_n5():
    assert calc_d3(5) == pytest.approx(0.8641, abs=0.0001)


def test_d3_n10():
    assert calc_d3(10) == pytest.approx(0.7971, abs=0.0001)


def test_d3_negative():
    assert calc_d3(-1) == 0.0


def test_a2_n2():
    assert calc_a2(2) == pytest.approx(1.880, abs=0.001)


def test_a2_n3():
    assert calc_a2(3) == pytest.approx(1.023, abs=0.001)


def test_a2_n5():
    assert calc_a2(5) == pytest.approx(0.577, abs=0.001)


def test_a2_n10():
    assert calc_a2(10) == pytest.approx(0.308, abs=0.001)


def test_a2_n15():
    assert calc_a2(15) == pytest.approx(0.223, abs=0.001)


def test_a2_n20():
    # For n > 15, calculated using formula
    result = calc_a2(20)
    assert result > 0
    assert result < calc_a2(15)  # Should decrease as n increases


def test_a3_n2():
    assert calc_a3(2) == pytest.approx(2.659, abs=0.001)


def test_a3_n3():
    assert calc_a3(3) == pytest.approx(1.954, abs=0.001)


def test_a3_n5():
    assert calc_a3(5) == pytest.approx(1.427, abs=0.001)


def test_a3_n10():
    assert calc_a3(10) == pytest.approx(0.975, abs=0.001)


def test_b3_n2():
    assert calc_b3(2) == 0.0


def test_b3_n5():
    assert calc_b3(5) == 0.0


def test_b3_n6():
    assert calc_b3(6) == pytest.approx(0.030, abs=0.001)


def test_b3_n10():
    assert calc_b3(10) == pytest.approx(0.284, abs=0.001)


def test_b4_n2():
    assert calc_b4(2) == pytest.approx(3.267, abs=0.001)


def test_b4_n3():
    assert calc_b4(3) == pytest.approx(2.568, abs=0.001)


def test_b4_n5():
    assert calc_b4(5) == pytest.approx(2.089, abs=0.001)


def test_b4_n10():
    assert calc_b4(10) == pytest.approx(1.716, abs=0.001)


def test_d3_limit_n2():
    assert calc_d3_limit(2) == 0.0


def test_d3_limit_n7():
    assert calc_d3_limit(7) == pytest.approx(0.076, abs=0.001)


def test_d3_limit_n10():
    assert calc_d3_limit(10) == pytest.approx(0.223, abs=0.001)


def test_d4_limit_n2():
    assert calc_d4_limit(2) == pytest.approx(3.268, abs=0.001)


def test_d4_limit_n3():
    assert calc_d4_limit(3) == pytest.approx(2.574, abs=0.001)


def test_d4_limit_n5():
    assert calc_d4_limit(5) == pytest.approx(2.114, abs=0.001)


def test_d4_limit_n10():
    assert calc_d4_limit(10) == pytest.approx(1.777, abs=0.001)


def test_constants_at_100():
    """Test that constants work at the maximum table size."""
    assert calc_c4(100) > 0
    assert calc_d2(100) > 0
    assert calc_d3(100) > 0


def test_constants_above_100():
    """Test that constants cap at 100 (no extrapolation beyond table)."""
    # Should return the value at index 100
    assert calc_c4(150) == calc_c4(100)
    assert calc_d2(150) == calc_d2(100)


def test_negative_inputs():
    """Test that negative inputs are handled gracefully."""
    assert calc_a2(-1) == 0.0
    assert calc_a3(-5) == 0.0
    assert calc_b3(-1) == 0.0
    assert calc_b4(-1) == 0.0
