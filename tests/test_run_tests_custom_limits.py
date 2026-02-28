"""
Tests for run_tests_with_custom_limits and CustomLimits.
"""

import math

import pandas as pd

from pycontrolcharts import (
    CustomLimits,
    RunTestConfig,
    RunType,
    run_tests_with_custom_limits,
)


def test_run_tests_with_custom_limits_basic():
    """List data + CustomLimits; point beyond UCL yields OVER_UCL violation."""
    limits = CustomLimits(center_line=10.0, ucl=12.0, lcl=8.0)
    data = [9.0, 11.0, 13.0, 10.0]  # 13 > UCL
    df = run_tests_with_custom_limits(data, limits=limits)
    assert len(df) == 4
    assert list(df.columns) == [
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
    # Point at index 2 (value 13) should have OVER_UCL
    violations_2 = df.iloc[2]['violations']
    assert any(v['type'] == RunType.OVER_UCL for v in violations_2)


def test_run_tests_with_custom_limits_no_sigma():
    """Only center_line/ucl/lcl; sigma columns NaN, test5/test6 not performed."""
    limits = CustomLimits(center_line=10.0, ucl=15.0, lcl=5.0)
    data = [10.0, 11.0, 12.0, 13.0, 14.0]  # 5 above center, could trigger test2
    df = run_tests_with_custom_limits(data, limits=limits)
    assert math.isnan(df['sigma_1_upper'].iloc[0])
    assert math.isnan(df['sigma_2_upper'].iloc[0])
    # No point beyond 2σ/1σ so no test5/test6 violations; test2 might fire
    # (9 consecutive above center needs 9 points). So we just check sigma is nan.
    assert df['center_line'].iloc[0] == 10.0
    assert df['ucl'].iloc[0] == 15.0
    assert df['lcl'].iloc[0] == 5.0


def test_run_tests_with_custom_limits_with_sigma():
    """Explicit sigma provided; test5/test6 can be performed."""
    limits = CustomLimits(
        center_line=10.0,
        ucl=13.0,
        lcl=7.0,
        sigma_1_upper=11.0,
        sigma_1_lower=9.0,
        sigma_2_upper=12.0,
        sigma_2_lower=8.0,
    )
    # 3 points: 10, 12.5, 12.5 -> 2 of 3 beyond +2σ (12) -> test5
    data = [10.0, 12.5, 12.5]
    df = run_tests_with_custom_limits(data, limits=limits)
    assert df['sigma_2_upper'].iloc[0] == 12.0
    violations_last = df.iloc[2]['violations']
    assert any(v['type'] == RunType.X_OVER_2SIGMA for v in violations_last)


def test_run_tests_test6_requires_four_of_five_outside_not_three():
    """Test 6 (4 of 5 beyond 1σ) must not fire when only 3 of 5 are outside.

    Bug: the state machine allowed alternating outside/inside (up, skip, up, skip, up),
    so 3 points beyond 1σ and 2 between CL and 1σ were incorrectly reported as a
    test 6 violation. Test 6 requires at least 4 of 5 points beyond 1σ (one inside allowed).
    """
    limits = CustomLimits(
        center_line=10.0,
        ucl=13.0,
        lcl=7.0,
        sigma_1_upper=11.0,
        sigma_1_lower=9.0,
        sigma_2_upper=12.0,
        sigma_2_lower=8.0,
    )
    # Pattern: outside +1σ, inside (CL..+1σ), outside, inside, outside
    # Values: 11.5 > 11 (outside), 10.5 in (10,11) (inside), 11.5, 10.5, 11.5
    # So 3 of 5 beyond +1σ — must NOT trigger test 6 (4 of 5 required).
    data = [11.5, 10.5, 11.5, 10.5, 11.5]
    config = RunTestConfig(
        test1=False, test2=False, test3=False, test5=False, test6=True
    )
    df = run_tests_with_custom_limits(data, limits=limits, run_tests=config)
    assert len(df) == 5
    for i in range(5):
        violations = df.iloc[i]['violations']
        assert not any(v['type'] == RunType.X_OVER_1SIGMA for v in violations), (
            f'Point {i} should not have X_OVER_1SIGMA: only 3 of 5 are beyond +1σ'
        )


def test_run_tests_with_custom_limits_run_tests_disabled():
    """RunTestConfig with all tests False yields no violations."""
    limits = CustomLimits(center_line=10.0, ucl=12.0, lcl=8.0)
    data = [9.0, 20.0, 10.0]  # 20 beyond UCL
    config = RunTestConfig(
        test1=False, test2=False, test3=False, test5=False, test6=False
    )
    df = run_tests_with_custom_limits(data, limits=limits, run_tests=config)
    assert all(df['violations'].apply(len) == 0)


def test_run_tests_with_custom_limits_spec_on_limits():
    """spec_upper/spec_lower on limits appear in output."""
    limits = CustomLimits(
        center_line=10.0,
        ucl=15.0,
        lcl=5.0,
        spec_upper=18.0,
        spec_lower=2.0,
    )
    data = [10.0, 11.0]
    df = run_tests_with_custom_limits(data, limits=limits)
    assert df['spec_upper'].iloc[0] == 18.0
    assert df['spec_lower'].iloc[0] == 2.0


def test_run_tests_with_custom_limits_variation():
    """Limits with variation_ucl/cl/lcl set yield variation columns."""
    limits = CustomLimits(
        center_line=10.0,
        ucl=14.0,
        lcl=6.0,
        variation_ucl=5.0,
        variation_cl=2.0,
        variation_lcl=0.0,
    )
    data = [10.0, 12.0, 11.0, 13.0]
    df = run_tests_with_custom_limits(data, limits=limits)
    assert 'variation' in df.columns
    assert 'variation_ucl' in df.columns
    assert 'variation_violations' in df.columns
    assert pd.isna(df['variation'].iloc[0])  # first point has no MR
    assert df['variation_ucl'].iloc[0] == 5.0
    assert df['variation_cl'].iloc[0] == 2.0
    assert df['variation_lcl'].iloc[0] == 0.0


def test_run_tests_with_custom_limits_dict_limits():
    """limits can be a dict with center_line, ucl, lcl."""
    limits = {'center_line': 10.0, 'ucl': 12.0, 'lcl': 8.0}
    data = [9.0, 13.0, 10.0]
    df = run_tests_with_custom_limits(data, limits=limits)
    assert len(df) == 3
    assert df['ucl'].iloc[0] == 12.0
    violations_1 = df.iloc[1]['violations']
    assert any(v['type'] == RunType.OVER_UCL for v in violations_1)


def test_run_tests_with_custom_limits_empty_data():
    """Empty list returns empty DataFrame with same column schema."""
    limits = CustomLimits(center_line=10.0, ucl=15.0, lcl=5.0)
    df = run_tests_with_custom_limits([], limits=limits)
    assert len(df) == 0
    assert 'point_id' in df.columns
    assert 'value' in df.columns
    assert 'violations' in df.columns
    assert 'variation' not in df.columns


def test_run_tests_with_custom_limits_empty_data_with_variation_limits():
    """Empty data with variation limits set returns empty DataFrame with variation columns."""
    limits = CustomLimits(
        center_line=10.0,
        ucl=15.0,
        lcl=5.0,
        variation_ucl=5.0,
        variation_cl=2.0,
        variation_lcl=0.0,
    )
    df = run_tests_with_custom_limits([], limits=limits)
    assert len(df) == 0
    assert 'variation' in df.columns
    assert 'variation_violations' in df.columns


def test_run_tests_with_custom_limits_dataframe():
    """DataFrame with value_column and label."""
    limits = CustomLimits(center_line=10.0, ucl=12.0, lcl=8.0)
    data = pd.DataFrame({'x': [9.0, 11.0, 10.0], 't': ['A', 'B', 'C']})
    df = run_tests_with_custom_limits(data, limits=limits, value_column='x', label='t')
    assert list(df['label']) == ['A', 'B', 'C']
    assert list(df['value']) == [9.0, 11.0, 10.0]
