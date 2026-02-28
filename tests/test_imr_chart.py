"""
Unit tests for XmR (Individuals and Moving Range) chart.

These tests use validated examples from Don Wheeler's
"Understanding Statistical Process Control" to verify correctness.
"""

import pytest
import math
import pandas as pd
from pycontrolcharts import calc_xmr, RunTestConfig
from pycontrolcharts.models import RunType
from pandas.testing import assert_frame_equal


def test_calc_xmr_datapoints():
    """Test that datapoints are created correctly."""
    values = [39, 41, 41, 41, 43, 44]
    df = calc_xmr(values)

    # Should have one row per value
    assert len(df) == 6

    # Verify first point structure
    assert df.iloc[0]['point_id'] == 0
    assert df.iloc[0]['value'] == 39
    assert df.iloc[0]['label'] == 1  # Auto-generated 1-based label
    assert len(df.iloc[0]['violations']) == 0


def test_calc_xmr_variation_points():
    """Test that moving range points are calculated correctly."""
    values = [10, 12, 11, 13, 10]
    df = calc_xmr(values)

    # Verify moving ranges
    # MR[0] = NaN (first point)
    # MR[1] = |12 - 10| = 2
    # MR[2] = |11 - 12| = 1
    # MR[3] = |13 - 11| = 2
    # MR[4] = |10 - 13| = 3
    assert pd.isna(df['variation'].iloc[0])
    assert df['variation'].iloc[1] == 2.0
    assert df['variation'].iloc[2] == 1.0
    assert df['variation'].iloc[3] == 2.0
    assert df['variation'].iloc[4] == 3.0


def test_calc_xmr_with_labels():
    """Test XmR chart with custom x-axis labels."""
    values = [39, 41, 41, 41, 43, 44]
    labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

    df = calc_xmr(values, label=labels)

    # Verify labels are used
    assert df['label'].tolist() == labels


def test_calc_xmr_with_phases():
    """Test XmR chart with multiple phases."""
    values = list(range(20))
    phases = ['A'] * 10 + ['B'] * 10

    df = calc_xmr(values, phase=phases)

    # Verify phases
    assert df['phase'].tolist() == phases

    # Verify control limits differ between phases
    phase_a_cl = df[df['phase'] == 'A']['center_line'].iloc[0]
    phase_b_cl = df[df['phase'] == 'B']['center_line'].iloc[0]
    assert phase_a_cl != phase_b_cl


def test_calc_xmr_same_data_same_limits_regardless_of_phase():
    """Same data yields same control limits whether in phase 1 or phase 2 (no cross-boundary MR)."""
    block = [10.0, 12.0, 11.0, 13.0, 11.5, 12.5, 10.5, 13.5, 11.0, 12.0]
    df_single = calc_xmr(block)
    dummy = [1.0] * 5  # dummy first phase
    phases = ['A'] * 5 + ['B'] * 10
    df_multi = calc_xmr(dummy + block, phase=phases)
    phase_b = df_multi[df_multi['phase'] == 'B']
    assert len(phase_b) == len(block)
    assert df_single['center_line'].iloc[0] == pytest.approx(
        phase_b['center_line'].iloc[0], rel=1e-9
    )
    assert df_single['ucl'].iloc[0] == pytest.approx(phase_b['ucl'].iloc[0], rel=1e-9)
    assert df_single['lcl'].iloc[0] == pytest.approx(phase_b['lcl'].iloc[0], rel=1e-9)
    assert df_single['variation_cl'].iloc[0] == pytest.approx(
        phase_b['variation_cl'].iloc[0], rel=1e-9
    )
    assert df_single['variation_ucl'].iloc[0] == pytest.approx(
        phase_b['variation_ucl'].iloc[0], rel=1e-9
    )
    # First point of each phase has no within-phase MR -> nan
    assert pd.isna(df_multi['variation'].iloc[0])
    assert pd.isna(df_multi['variation'].iloc[5])


def test_calc_xmr_from_dataframe():
    """Test XmR chart with pandas DataFrame input."""
    input_df = pd.DataFrame(
        {
            'measurement': [39, 41, 41, 41, 43, 44],
            'date': pd.date_range('2026-01-01', periods=6),
        }
    )

    df = calc_xmr(input_df, value_column='measurement', label='date')

    # Verify it works
    assert len(df) == 6
    assert df['value'].tolist() == input_df['measurement'].tolist()
    assert df['point_id'].tolist() == [0, 1, 2, 3, 4, 5]
    assert df['ucl'].iloc[0] == pytest.approx(44.159574, rel=0.0001)
    assert df['sigma_2_upper'].iloc[0] == pytest.approx(43.27305, rel=0.0001)
    assert df['sigma_1_upper'].iloc[0] == pytest.approx(42.386525, rel=0.0001)
    assert df['lcl'].iloc[0] == pytest.approx(38.840426, rel=0.0001)
    assert math.isnan(df['variation'].iloc[0])
    assert df['variation'].iloc[1] == pytest.approx(2)
    assert df['variation_ucl'].iloc[1] == pytest.approx(3.268, rel=0.0001)
    assert df['variation_cl'].iloc[1] == pytest.approx(1.0, rel=0.0001)
    assert df['variation_lcl'].iloc[1] == pytest.approx(0, rel=0.0001)


def test_xmr_with_spec_limits():
    """Test XmR chart with specification limits."""
    df = calc_xmr([39, 41, 41, 41, 43, 44], spec_upper=50.0, spec_lower=30.0)

    # Verify spec limits
    assert df['spec_upper'].iloc[0] == 50.0
    assert df['spec_lower'].iloc[0] == 30.0


def test_xmr_run_tests_disabled():
    """Test XmR chart with run tests disabled."""
    df = calc_xmr([39, 41, 41, 70, 43, 44], run_tests=False)

    # Verify no violations
    assert all(len(v) == 0 for v in df['violations'])


def test_xmr_detects_outlier():
    """Test XmR chart detects outliers."""
    # Add outlier at position 9 (value 65)
    values = [39, 41, 41, 41, 43, 44, 41, 42, 40, 65, 44, 40]
    df = calc_xmr(values, run_tests=True)

    # Point at index 9 (value 65) is beyond UCL and must have OVER_UCL violation
    outlier_row = df.iloc[9]
    assert outlier_row['value'] == 65.0
    violation_types = {v['type'] for v in outlier_row['violations']}
    assert RunType.OVER_UCL in violation_types, (
        'Outlier at point 10 (value 65) should have OVER_UCL violation'
    )

    # Verify violation structure on that point
    assert len(outlier_row['violations']) > 0
    first_violation = outlier_row['violations'][0]
    assert 'type' in first_violation
    assert 'description' in first_violation
    assert isinstance(first_violation['type'], int)
    assert isinstance(first_violation['description'], str)


def test_xmr_run_tests_do_not_span_phases():
    """Run tests are evaluated per phase; no cross-phase sliding window."""
    # Phase A: 6 points with 5 above A's center (one low to pull mean down).
    # Phase B: 4 points all above B's center.
    # Last 9 points = 5 from A + 4 from B. With global logic they could be
    # "9 above center" (using B's center); per-phase we have only 5 and 4.
    values = [0, 13, 13, 13, 13, 13] + [11, 11, 11, 11]
    phases = ['A'] * 6 + ['B'] * 4
    config = RunTestConfig(
        test1=False, test3=False, test5=False, test6=False, test2_n=9
    )
    df = calc_xmr(values, phase=phases, run_tests=config)
    # No point should have "9 consecutive above center" (X_OVER_AVG)
    for i, row in df.iterrows():
        for v in row['violations']:
            assert v['type'] != RunType.X_OVER_AVG, (
                f'Point {i} should not have X_OVER_AVG when run tests are per phase'
            )


def test_xmr_run_tests_violation_within_single_phase():
    """A run of 9 on one side of center in one phase triggers violation only in that phase."""
    # One phase with 9 consecutive points above center; another phase with no such run.
    # Phase A: 9 points at 12, one at 10 -> mean 11.8, all 9 at 12 are above -> violation at 9th.
    values = [10, 12, 12, 12, 12, 12, 12, 12, 12, 12] + [5, 5, 5]
    phases = ['A'] * 10 + ['B'] * 3
    config = RunTestConfig(
        test1=False, test3=False, test5=False, test6=False, test2_n=9
    )
    df = calc_xmr(values, phase=phases, run_tests=config)
    phase_a = df[df['phase'] == 'A']
    phase_b = df[df['phase'] == 'B']
    # In phase A, the 9th point (index 8 in 0-based, row 8) ends a run of 9 above center -> violation
    violations_a = phase_a['violations']
    has_over_avg_a = any(
        v['type'] == RunType.X_OVER_AVG
        for row_v in violations_a
        for v in (row_v if isinstance(row_v, list) else [row_v])
    )
    assert has_over_avg_a, 'Phase A should have X_OVER_AVG (9 consecutive above center)'
    # Phase B has only 3 points -> no run of 9
    violations_b = phase_b['violations']
    has_over_avg_b = any(
        v['type'] == RunType.X_OVER_AVG
        for row_v in violations_b
        for v in (row_v if isinstance(row_v, list) else [row_v])
    )
    assert not has_over_avg_b, 'Phase B should not have X_OVER_AVG'


def test_calc_xmr_api_list_vs_dataframe():
    """Test that the API works with both list and DataFrame input."""
    values = [39, 41, 41, 41, 43, 44]
    df = pd.DataFrame({'value': values})

    from_df = calc_xmr(df, value_column='value')
    from_list = calc_xmr(values)

    assert_frame_equal(from_df, from_list)


def test_calc_xmr_api_list_vs_series():
    """Test that the API works with both list and Series input."""
    from pandas.testing import assert_frame_equal

    values = [39, 41, 41, 41, 43, 44]
    series = pd.Series(values)
    labels = list(range(1, len(values) + 1))

    from_series = calc_xmr(series, label=labels)
    from_list = calc_xmr(values, label=labels)

    assert_frame_equal(from_series, from_list)


def test_xmr_dataframe_columns():
    """Test that all required columns are present."""
    df = calc_xmr([39, 41, 41, 41, 43, 44])

    required_columns = [
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
        'variation',
        'variation_ucl',
        'variation_cl',
        'variation_lcl',
        'variation_violations',
    ]

    for col in required_columns:
        assert col in df.columns, f'Missing column: {col}'


def test_calc_xmr_with_USPC_p49():
    """From Don Wheeler: Understanding Statistical Process Control p.49"""
    values = [39, 41, 41, 41, 43, 44, 41, 42, 40, 41, 44, 40]
    df = calc_xmr(values)

    # Verify it returns a DataFrame
    assert isinstance(df, pd.DataFrame)

    # Verify control limits match Wheeler's calculations
    assert df['center_line'].iloc[0] == pytest.approx(41.42, rel=0.0001)
    assert df['ucl'].iloc[0] == pytest.approx(46.01, rel=0.0001)
    assert df['lcl'].iloc[0] == pytest.approx(36.82, rel=0.0001)


def test_calc_xmr_with_USPC_p215():
    """From Don Wheeler: Understanding Statistical Process Control p.215"""
    values = [
        905, 930, 865, 895, 905, 885, 890, 930, 915, 910,
        920, 915, 925, 860, 905, 925, 925, 905, 915, 930,
        890, 940, 860, 875, 985, 970, 940, 975, 1000, 1035,
        1020, 985, 960, 945, 965, 940, 900, 920, 980, 950,
        955, 970, 970, 1035, 1040,
    ]  # fmt: skip
    df = calc_xmr(values)

    # Verify control limits match Wheeler's calculations
    assert df['center_line'].iloc[0] == pytest.approx(936.89, rel=0.0001)
    assert df['ucl'].iloc[0] == pytest.approx(1010.93, rel=0.0001)
    assert df['lcl'].iloc[0] == pytest.approx(862.84, rel=0.0001)

    assert df['variation_ucl'].iloc[0] == pytest.approx(90.98, rel=0.0001)
    assert df['variation_cl'].iloc[0] == pytest.approx(27.84, rel=0.0001)


def test_calc_xmr_with_USPC_p215_run_tests():
    """USPC p215: each point has exactly the listed run-test violations and no others (one-based).

    The repetition of separate asserts per data point is intentional: each point's
    expected violation set is asserted explicitly so that any single point's
    regression is visible. Do not refactor into a loop or shared data structure.
    """
    values = [
        905, 930, 865, 895, 905, 885, 890, 930, 915, 910,
        920, 915, 925, 860, 905, 925, 925, 905, 915, 930,
        890, 940, 860, 875, 985, 970, 940, 975, 1000, 1035,
        1020, 985, 960, 945, 965, 940, 900, 920, 980, 950,
        955, 970, 970, 1035, 1040,
    ]  # fmt: skip
    df = calc_xmr(values)

    assert {v['type'] for v in df.iloc[0]['violations']} == {
        RunType.X_UNDER_AVG,
        RunType.X_UNDER_1SIGMA,
    }  # point 1
    assert {v['type'] for v in df.iloc[1]['violations']} == {
        RunType.X_UNDER_AVG,
        RunType.X_UNDER_1SIGMA,
    }  # point 2
    assert {v['type'] for v in df.iloc[2]['violations']} == {
        RunType.X_UNDER_AVG,
        RunType.X_UNDER_1SIGMA,
    }  # point 3
    assert {v['type'] for v in df.iloc[3]['violations']} == {
        RunType.X_UNDER_AVG,
        RunType.X_UNDER_1SIGMA,
    }  # point 4
    assert {v['type'] for v in df.iloc[4]['violations']} == {
        RunType.X_UNDER_AVG,
        RunType.X_UNDER_1SIGMA,
    }  # point 5
    assert {v['type'] for v in df.iloc[5]['violations']} == {
        RunType.X_UNDER_AVG,
        RunType.X_UNDER_1SIGMA,
    }  # point 6
    assert {v['type'] for v in df.iloc[6]['violations']} == {
        RunType.X_UNDER_AVG,
        RunType.X_UNDER_1SIGMA,
    }  # point 7
    assert {v['type'] for v in df.iloc[7]['violations']} == {
        RunType.X_UNDER_AVG
    }  # point 8
    assert {v['type'] for v in df.iloc[8]['violations']} == {
        RunType.X_UNDER_AVG
    }  # point 9
    assert {v['type'] for v in df.iloc[9]['violations']} == {
        RunType.X_UNDER_AVG
    }  # point 10
    assert {v['type'] for v in df.iloc[10]['violations']} == {
        RunType.X_UNDER_AVG
    }  # point 11
    assert {v['type'] for v in df.iloc[11]['violations']} == {
        RunType.X_UNDER_AVG
    }  # point 12
    assert {v['type'] for v in df.iloc[12]['violations']} == {
        RunType.X_UNDER_AVG
    }  # point 13
    assert {v['type'] for v in df.iloc[13]['violations']} == {
        RunType.X_UNDER_AVG,
        RunType.UNDER_LCL,
    }  # point 14
    assert {v['type'] for v in df.iloc[14]['violations']} == {
        RunType.X_UNDER_AVG
    }  # point 15
    assert {v['type'] for v in df.iloc[15]['violations']} == {
        RunType.X_UNDER_AVG
    }  # point 16
    assert {v['type'] for v in df.iloc[16]['violations']} == {
        RunType.X_UNDER_AVG
    }  # point 17
    assert {v['type'] for v in df.iloc[17]['violations']} == {
        RunType.X_UNDER_AVG
    }  # point 18
    assert {v['type'] for v in df.iloc[18]['violations']} == {
        RunType.X_UNDER_AVG
    }  # point 19
    assert {v['type'] for v in df.iloc[19]['violations']} == {
        RunType.X_UNDER_AVG
    }  # point 20
    assert {v['type'] for v in df.iloc[20]['violations']} == {
        RunType.X_UNDER_AVG
    }  # point 21
    assert {v['type'] for v in df.iloc[21]['violations']} == set()  # point 22
    assert {v['type'] for v in df.iloc[22]['violations']} == {
        RunType.UNDER_LCL,
        RunType.X_UNDER_2SIGMA,
    }  # point 23
    assert {v['type'] for v in df.iloc[23]['violations']} == {
        RunType.X_UNDER_2SIGMA,
    }  # point 24
    assert {v['type'] for v in df.iloc[24]['violations']} == {
        RunType.X_OVER_AVG,
        RunType.X_OVER_1SIGMA,
    }  # point 25
    assert {v['type'] for v in df.iloc[25]['violations']} == {
        RunType.X_OVER_AVG,
        RunType.X_OVER_1SIGMA,
    }  # point 26
    assert {v['type'] for v in df.iloc[26]['violations']} == {
        RunType.X_OVER_AVG,
        RunType.X_OVER_1SIGMA,
    }  # point 27
    assert {v['type'] for v in df.iloc[27]['violations']} == {
        RunType.X_OVER_AVG,
        RunType.X_OVER_1SIGMA,
    }  # point 28
    assert {v['type'] for v in df.iloc[28]['violations']} == {
        RunType.X_OVER_AVG,
        RunType.X_OVER_1SIGMA,
        RunType.X_OVER_2SIGMA,
    }  # point 29
    assert {v['type'] for v in df.iloc[29]['violations']} == {
        RunType.X_OVER_AVG,
        RunType.X_OVER_1SIGMA,
        RunType.X_OVER_2SIGMA,
        RunType.OVER_UCL,
    }  # point 30
    assert {v['type'] for v in df.iloc[30]['violations']} == {
        RunType.X_OVER_AVG,
        RunType.X_OVER_1SIGMA,
        RunType.X_OVER_2SIGMA,
        RunType.OVER_UCL,
    }  # point 31
    assert {v['type'] for v in df.iloc[31]['violations']} == {
        RunType.X_OVER_AVG,
        RunType.X_OVER_1SIGMA,
    }  # point 32
    assert {v['type'] for v in df.iloc[32]['violations']} == {
        RunType.X_OVER_AVG,
    }  # point 33
    assert {v['type'] for v in df.iloc[33]['violations']} == {
        RunType.X_OVER_AVG
    }  # point 34
    assert {v['type'] for v in df.iloc[34]['violations']} == {
        RunType.X_OVER_AVG
    }  # point 35
    assert {v['type'] for v in df.iloc[35]['violations']} == {
        RunType.X_OVER_AVG
    }  # point 36
    assert {v['type'] for v in df.iloc[36]['violations']} == set()  # point 37
    assert {v['type'] for v in df.iloc[37]['violations']} == set()  # point 38
    assert {v['type'] for v in df.iloc[38]['violations']} == set()  # point 39
    assert {v['type'] for v in df.iloc[39]['violations']} == set()  # point 40
    assert {v['type'] for v in df.iloc[40]['violations']} == set()  # point 41
    assert {v['type'] for v in df.iloc[41]['violations']} == {
        RunType.X_OVER_1SIGMA,
    }  # point 42
    assert {v['type'] for v in df.iloc[42]['violations']} == {
        RunType.X_OVER_1SIGMA,
    }  # point 43
    assert {v['type'] for v in df.iloc[43]['violations']} == {
        RunType.X_OVER_1SIGMA,
        RunType.X_OVER_2SIGMA,
        RunType.OVER_UCL,
    }  # point 44
    assert {v['type'] for v in df.iloc[44]['violations']} == {
        RunType.X_OVER_1SIGMA,
        RunType.X_OVER_2SIGMA,
        RunType.OVER_UCL,
    }  # point 45


def test_calc_xmr_with_GTDA_p134():
    data = {
        'Treatment': [
            'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
            'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B',
            'C', 'C', 'C', 'C', 'C', 'C', 'C', 'C', 'C', 'C',
            'D', 'D', 'D', 'D', 'D', 'D', 'D', 'D', 'D', 'D',
        ],
        'Value': [
            9, 14, 9, 12, 10, 11, 7, 9, 12, 13,
            14, 11, 10, 14, 12, 11, 11, 10, 13, 9,
            14, 17, 17, 13, 13, 12, 14, 16, 15, 18,
            12, 14, 17, 12, 11, 13, 15, 16, 14, 13,
        ],
    }  # fmt: skip
    chart = calc_xmr(pd.DataFrame(data), value_column='Value', phase='Treatment')

    phase_a = chart.query('phase == "A"')
    assert phase_a['ucl'].iloc[0] == pytest.approx(18.283215, rel=0.0001)
    assert phase_a['center_line'].iloc[0] == pytest.approx(10.6, rel=0.0001)
    assert phase_a['lcl'].iloc[0] == pytest.approx(2.916785, rel=0.0001)

    phase_b = chart.query('phase == "B"')
    assert phase_b['ucl'].iloc[0] == pytest.approx(17.114657, rel=0.0001)
    assert phase_b['center_line'].iloc[0] == pytest.approx(11.5, rel=0.0001)
    assert phase_b['lcl'].iloc[0] == pytest.approx(5.885343, rel=0.0001)

    phase_c = chart.query('phase == "C"')
    assert phase_c['ucl'].iloc[0] == pytest.approx(19.628132, rel=0.0001)
    assert phase_c['center_line'].iloc[0] == pytest.approx(14.9, rel=0.0001)
    assert phase_c['lcl'].iloc[0] == pytest.approx(10.171868, rel=0.0001)

    phase_d = chart.query('phase == "D"')
    assert phase_d['ucl'].iloc[0] == pytest.approx(19.314657, rel=0.0001)
    assert phase_d['center_line'].iloc[0] == pytest.approx(13.7, rel=0.0001)
    assert phase_d['lcl'].iloc[0] == pytest.approx(8.085343, rel=0.0001)


def test_calc_xmr_with_USPC_p56():
    data = {
        'Value': [
            4, 5, 5, 4, 8, 4, 3, 7, 0, 2, 1, 5,
            3, 2, 0, 3, 6, 9, 9, 7, 8, 7, 9, 9,
        ],
        'Subgroup': [
            'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I',
            'II', 'II', 'II', 'II', 'II', 'II', 'II', 'II',
            'III', 'III', 'III', 'III', 'III', 'III', 'III', 'III',
        ],
    }  # fmt: skip
    df = calc_xmr(pd.DataFrame(data), value_column='Value', phase='Subgroup')

    assert df['phase'].iloc[0] == 'I'
    assert df['center_line'].iloc[0] == pytest.approx(5.0, rel=0.0001)
    assert df['ucl'].iloc[0] == pytest.approx(10.7, rel=0.0001)
    assert df['lcl'].iloc[0] <= 0
    assert df['variation_ucl'].iloc[0] == pytest.approx(7.0, rel=0.001)
    assert df['variation_cl'].iloc[0] == pytest.approx(2.14, rel=0.01)
    assert df['variation_lcl'].iloc[0] == pytest.approx(0.0, rel=0.0001)

    assert df['phase'].iloc[8] == 'II'
    assert df['center_line'].iloc[8] == pytest.approx(2.0, rel=0.0001)
    assert df['ucl'].iloc[8] == pytest.approx(7.7, rel=0.001)
    assert df['lcl'].iloc[8] <= 0
    assert df['variation_ucl'].iloc[8] == pytest.approx(7.0, rel=0.001)
    assert df['variation_cl'].iloc[8] == pytest.approx(2.14, rel=0.01)
    assert df['variation_lcl'].iloc[8] == pytest.approx(0.0, rel=0.0001)

    assert df['phase'].iloc[16] == 'III'
    assert df['center_line'].iloc[16] == pytest.approx(8, rel=0.0001)
    assert df['ucl'].iloc[16] == pytest.approx(11.42, rel=0.0001)
    assert df['lcl'].iloc[16] == pytest.approx(4.58, rel=0.001)
    assert df['variation_ucl'].iloc[16] == pytest.approx(4.2, rel=0.001)
    assert df['variation_cl'].iloc[16] == pytest.approx(1.29, rel=0.01)
    assert df['variation_lcl'].iloc[16] == pytest.approx(0.0, rel=0.0001)


def test_calc_xmr_with_USPC_p56_p2_only():

    data = [0, 2, 1, 5, 3, 2, 0, 3]

    df = calc_xmr(data)
    assert df['center_line'].iloc[0] == pytest.approx(2.0, rel=0.0001)
    assert df['ucl'].iloc[0] == pytest.approx(7.7, rel=0.001)
    assert df['lcl'].iloc[0] <= 0
    assert df['variation_ucl'].iloc[0] == pytest.approx(7.0, rel=0.001)
    assert df['variation_cl'].iloc[0] == pytest.approx(2.14, rel=0.01)
    assert df['variation_lcl'].iloc[0] == pytest.approx(0.0, rel=0.0001)


def test_calc_xmr_with_USPC_p27():
    data = {
        'ID': list(range(1, 205)),
        'Group': [
            1, 1, 1, 1, 2, 2, 2, 2, 3, 3,
            3, 3, 4, 4, 4, 4, 5, 5, 5, 5,
            6, 6, 6, 6, 7, 7, 7, 7, 8, 8,
            8, 8, 9, 9, 9, 9, 10, 10, 10, 10,
            11, 11, 11, 11, 12, 12, 12, 12, 13, 13,
            13, 13, 14, 14, 14, 14, 15, 15, 15, 15,
            16, 16, 16, 16, 17, 17, 17, 17, 18, 18,
            18, 18, 19, 19, 19, 19, 20, 20, 20, 20,
            21, 21, 21, 21, 22, 22, 22, 22, 23, 23,
            23, 23, 24, 24, 24, 24, 25, 25, 25, 25,
            26, 26, 26, 26, 27, 27, 27, 27, 28, 28,
            28, 28, 29, 29, 29, 29, 30, 30, 30, 30,
            31, 31, 31, 31, 32, 32, 32, 32, 33, 33,
            33, 33, 34, 34, 34, 34, 35, 35, 35, 35,
            36, 36, 36, 36, 37, 37, 37, 37, 38, 38,
            38, 38, 39, 39, 39, 39, 40, 40, 40, 40,
            41, 41, 41, 41, 42, 42, 42, 42, 43, 43,
            43, 43, 44, 44, 44, 44, 45, 45, 45, 45,
            46, 46, 46, 46, 47, 47, 47, 47, 48, 48,
            48, 48, 49, 49, 49, 49, 50, 50, 50, 50,
            51, 51, 51, 51,
        ],
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
    }  # fmt: skip
    df = calc_xmr(pd.DataFrame(data), value_column='Value')

    assert df['center_line'].iloc[0] == pytest.approx(4498.18, rel=0.001)
    assert df['ucl'].iloc[0] == pytest.approx(5346.08, rel=0.001)
    assert df['lcl'].iloc[0] == pytest.approx(3650.27, rel=0.001)
    assert df['variation_ucl'].iloc[0] == pytest.approx(1041.88, rel=0.001)
    assert df['variation_cl'].iloc[0] == pytest.approx(318.81, rel=0.01)
    assert df['variation_lcl'].iloc[0] == pytest.approx(0.0, rel=0.0001)
