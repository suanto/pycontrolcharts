"""
Unit tests for p-chart and np-chart.

These tests use validated examples from Don Wheeler's
"Understanding Statistical Process Control" (USPC) where applicable.
"""

import pandas as pd
import pytest

from pycontrolcharts import calc_p, calc_np, RunType


def test_p_chart_with_USPC_p264():
    """USPC p264: p-chart (incomplete invoices / invoices per day) reference example."""
    data = {
        'Date': [
            '27.9.2018', '28.9.2018', '29.9.2018', '30.9.2018',
            '1.10.2018', '4.10.2018', '5.10.2018', '6.10.2018',
            '7.10.2018', '8.10.2018', '11.10.2018', '12.10.2018',
            '13.10.2018', '14.10.2018', '15.10.2018', '18.10.2018',
            '19.10.2018', '20.10.2018', '21.10.2018', '22.10.2018',
        ],
        'NofIncompleteInvoices': [
            20, 18, 14, 16, 13, 29, 21, 14, 6, 6,
            7, 7, 9, 5, 8, 9, 9, 10, 9, 10,
        ],
        'NofInvoices': [
            98, 104, 97, 99, 97, 102, 104, 101, 55, 48,
            50, 53, 56, 49, 56, 53, 52, 51, 52, 47,
        ],
    }  # fmt: skip
    df = calc_p(
        pd.DataFrame(data),
        value_column='NofIncompleteInvoices',
        label='Date',
        sample_size_column='NofInvoices',
    )
    assert len(df) == 20
    assert 'center_line' in df.columns
    assert 'ucl' in df.columns
    assert 'lcl' in df.columns
    # CL (center line)
    assert df['center_line'].iloc[0] == pytest.approx(0.169, abs=0.001)
    # UCL/LCL for first 10 points (reference USPC p264)
    ucl_ref = [0.282, 0.279, 0.283, 0.281, 0.283, 0.280, 0.279, 0.280, 0.320, 0.331]
    lcl_ref = [0.055, 0.058, 0.055, 0.056, 0.055, 0.057, 0.058, 0.057, 0.017, 0.006]
    for i in range(10):
        assert df['ucl'].iloc[i] == pytest.approx(ucl_ref[i], abs=0.002)
        assert df['lcl'].iloc[i] == pytest.approx(lcl_ref[i], abs=0.002)
    # Data point six (index 5) is above UCL and should have OVER_UCL violation
    assert any(v['type'] == RunType.OVER_UCL for v in df['violations'].iloc[5]), (
        'Sixth point should be above UCL and have OVER_UCL violation'
    )


def test_np_chart_with_USPC_p262():
    """USPC p262: np-chart (number defective) with constant sample size, 21 samples."""
    data = {
        'SampleID': list(range(1, 22)),
        'Count': [
            11, 20, 19, 24, 19, 18, 16, 42, 18, 24, 15,
            17, 19, 26, 19, 22, 21, 32, 22, 33, 30,
        ],
    }  # fmt: skip
    df = calc_np(
        pd.DataFrame(data),
        value_column='Count',
        sample_size=60,
        label='SampleID',
    )
    assert len(df) == 21
    assert df['ucl'].iloc[0] == pytest.approx(33.46, abs=0.01)
    assert df['center_line'].iloc[0] == pytest.approx(22.24, abs=0.01)
    assert df['lcl'].iloc[0] == pytest.approx(11.02, abs=0.01)

    # Data point 0 (value 11) is below LCL
    assert df['value'].iloc[0] < df['lcl'].iloc[0]

    # 8th data point (index 7) is out of control, above UCL
    assert any(v['type'] == RunType.OVER_UCL for v in df['violations'].iloc[7]), (
        'Eighth point should be above UCL and have OVER_UCL violation'
    )
