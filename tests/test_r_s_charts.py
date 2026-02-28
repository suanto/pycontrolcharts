"""
Unit tests for X-bar/R and X-bar/S chart calculations with new DataFrame API.

These tests verify that X-bar/R and X-bar/S charts compute correctly,
including rational subgroup processing and control limit calculations.
"""

import pytest
import pandas as pd
from pycontrolcharts import calc_xbar_r, calc_xbar_s


def _uspc_p27_data():
    """USPC p27 dataset (204 points, 51 groups of 4). Returns a fresh DataFrame."""
    return pd.DataFrame(
        {
            'ID': list(range(1, 205)),
            'Group': [g for g in range(1, 52) for _ in range(4)],
            'Value': [
                5045, 4350, 4350, 3975, 4290, 4430, 4485, 4285, 3980, 3925,
                3645, 3760, 3300, 3685, 3463, 5200, 5100, 4635, 5100, 5450,
                4635, 4720, 4810, 4565, 4410, 4065, 4565, 5190, 4725, 4640,
                4640, 4895, 4790, 4845, 4700, 4600, 4110, 4410, 4180, 4790,
                4790, 4340, 4895, 5750, 4740, 5000, 4895, 4255, 4170, 3850,
                4445, 4650, 4170, 4255, 4170, 4375, 4175, 4550, 4450, 2855,
                2920, 4375, 4375, 4355, 4090, 5000, 4335, 5000, 4640, 4335,
                5000, 4615, 4215, 4275, 4275, 5000, 4615, 4735, 4215, 4700,
                4700, 4700, 4700, 4095, 4095, 3940, 3700, 3650, 4445, 4000,
                4845, 5000, 4560, 4700, 4310, 4310, 5000, 4575, 4700, 4430,
                4850, 4850, 4570, 4570, 4855, 4160, 4325, 4125, 4100, 4340,
                4575, 3875, 4050, 4050, 4685, 4685, 4430, 4300, 4690, 4560,
                3075, 2965, 4080, 4080, 4425, 4300, 4430, 4840, 4840, 4310,
                4185, 4570, 4700, 4440, 4850, 4125, 4450, 4450, 4850, 4450,
                3635, 3635, 3635, 3900, 4340, 4340, 3665, 3775, 5000, 4850,
                4775, 4500, 4770, 4500, 4770, 5150, 4850, 4700, 5000, 5000,
                5000, 4700, 4500, 4840, 5075, 5000, 4770, 4570, 4925, 4775,
                5075, 4925, 5075, 4925, 5250, 4915, 5600, 5075, 4450, 4215,
                4325, 4665, 4615, 4615, 4500, 4765, 4500, 4500, 4850, 4930,
                4700, 4890, 4625, 4425, 4135, 4190, 4080, 3690, 5050, 4625,
                5150, 5250, 5000, 5000,
            ],
        }
    )  # fmt: skip


def test_xbar_r_basic_calc():
    """Test basic X-bar/R chart with simple data."""
    values = [10, 11, 12, 9, 10, 11, 11, 12, 10, 10, 11, 12]
    df = calc_xbar_r(values, subgroup_size=3, run_tests=False)

    assert len(df) == 4
    assert df['center_line'].iloc[0] > 0
    assert df['ucl'].iloc[0] > df['center_line'].iloc[0]
    assert df['lcl'].iloc[0] < df['center_line'].iloc[0]


def test_xbar_r_subgroup_means():
    """Test that rational subgroup means are calculated correctly."""
    values = [10, 12, 14, 20, 22, 24]
    df = calc_xbar_r(values, subgroup_size=3, run_tests=False)

    assert df['value'].iloc[0] == pytest.approx(12.0)
    assert df['value'].iloc[1] == pytest.approx(22.0)


def test_xbar_r_subgroup_ranges():
    """Test that rational subgroup ranges are calculated correctly."""
    values = [10, 12, 14, 20, 22, 24]
    df = calc_xbar_r(values, subgroup_size=3, run_tests=False)

    assert df['variation'].iloc[0] == pytest.approx(4.0)
    assert df['variation'].iloc[1] == pytest.approx(4.0)


def test_xbar_r_wheeler_example():
    """From Don Wheeler: Understanding Statistical Process Control p.56"""
    values = [
        4, 5, 5, 4, 8, 4, 3, 7, 0, 2, 1, 5,
        3, 2, 0, 3, 6, 9, 9, 7, 8, 7, 9, 9,
    ]  # fmt: skip
    df = calc_xbar_r(values, subgroup_size=8, run_tests=False)

    assert len(df) == 3
    assert df['center_line'].iloc[0] == pytest.approx(5.0, abs=0.01)
    assert df['ucl'].iloc[0] == pytest.approx(6.62, abs=0.01)
    assert df['lcl'].iloc[0] == pytest.approx(3.38, abs=0.01)
    assert df['variation_cl'].iloc[0] == pytest.approx(4.33, abs=0.01)
    assert df['variation_ucl'].iloc[0] == pytest.approx(8.08, abs=0.01)
    assert df['variation_lcl'].iloc[0] == pytest.approx(0.59, abs=0.01)


def test_xbar_r_insufficient_data():
    """Test X-bar/R chart with insufficient data for even one rational subgroup."""
    values = [10, 11]
    df = calc_xbar_r(values, subgroup_size=3, run_tests=False)
    assert len(df) == 0


def test_xbar_r_subgroup_size_too_small():
    """Test X-bar/R chart with invalid subgroup size."""
    with pytest.raises(ValueError):
        calc_xbar_r([10, 11, 12, 13, 14], subgroup_size=1, run_tests=False)


def test_xbar_r_dataframe_structure():
    """Test DataFrame has correct structure."""
    values = [10, 11, 12, 9, 10, 11]
    df = calc_xbar_r(values, subgroup_size=3, run_tests=False)

    assert 'point_id' in df.columns
    assert 'value' in df.columns
    assert 'variation' in df.columns
    assert 'center_line' in df.columns
    assert 'ucl' in df.columns
    assert 'variation_ucl' in df.columns


def test_xbar_s_basic_calc():
    """Test basic X-bar/S chart with simple data."""
    values = [10, 11, 12, 9, 10, 11, 11, 12, 10, 10, 11, 12]
    df = calc_xbar_s(values, subgroup_size=3, run_tests=False)

    assert len(df) == 4
    assert df['center_line'].iloc[0] > 0
    assert df['ucl'].iloc[0] > df['center_line'].iloc[0]
    assert df['lcl'].iloc[0] < df['center_line'].iloc[0]


def test_xbar_s_subgroup_means():
    """Test that rational subgroup means are calculated correctly."""
    values = [10, 12, 14, 20, 22, 24]
    df = calc_xbar_s(values, subgroup_size=3, run_tests=False)

    assert df['value'].iloc[0] == pytest.approx(12.0)
    assert df['value'].iloc[1] == pytest.approx(22.0)


def test_xbar_s_subgroup_std_devs():
    """Test that rational subgroup standard deviations are calculated correctly."""
    values = [10, 12, 14, 20, 22, 24]
    df = calc_xbar_s(values, subgroup_size=3, run_tests=False)

    assert df['variation'].iloc[0] == pytest.approx(2.0)
    assert df['variation'].iloc[1] == pytest.approx(2.0)


def test_xbar_s_wheeler_example():
    """From Don Wheeler: Understanding Statistical Process Control p.56"""
    values = [
        4, 5, 5, 4, 8, 4, 3, 7, 0, 2, 1, 5,
        3, 2, 0, 3, 6, 9, 9, 7, 8, 7, 9, 9,
    ]  # fmt: skip
    df = calc_xbar_s(values, subgroup_size=8, run_tests=False)

    assert len(df) == 3
    assert df['center_line'].iloc[0] == pytest.approx(5.0, abs=0.01)
    assert df['ucl'].iloc[0] == pytest.approx(6.68, abs=0.01)
    assert df['lcl'].iloc[0] == pytest.approx(3.32, abs=0.01)
    assert df['variation_cl'].iloc[0] == pytest.approx(1.525, abs=0.01)
    assert df['variation_ucl'].iloc[0] == pytest.approx(2.768, abs=0.01)
    assert df['variation_lcl'].iloc[0] == pytest.approx(0.282, abs=0.01)


def test_xbar_r_vs_xbar_s_limits_differ():
    """Test that X-bar/R and X-bar/S charts have different limits for same data."""
    values = [10, 11, 12, 9, 10, 11, 11, 12, 10, 10, 11, 12]

    r_df = calc_xbar_r(values, subgroup_size=3, run_tests=False)
    s_df = calc_xbar_s(values, subgroup_size=3, run_tests=False)

    assert r_df['variation'].iloc[0] != s_df['variation'].iloc[0]
    assert r_df['variation_cl'].iloc[0] != s_df['variation_cl'].iloc[0]


def test_xbar_r_with_phase_labels():
    """Test X-bar/R chart with phase labels parameter."""
    values = [10, 11, 12, 20, 21, 22, 10, 11, 12, 20, 21, 22]
    phase_labels = [
        'baseline',
        'baseline',
        'baseline',
        'baseline',
        'baseline',
        'baseline',
        'improved',
        'improved',
        'improved',
        'improved',
        'improved',
        'improved',
    ]

    df = calc_xbar_r(values, subgroup_size=3, phase=phase_labels, run_tests=False)

    assert df['phase'].nunique() == 2
    assert 'baseline' in df['phase'].values
    assert 'improved' in df['phase'].values


def test_xbar_r_with_variable_subgroups():
    """Test basic X-bar/R chart with variable subgroup sizes."""
    df = pd.DataFrame(
        {
            'measurement': [
                10,
                11,
                12,
                9,
                10,
                11,
                12,
                10,
                11,
            ],
            'batch': ['A', 'A', 'A', 'B', 'B', 'B', 'B', 'C', 'C'],
        }  # fmt: skip
    )

    result = calc_xbar_r(
        df, value_column='measurement', subgroup='batch', run_tests=False
    )

    assert len(result) == 3
    assert result['value'].iloc[0] == pytest.approx(11.0)
    assert result['value'].iloc[1] == pytest.approx(10.5)
    assert result['value'].iloc[2] == pytest.approx(10.5)
    assert result['variation'].iloc[0] == pytest.approx(2.0)
    assert result['variation'].iloc[1] == pytest.approx(3.0)
    assert result['variation'].iloc[2] == pytest.approx(1.0)
    assert result['ucl'].iloc[0] > result['center_line'].iloc[0]


def test_xbar_s_with_variable_subgroups():
    """Test basic X-bar/S chart with variable subgroup sizes."""
    df = pd.DataFrame(
        {
            'measurement': [
                10,
                11,
                12,
                9,
                10,
                11,
                12,
                10,
                11,
            ],
            'batch': ['A', 'A', 'A', 'B', 'B', 'B', 'B', 'C', 'C'],
        }  # fmt: skip
    )

    result = calc_xbar_s(
        df, value_column='measurement', subgroup='batch', run_tests=False
    )

    assert len(result) == 3
    assert result['value'].iloc[0] == pytest.approx(11.0)
    assert result['value'].iloc[1] == pytest.approx(10.5)
    assert result['value'].iloc[2] == pytest.approx(10.5)
    assert result['variation'].iloc[0] > 0
    assert result['variation'].iloc[1] > 0
    assert result['variation'].iloc[2] > 0


def test_variable_subgroups_with_phases():
    """Test that phases work with variable subgroups."""
    df = pd.DataFrame(
        {
            'measurement': [10, 11, 12, 9, 10, 11, 20, 21],
            'batch': ['A', 'A', 'A', 'B', 'B', 'B', 'C', 'C'],
            'phase': [
                'baseline',
                'baseline',
                'baseline',
                'baseline',
                'baseline',
                'baseline',
                'improved',
                'improved',
            ],
        }  # fmt: skip
    )

    result = calc_xbar_r(
        df,
        value_column='measurement',
        subgroup='batch',
        phase='phase',
        run_tests=False,
    )

    assert len(result) == 3
    assert result['phase'].tolist() == ['baseline', 'baseline', 'improved']
    baseline_cl = result[result['phase'] == 'baseline']['center_line'].iloc[0]
    improved_cl = result[result['phase'] == 'improved']['center_line'].iloc[0]
    assert baseline_cl != improved_cl


def test_variable_subgroups_small_size():
    """Test that subgroups with size < 2 produce NaN for variation."""
    df = pd.DataFrame(
        {
            'measurement': [10, 11, 12, 15],
            'batch': ['A', 'A', 'B', 'C'],
        }  # fmt: skip
    )

    result = calc_xbar_r(
        df, value_column='measurement', subgroup='batch', run_tests=False
    )

    assert len(result) == 3
    assert pd.isna(result['variation'].iloc[2])
    assert result['value'].iloc[2] == 15.0


def test_variable_subgroups_mutual_exclusion():
    """Test error when both subgroup_size and subgroup are provided."""
    df = pd.DataFrame({'measurement': [10, 11, 12], 'batch': ['A', 'A', 'A']})

    with pytest.raises(ValueError, match='Cannot specify both'):
        calc_xbar_r(df, value_column='measurement', subgroup_size=3, subgroup='batch')


def test_variable_subgroups_neither_provided():
    """Test error when neither subgroup_size nor subgroup are provided."""
    df = pd.DataFrame({'measurement': [10, 11, 12], 'batch': ['A', 'A', 'A']})

    with pytest.raises(ValueError, match="Either 'subgroup_size' or 'subgroup'"):
        calc_xbar_r(df, value_column='measurement')


def test_variable_subgroups_labels():
    """Test that first label from each subgroup is used."""
    df = pd.DataFrame(
        {
            'measurement': [10, 11, 12, 9, 10],
            'batch': ['A', 'A', 'A', 'B', 'B'],
            'date': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        }  # fmt: skip
    )

    result = calc_xbar_r(
        df,
        value_column='measurement',
        subgroup='batch',
        label='date',
        run_tests=False,
    )

    assert result['label'].tolist() == ['Mon', 'Thu']


def test_variable_subgroups_average_size():
    """Test that average subgroup size is used for control limits."""
    df = pd.DataFrame(
        {
            'measurement': [
                10,
                11,
                12,
                9,
                10,
                11,
                12,
                13,
            ],
            'batch': ['A', 'A', 'A', 'B', 'B', 'B', 'B', 'B'],
        }  # fmt: skip
    )

    result = calc_xbar_r(
        df, value_column='measurement', subgroup='batch', run_tests=False
    )

    assert result['ucl'].iloc[0] > result['center_line'].iloc[0]
    assert result['lcl'].iloc[0] < result['center_line'].iloc[0]


def test_xbar_s_uspc_p27_data():
    """X-bar S on USPC p27 data (Advanced Topics in Statistical Process Control, p.96)."""
    df = _uspc_p27_data()
    df_s = calc_xbar_s(df, value_column='Value', subgroup='Group', run_tests=False)

    assert df_s['center_line'].iloc[0] == pytest.approx(4498.18, abs=0.01)
    assert df_s['ucl'].iloc[0] == pytest.approx(4990.55, abs=0.01)
    assert df_s['lcl'].iloc[0] == pytest.approx(4005.81, abs=0.01)
    assert df_s['variation_cl'].iloc[0] == pytest.approx(302.44, abs=0.01)
    assert df_s['variation_ucl'].iloc[0] == pytest.approx(685.33, abs=0.01)
    assert df_s['variation_lcl'].iloc[0] == pytest.approx(0, abs=0.01)


def test_xbar_r_uspc_p27_data():
    """X-bar R on USPC p27 data (Advanced Topics in Statistical Process Control, p.88)."""
    df = _uspc_p27_data()
    df_r = calc_xbar_r(df, value_column='Value', subgroup='Group', run_tests=False)

    assert df_r['center_line'].iloc[0] == pytest.approx(4498.18, abs=0.01)
    assert df_r['ucl'].iloc[0] == pytest.approx(4978.32, abs=0.01)
    assert df_r['lcl'].iloc[0] == pytest.approx(4018.04, abs=0.01)
    assert df_r['variation_cl'].iloc[0] == pytest.approx(658.63, abs=0.01)
    assert df_r['variation_ucl'].iloc[0] == pytest.approx(1502.98, abs=0.01)
    assert df_r['variation_lcl'].iloc[0] == pytest.approx(0, abs=0.01)
