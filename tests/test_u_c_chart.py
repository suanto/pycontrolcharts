"""
Unit tests for u-chart and c-chart.

These tests use validated examples from Don Wheeler's
"Understanding Statistical Process Control" (USPC) to verify correctness.
"""

import pandas as pd
import pytest

from pycontrolcharts import calc_c, calc_u, RunType


def test_uchart_with_USPC_p276():
    """USPC p276: u-chart with variable area (NofLeaks / NofRadiators)."""
    data = {
        'Date': [
            '3.6.1948', '4.6.1948', '5.6.1948', '6.6.1948', '7.6.1948',
            '10.6.1948', '11.6.1948', '12.6.1948', '13.6.1948', '14.6.1948',
            '17.6.1948', '18.6.1948', '19.6.1948', '20.6.1948', '24.6.1948',
            '25.6.1948', '26.6.1948', '27.6.1948',
        ],
        'NofLeaks': [
            14, 4, 5, 13, 6, 2, 4, 11, 8, 10,
            3, 11, 1, 3, 6, 8, 5, 2,
        ],
        'NofRadiators': [
            39, 45, 46, 48, 40, 58, 50, 50, 50, 50,
            32, 50, 33, 50, 50, 50, 50, 50,
        ],
        'Rate': [
            0.36, 0.09, 0.11, 0.27, 0.15, 0.03, 0.08, 0.22,
            0.16, 0.2, 0.09, 0.22, 0.03, 0.06, 0.12, 0.16, 0.1, 0.04,
        ],
    }  # fmt: skip

    df = calc_u(
        pd.DataFrame(data),
        value_column='NofLeaks',
        label='Date',
        area_column='NofRadiators',
    )
    assert df['center_line'].iloc[0] == pytest.approx(0.138, abs=0.001)
    assert df['ucl'].iloc[0] == pytest.approx(0.316, abs=0.001)
    assert df['ucl'].iloc[1] == pytest.approx(0.304, abs=0.001)
    assert df['ucl'].iloc[2] == pytest.approx(0.302, abs=0.001)
    assert df['ucl'].iloc[3] == pytest.approx(0.299, abs=0.001)
    assert df['ucl'].iloc[4] == pytest.approx(0.314, abs=0.001)
    assert df['ucl'].iloc[5] == pytest.approx(0.284, abs=0.001)
    assert any(v['type'] == RunType.OVER_UCL for v in df['violations'].iloc[0]), (
        'First point (0.36) should be above UCL (0.316) and have OVER_UCL violation'
    )


def test_uchart_with_USPC_p273():
    """USPC p273: u-chart with constant area (defects per unit)."""
    data = {
        'ID': list(range(1, 41)),
        'Count': [
            2, 4, 1, 1, 4, 5, 2, 1, 2, 4,
            4, 3, 5, 2, 1, 1, 2, 3, 2, 4,
            3, 2, 4, 3, 2, 3, 5, 1, 4, 3,
            4, 2, 3, 6, 4, 0, 1, 2, 3, 1,
        ],
        'Area': [1] * 40,
    }  # fmt: skip

    df = calc_u(
        pd.DataFrame(data),
        value_column='Count',
        label='ID',
        area_column='Area',
    )
    assert len(df) == 40
    assert df['center_line'].iloc[0] == pytest.approx(2.725, abs=0.001)
    assert df['ucl'].iloc[0] == pytest.approx(7.678, abs=0.001)
    assert df['lcl'].iloc[0] == pytest.approx(0.0, abs=0.001)
    assert all(len(df['violations'].iloc[i]) == 0 for i in range(len(df))), (
        'There should be no violations'
    )


def test_cchart_with_USPC_p273():
    """USPC p273: c-chart (same counts as u-chart constant area)."""
    counts = [
        2, 4, 1, 1, 4, 5, 2, 1, 2, 4,
        4, 3, 5, 2, 1, 1, 2, 3, 2, 4,
        3, 2, 4, 3, 2, 3, 5, 1, 4, 3,
        4, 2, 3, 6, 4, 0, 1, 2, 3, 1,
    ]  # fmt: skip
    df = calc_c(counts)
    assert len(df) == 40
    assert df['center_line'].iloc[0] == pytest.approx(2.725, abs=0.001)
    assert df['ucl'].iloc[0] == pytest.approx(7.678, abs=0.001)
    assert df['lcl'].iloc[0] == pytest.approx(0.0, abs=0.001)
    assert all(len(df['violations'].iloc[i]) == 0 for i in range(len(df))), (
        'There should be no violations'
    )


def test_uspc_p220():
    """c-chart with monthly injury counts (24 months); labels from Month column. Data from USPC p220."""
    data = pd.DataFrame(
        {
            'Month': [
                '1-01', '1-02', '1-03', '1-04', '1-05', '1-06',
                '1-07', '1-08', '1-09', '1-10', '1-11', '1-12',
                '2-01', '2-02', '2-03', '2-04', '2-05', '2-06',
                '2-07', '2-08', '2-09', '2-10', '2-11', '2-12',
            ],
            'Number of injuries': [
                6, 2, 4, 8, 5, 4, 23, 7, 3, 5, 12, 7,
                10, 5, 9, 4, 3, 2, 2, 1, 3, 4, 3, 1,
            ],
        }
    )  # fmt: skip

    df = calc_c(data, value_column='Number of injuries', label='Month')

    assert len(df) == 24
    assert df['value'].iloc[0] == 6.0
    assert df['label'].iloc[0] == '1-01'

    assert df['center_line'].iloc[0] == pytest.approx(5.54, abs=0.01)
    assert df['ucl'].iloc[0] == pytest.approx(12.6, abs=0.01)
    assert df['lcl'].iloc[0] == pytest.approx(0.0, abs=0.001)

    assert {v['type'] for v in df.iloc[6]['violations']} == {
        RunType.OVER_UCL
    }  # point 7

    assert {v['type'] for v in df.iloc[15]['violations']} == {
        RunType.X_UNDER_AVG
    }  # point 16

    assert {v['type'] for v in df.iloc[16]['violations']} == {
        RunType.X_UNDER_AVG,
        RunType.X_UNDER_1SIGMA,
    }  # point 17

    assert {v['type'] for v in df.iloc[22]['violations']} == {
        RunType.X_UNDER_AVG,
        RunType.X_UNDER_1SIGMA,
    }  # point 23
