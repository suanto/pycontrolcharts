"""
Unit tests for attribute control charts (p, np, c, u).

These tests verify that attribute charts compute correctly using the new DataFrame API,
including control limit calculations and handling of variable sample sizes.
"""

import pytest
import math
import pandas as pd
from pycontrolcharts import calc_p, calc_np, calc_c, calc_u, RunTestConfig


def test_p_chart_basic_calc():
    """Test basic p-chart with constant sample sizes."""
    defectives = [5, 3, 7, 4, 6]
    df = calc_p(data=defectives, sample_size=100, run_tests=False)

    # Should return a DataFrame
    assert isinstance(df, pd.DataFrame)

    # Should have 5 rows
    assert len(df) == 5

    # Check required columns exist
    required_cols = [
        'label',
        'value',
        'center_line',
        'ucl',
        'lcl',
        'sigma_1_upper',
        'sigma_1_lower',
        'sigma_2_upper',
        'sigma_2_lower',
        'phase',
        'violations',
    ]
    for col in required_cols:
        assert col in df.columns

    # Check proportions are calculated correctly
    assert df['value'].iloc[0] == pytest.approx(0.05)  # 5/100
    assert df['value'].iloc[1] == pytest.approx(0.03)  # 3/100
    assert df['value'].iloc[2] == pytest.approx(0.07)  # 7/100

    # Check center line (average proportion)
    # total defectives = 25, total inspected = 500, p-bar = 0.05
    assert df['center_line'].iloc[0] == pytest.approx(0.05)

    # Check control limits are calculated
    assert df['ucl'].iloc[0] > df['center_line'].iloc[0]
    assert df['lcl'].iloc[0] <= df['center_line'].iloc[0]


def test_p_chart_variable_sample_sizes():
    """Test p-chart with variable sample sizes."""
    defectives = [5, 4, 6]
    sample_sizes = [100, 80, 120]
    df = calc_p(data=defectives, sample_size=sample_sizes, run_tests=False)

    assert len(df) == 3
    # Proportions should be calculated per sample
    assert df['value'].iloc[0] == pytest.approx(0.05)  # 5/100
    assert df['value'].iloc[1] == pytest.approx(0.05)  # 4/80
    assert df['value'].iloc[2] == pytest.approx(0.05)  # 6/120


def test_p_chart_with_run_tests():
    """Test p-chart with run tests enabled."""
    defectives = [5] * 10
    df = calc_p(data=defectives, sample_size=100, run_tests=RunTestConfig())

    assert 'violations' in df.columns
    # Violations column should contain lists
    assert isinstance(df['violations'].iloc[0], list)


def test_np_chart_basic_calc():
    """Test basic np-chart with constant sample size."""
    defectives = [5, 3, 7, 4, 6]
    df = calc_np(data=defectives, sample_size=100, run_tests=False)

    # Should return a DataFrame
    assert isinstance(df, pd.DataFrame)

    # Should have 5 rows
    assert len(df) == 5

    # Check values are the raw defective counts
    assert df['value'].iloc[0] == 5.0
    assert df['value'].iloc[1] == 3.0
    assert df['value'].iloc[2] == 7.0

    # Check center line (average number defective)
    # Average proportion = 25/(5*100) = 0.05, np = 0.05 * 100 = 5
    assert df['center_line'].iloc[0] == pytest.approx(5.0)

    # Check control limits are calculated
    assert df['ucl'].iloc[0] > df['center_line'].iloc[0]


def test_np_chart_with_run_tests():
    """Test np-chart with run tests enabled."""
    defectives = [5, 3, 7, 4, 6, 5, 4, 6, 5, 7]
    df = calc_np(data=defectives, sample_size=100, run_tests=RunTestConfig())

    assert 'violations' in df.columns
    assert isinstance(df['violations'].iloc[0], list)


def test_c_chart_basic_calc():
    """Test basic c-chart."""
    defects = [5, 3, 7, 4, 6, 2, 8, 5]
    df = calc_c(defects, run_tests=False)

    # Should return a DataFrame
    assert isinstance(df, pd.DataFrame)

    # Should have 8 rows
    assert len(df) == 8

    # Check values are the raw defect counts
    assert df['value'].iloc[0] == 5.0
    assert df['value'].iloc[1] == 3.0
    assert df['value'].iloc[2] == 7.0

    # Check center line (average defects)
    # Average = (5+3+7+4+6+2+8+5) / 8 = 40/8 = 5
    assert df['center_line'].iloc[0] == pytest.approx(5.0)

    # Check control limits: UCL = c-bar + 3*sqrt(c-bar) = 5 + 3*sqrt(5)
    expected_ucl = 5 + 3 * math.sqrt(5)
    assert df['ucl'].iloc[0] == pytest.approx(expected_ucl)

    # LCL = c-bar - 3*sqrt(c-bar), but cannot be negative
    expected_lcl = max(5 - 3 * math.sqrt(5), 0)
    assert df['lcl'].iloc[0] == pytest.approx(expected_lcl)


def test_c_chart_with_run_tests():
    """Test c-chart with run tests enabled."""
    defects = [5, 3, 7, 4, 6, 2, 8, 5, 4, 6]
    df = calc_c(defects, run_tests=RunTestConfig())

    assert 'violations' in df.columns
    assert isinstance(df['violations'].iloc[0], list)


def test_c_chart_zero_defects():
    """Test c-chart with some zero defects."""
    defects = [0, 1, 0, 2, 1, 0]
    df = calc_c(defects, run_tests=False)

    assert len(df) == 6
    assert df['value'].iloc[0] == 0.0
    # Average = 4/6 = 0.667
    assert df['center_line'].iloc[0] == pytest.approx(4 / 6)


def test_u_chart_basic_calc():
    """Test basic u-chart with variable areas."""
    defects = [10, 8, 12, 6, 15]
    areas = [10, 8, 12, 10, 10]
    df = calc_u(data=defects, area=areas, run_tests=False)

    # Should return a DataFrame
    assert isinstance(df, pd.DataFrame)

    # Should have 5 rows
    assert len(df) == 5

    # Check u-values are calculated correctly (defects per unit)
    assert df['value'].iloc[0] == pytest.approx(1.0)  # 10/10
    assert df['value'].iloc[1] == pytest.approx(1.0)  # 8/8
    assert df['value'].iloc[2] == pytest.approx(1.0)  # 12/12
    assert df['value'].iloc[3] == pytest.approx(0.6)  # 6/10
    assert df['value'].iloc[4] == pytest.approx(1.5)  # 15/10

    # Check center line (average defects per unit)
    # total defects = 51, total area = 50, u-bar = 51/50 = 1.02
    assert df['center_line'].iloc[0] == pytest.approx(51 / 50)

    # Check control limits are calculated
    assert df['ucl'].iloc[0] > df['center_line'].iloc[0]


def test_u_chart_constant_areas():
    """Test u-chart with constant areas (similar to c-chart)."""
    defects = [5, 3, 7, 4, 6]
    df = calc_u(data=defects, area=10, run_tests=False)

    assert len(df) == 5
    # u-values should be defects/10
    assert df['value'].iloc[0] == pytest.approx(0.5)
    assert df['value'].iloc[1] == pytest.approx(0.3)
    assert df['value'].iloc[2] == pytest.approx(0.7)


def test_u_chart_with_run_tests():
    """Test u-chart with run tests enabled."""
    defects = [10, 8, 12, 6, 15, 9, 11, 7, 13, 10]
    df = calc_u(data=defects, area=10, run_tests=RunTestConfig())

    assert 'violations' in df.columns
    assert isinstance(df['violations'].iloc[0], list)


def test_attribute_chart_p_with_phases():
    """Test p-chart with multiple phases."""
    defectives = [5, 3, 7, 10, 12, 11]
    phases = ['A', 'A', 'A', 'B', 'B', 'B']
    df = calc_p(data=defectives, sample_size=100, phase=phases, run_tests=False)

    # Should have phase column with phase names
    assert 'phase' in df.columns

    # Check unique phases
    phases_unique = df['phase'].unique()
    assert len(phases_unique) == 2

    # Phases should have different center lines
    phase1_cl = df[df['phase'] == phases_unique[0]]['center_line'].iloc[0]
    phase2_cl = df[df['phase'] == phases_unique[1]]['center_line'].iloc[0]
    assert phase1_cl != phase2_cl


def test_attribute_chart_c_with_phases():
    """Test c-chart with multiple phases."""
    defects = [3, 4, 3, 10, 11, 12]
    phases = ['pre', 'pre', 'pre', 'post', 'post', 'post']
    df = calc_c(defects, phase=phases, run_tests=False)

    # Should have phase column
    phases_unique = df['phase'].unique()
    assert len(phases_unique) == 2

    # First phase average: (3+4+3)/3 = 3.33
    # Second phase average: (10+11+12)/3 = 11
    phase1_cl = df[df['phase'] == phases_unique[0]]['center_line'].iloc[0]
    phase2_cl = df[df['phase'] == phases_unique[1]]['center_line'].iloc[0]
    assert phase1_cl == pytest.approx(10 / 3)
    assert phase2_cl == pytest.approx(11.0)


def test_p_chart_all_zeros():
    """Test p-chart with all zero defectives."""
    defectives = [0, 0, 0, 0, 0]
    df = calc_p(data=defectives, sample_size=100, run_tests=False)

    assert len(df) == 5
    # All proportions should be 0
    assert (df['value'] == 0.0).all()
    # Center line should be 0
    assert df['center_line'].iloc[0] == 0.0


def test_np_chart_all_max():
    """Test np-chart with all defectives at sample size."""
    defectives = [50, 50, 50]
    df = calc_np(data=defectives, sample_size=50, run_tests=False)

    assert len(df) == 3
    # All values should be 50
    assert (df['value'] == 50.0).all()


def test_attribute_chart_custom_labels():
    """Test attribute charts with custom labels."""
    defects = [5, 3, 7]
    labels = ['Day 1', 'Day 2', 'Day 3']
    df = calc_c(defects, label=labels)

    assert df['label'].iloc[0] == 'Day 1'
    assert df['label'].iloc[1] == 'Day 2'
    assert df['label'].iloc[2] == 'Day 3'


def test_p_chart_with_phase_labels():
    """Test p-chart with phase labels parameter."""
    defectives = [5, 3, 7, 10, 12, 11]
    phase_labels = ['before', 'before', 'before', 'after', 'after', 'after']
    df = calc_p(data=defectives, sample_size=100, phase=phase_labels, run_tests=False)

    # Check phase column
    assert 'phase' in df.columns
    unique_phases = df['phase'].unique()
    assert len(unique_phases) == 2
    assert 'before' in unique_phases
    assert 'after' in unique_phases

    # Check phase boundaries
    assert (df['phase'].iloc[0:3] == 'before').all()
    assert (df['phase'].iloc[3:6] == 'after').all()


def test_np_chart_with_phase_labels():
    """Test np-chart with phase labels parameter."""
    defectives = [5, 3, 7, 4, 6, 8]
    phase_labels = ['baseline', 'baseline', 'baseline', 'test', 'test', 'test']
    df = calc_np(data=defectives, sample_size=100, phase=phase_labels, run_tests=False)

    unique_phases = df['phase'].unique()
    assert len(unique_phases) == 2
    assert 'baseline' in unique_phases
    assert 'test' in unique_phases


def test_c_chart_with_phase_labels():
    """Test c-chart with phase labels parameter."""
    defects = [3, 4, 3, 10, 11, 12]
    phase_labels = ['pre', 'pre', 'pre', 'post', 'post', 'post']
    df = calc_c(defects, phase=phase_labels, run_tests=False)

    unique_phases = df['phase'].unique()
    assert len(unique_phases) == 2
    assert 'pre' in unique_phases
    assert 'post' in unique_phases

    # Verify different control limits for different phases
    pre_cl = df[df['phase'] == 'pre']['center_line'].iloc[0]
    post_cl = df[df['phase'] == 'post']['center_line'].iloc[0]
    assert pre_cl == pytest.approx(10 / 3)
    assert post_cl == pytest.approx(11.0)


def test_u_chart_with_phase_labels():
    """Test u-chart with phase labels parameter."""
    defects = [10, 8, 12, 6]
    areas = [10, 8, 12, 10]
    phase_labels = ['phase1', 'phase1', 'phase2', 'phase2']
    df = calc_u(data=defects, area=areas, phase=phase_labels, run_tests=False)

    unique_phases = df['phase'].unique()
    assert len(unique_phases) == 2
    assert 'phase1' in unique_phases
    assert 'phase2' in unique_phases


def test_phases_length_validation():
    """Test that all charts validate phases length."""
    defects = [3, 4, 5, 6]

    # Too short
    with pytest.raises(ValueError, match='length'):
        calc_c(defects, phase=['a', 'b'])

    # Too long
    with pytest.raises(ValueError, match='length'):
        calc_c(defects, phase=['a', 'b', 'c', 'd', 'e'])


def test_phases_empty_validation():
    """Test that empty phases list raises error."""
    defects = [3, 4, 5]
    with pytest.raises(ValueError):
        calc_c(defects, phase=[])
