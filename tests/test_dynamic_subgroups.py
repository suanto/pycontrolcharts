"""
Comprehensive tests for dynamic (variable-sized) subgroups in control charts.

This module tests real-world scenarios where subgroup sizes naturally vary,
such as manufacturing batches, shift production, or time-based groupings.
"""

import pytest
import pandas as pd
from pycontrolcharts import calc_xbar_r, calc_xbar_s


def test_manufacturing_batches_varying_sizes():
    """Test production data with varying batch sizes."""
    df = pd.DataFrame(
        {
            'measurement': [
                10.2,
                10.5,
                10.1,
                9.8,
                9.9,
                10.0,
                10.1,
                10.3,
                10.4,
                9.7,
                9.9,
                10.2,
                10.0,
                10.1,
            ],
            'batch_id': [
                'A',
                'A',
                'A',
                'B',
                'B',
                'B',
                'B',
                'C',
                'C',
                'D',
                'D',
                'D',
                'D',
                'D',
            ],
            'date': pd.date_range('2026-01-01', periods=14),
            'operator': ['John'] * 7 + ['Jane'] * 7,
        }
    )

    result = calc_xbar_r(
        df, value_column='measurement', subgroup='batch_id', label='date'
    )

    assert len(result) == 4
    assert not result['value'].isna().any()
    assert not pd.isna(result['variation'].iloc[2])
    assert (result['ucl'] > result['center_line']).all()
    assert (result['lcl'] < result['center_line']).all()


def test_time_based_subgroups_hourly():
    """Test hourly production data where hour sizes vary."""
    timestamps = pd.date_range('2026-01-01 08:00', periods=25, freq='10min')
    df = pd.DataFrame(
        {
            'temperature': [
                98.5,
                98.6,
                98.4,
                98.7,
                98.5,
                98.8,
                98.9,
                98.7,
                98.6,
                98.5,
                98.7,
                98.8,
                98.6,
                98.7,
                98.4,
                98.5,
                98.6,
                98.5,
                98.3,
                98.4,
                98.2,
                98.5,
                98.4,
                98.3,
                98.6,
            ],
            'timestamp': timestamps,
            'hour': [1] * 5 + [2] * 3 + [3] * 6 + [4] * 4 + [5] * 7,
        }
    )

    result = calc_xbar_s(df, value_column='temperature', subgroup='hour')

    assert len(result) == 5
    assert not result['value'].isna().any()
    assert not result['variation'].isna().any()


def test_multi_phase_with_variable_subgroups():
    """Test phase changes with variable subgroup sizes."""
    df = pd.DataFrame(
        {
            'yield_pct': [
                85,
                86,
                87,
                84,
                85,
                86,
                87,
                85,
                90,
                91,
                92,
                93,
                94,
                91,
                93,
                94,
                95,
                92,
                94,
            ],
            'batch': ['B1'] * 3 + ['B2'] * 5 + ['B3'] * 2 + ['B4'] * 4 + ['B5'] * 5,
            'phase': ['baseline'] * 8 + ['improved'] * 11,
        }
    )

    result = calc_xbar_r(df, value_column='yield_pct', subgroup='batch', phase='phase')

    assert len(result) == 5
    assert result['phase'].iloc[0] == 'baseline'
    assert result['phase'].iloc[1] == 'baseline'
    assert result['phase'].iloc[2] == 'improved'
    assert result['phase'].iloc[3] == 'improved'
    assert result['phase'].iloc[4] == 'improved'
    baseline_cl = result[result['phase'] == 'baseline']['center_line'].iloc[0]
    improved_cl = result[result['phase'] == 'improved']['center_line'].iloc[0]
    assert baseline_cl != improved_cl


def test_missing_measurements_in_batches():
    """Test when some measurements are missing (realistic scenario)."""
    df = pd.DataFrame(
        {
            'weight': [100.1, 100.2, 99.8, 99.9, 100.0, 100.1, 100.2],
            'batch': ['1', '1', '2', '2', '2', '2', '3'],
        }
    )

    result = calc_xbar_r(df, value_column='weight', subgroup='batch', run_tests=False)

    assert len(result) == 3
    assert not pd.isna(result['variation'].iloc[0])
    assert pd.isna(result['variation'].iloc[2])
    assert result['value'].iloc[2] == 100.2


def test_all_subgroups_size_one():
    """Test when all subgroups have only one measurement."""
    df = pd.DataFrame({'value': [10, 20, 30, 40], 'batch': ['A', 'B', 'C', 'D']})

    result = calc_xbar_r(df, value_column='value', subgroup='batch', run_tests=False)

    assert len(result) == 4
    assert result['variation'].isna().all()
    assert result['value'].tolist() == [10, 20, 30, 40]


def test_very_mixed_subgroup_sizes():
    """Test extreme variation in subgroup sizes."""
    df = pd.DataFrame(
        {
            'value': [1] * 1 + [2] * 10 + [3] * 2 + [4] * 7 + [5] * 3,
            'batch': ['A'] * 1 + ['B'] * 10 + ['C'] * 2 + ['D'] * 7 + ['E'] * 3,
        }
    )

    result = calc_xbar_s(df, value_column='value', subgroup='batch', run_tests=False)

    assert len(result) == 5
    assert pd.isna(result['variation'].iloc[0])
    assert result['variation'].iloc[1] == 0.0


def test_string_subgroup_identifiers():
    """Test with various string formats for subgroup IDs."""
    df = pd.DataFrame(
        {
            'measurement': [10, 11, 12, 13, 14, 15],
            'batch': [
                'LOT-001',
                'LOT-001',
                'LOT-002',
                'LOT-002',
                'BATCH_A',
                'BATCH_A',
            ],
        }
    )

    result = calc_xbar_r(
        df, value_column='measurement', subgroup='batch', run_tests=False
    )

    assert len(result) == 3


def test_numeric_subgroup_identifiers():
    """Test with numeric subgroup IDs."""
    df = pd.DataFrame(
        {'measurement': [10, 11, 12, 13, 14, 15], 'batch_num': [1, 1, 2, 2, 3, 3]}
    )

    result = calc_xbar_r(
        df, value_column='measurement', subgroup='batch_num', run_tests=False
    )

    assert len(result) == 3


def test_subgroups_maintain_order():
    """Test that subgroup order is preserved (not alphabetically sorted)."""
    df = pd.DataFrame(
        {'value': [1, 2, 3, 4, 5, 6], 'batch': ['Z', 'Z', 'A', 'A', 'M', 'M']}
    )

    result = calc_xbar_r(df, value_column='value', subgroup='batch', run_tests=False)

    assert result['value'].iloc[0] == 1.5
    assert result['value'].iloc[1] == 3.5
    assert result['value'].iloc[2] == 5.5


def test_empty_dataframe():
    """Test with empty DataFrame."""
    df = pd.DataFrame({'value': [], 'batch': []})

    result = calc_xbar_r(df, value_column='value', subgroup='batch', run_tests=False)

    assert len(result) == 0


def test_single_subgroup():
    """Test with only one subgroup."""
    df = pd.DataFrame({'value': [10, 11, 12, 13], 'batch': ['A', 'A', 'A', 'A']})

    result = calc_xbar_r(df, value_column='value', subgroup='batch', run_tests=False)

    assert len(result) == 1
    assert result['value'].iloc[0] == 11.5


def test_custom_labels_from_column():
    """Test using custom labels from a DataFrame column."""
    df = pd.DataFrame(
        {
            'value': [10, 11, 12, 13, 14, 15],
            'batch': ['A', 'A', 'B', 'B', 'C', 'C'],
            'date': pd.date_range('2026-01-01', periods=6),
        }
    )

    result = calc_xbar_r(
        df, value_column='value', subgroup='batch', label='date', run_tests=False
    )

    expected_dates = pd.to_datetime(['2026-01-01', '2026-01-03', '2026-01-05'])
    assert (pd.to_datetime(result['label']) == expected_dates).all()


def test_phase_from_column():
    """Test phase extraction from DataFrame column."""
    df = pd.DataFrame(
        {
            'value': [10, 11, 12, 13, 14, 15],
            'batch': ['A', 'A', 'B', 'B', 'C', 'C'],
            'process': ['old', 'old', 'old', 'old', 'new', 'new'],
        }
    )

    result = calc_xbar_r(
        df, value_column='value', subgroup='batch', phase='process', run_tests=False
    )

    assert result['phase'].tolist() == ['old', 'old', 'new']


def test_phase_change_within_subgroup():
    """Test when phase changes within a subgroup (should use first)."""
    df = pd.DataFrame(
        {
            'value': [10, 11, 12, 13, 14, 15],
            'batch': ['A', 'A', 'B', 'B', 'C', 'C'],
            'phase': [
                'baseline',
                'improved',
                'improved',
                'improved',
                'improved',
                'improved',
            ],
        }
    )

    result = calc_xbar_r(
        df, value_column='value', subgroup='batch', phase='phase', run_tests=False
    )

    assert result['phase'].iloc[0] == 'baseline'


def test_equal_sized_subgroups_match_fixed():
    """Test that variable subgroups with equal sizes match fixed subgroups."""
    data = [10, 11, 12, 9, 10, 11, 11, 12, 10]

    fixed_result = calc_xbar_r(data, subgroup_size=3, run_tests=False)

    df = pd.DataFrame(
        {'value': data, 'batch': ['A', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'C']}
    )
    variable_result = calc_xbar_r(
        df, value_column='value', subgroup='batch', run_tests=False
    )

    assert (fixed_result['value'] == variable_result['value']).all()
    assert (fixed_result['variation'] == variable_result['variation']).all()
    assert fixed_result['center_line'].iloc[0] == pytest.approx(
        variable_result['center_line'].iloc[0]
    )
    assert fixed_result['ucl'].iloc[0] == pytest.approx(variable_result['ucl'].iloc[0])
    assert fixed_result['lcl'].iloc[0] == pytest.approx(variable_result['lcl'].iloc[0])


def test_spec_limits_with_variable_subgroups():
    """Test that specification limits work correctly."""
    df = pd.DataFrame(
        {'value': [10, 11, 12, 9, 10, 11], 'batch': ['A', 'A', 'A', 'B', 'B', 'B']}
    )

    result = calc_xbar_r(
        df,
        value_column='value',
        subgroup='batch',
        spec_upper=15.0,
        spec_lower=5.0,
        run_tests=False,
    )

    assert result['spec_upper'].iloc[0] == 15.0
    assert result['spec_lower'].iloc[0] == 5.0
    assert (result['spec_upper'] == 15.0).all()
    assert (result['spec_lower'] == 5.0).all()


def test_run_tests_enabled_variable_subgroups():
    """Test that run tests work with variable subgroups."""
    df = pd.DataFrame(
        {
            'value': [10, 11, 10, 11, 10, 11, 20, 21, 10, 11],
            'batch': ['A', 'A', 'B', 'B', 'C', 'C', 'D', 'D', 'E', 'E'],
        }
    )

    result = calc_xbar_r(df, value_column='value', subgroup='batch', run_tests=True)

    violations_df = result[result['violations'].apply(len) > 0]
    assert len(violations_df) > 0


def test_run_tests_disabled_variable_subgroups():
    """Test that run tests can be disabled."""
    df = pd.DataFrame(
        {
            'value': [10, 11, 10, 11, 10, 11, 20, 21],
            'batch': ['A', 'A', 'B', 'B', 'C', 'C', 'D', 'D'],
        }
    )

    result = calc_xbar_r(df, value_column='value', subgroup='batch', run_tests=False)

    assert all(len(v) == 0 for v in result['violations'])
