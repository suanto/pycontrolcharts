#!/usr/bin/env python3
"""
Drive USPC and GTDA reference charts to HTML for visual inspection.

Copies data and calc logic from tests (test_imr_chart, test_p_np_charts, test_u_c_chart).
Run from repo root with plotly installed: pip install pycontrolcharts[plotly]
  python scripts/drive_reference_charts.py [--output-dir chart_output] [--write-csv] [--write-json]
"""

import argparse
import importlib.util
import sys
from pathlib import Path

if importlib.util.find_spec('plotly') is None:
    sys.exit(
        'Plotting requires plotly. Install with: pip install pycontrolcharts[plotly]'
    )

import pandas as pd

from pycontrolcharts import (
    ChartType,
    calc_c,
    calc_np,
    calc_p,
    calc_u,
    calc_xbar_r,
    calc_xbar_s,
    calc_xmr,
    plot_control_chart,
)


def _uspc_p49():
    """USPC p49: XmR (Wheeler)."""
    values = [
        39, 41, 41, 41, 43, 44, 41, 42, 40, 41, 44, 40,
    ]  # fmt: skip
    return calc_xmr(values), ChartType.XMR, 'uspc_p49_xmr', 'USPC p49 XmR'


def _uspc_p215():
    """USPC p215: XmR."""
    values = [
        905, 930, 865, 895, 905, 885, 890, 930,
        915, 910, 920, 915, 925, 860, 905, 925,
        925, 905, 915, 930, 890, 940, 860, 875,
        985, 970, 940, 975, 1000, 1035, 1020, 985,
        960, 945, 965, 940, 900, 920, 980, 950,
        955, 970, 970, 1035, 1040,
    ]  # fmt: skip
    return (
        calc_xmr(values, spec_upper=1050, spec_lower=850),
        ChartType.XMR,
        'uspc_p215_xmr',
        'USPC p215 XmR',
    )


def _gtda_p134():
    """GTDA p134: XmR with phases (Treatment A/B/C/D)."""
    data = {
        'Treatment': (['A'] * 10 + ['B'] * 10 + ['C'] * 10 + ['D'] * 10),
        'Value': [
            9, 14, 9, 12, 10, 11, 7, 9, 12, 13,
            14, 11, 10, 14, 12, 11, 11, 10, 13, 9,
            14, 17, 17, 13, 13, 12, 14, 16, 15, 18,
            12, 14, 17, 12, 11, 13, 15, 16, 14, 13,
        ],
    }  # fmt: skip
    df = calc_xmr(pd.DataFrame(data), value_column='Value', phase='Treatment')
    return df, ChartType.XMR, 'gtda_p134_xmr', 'GTDA p134 XmR (phases)'


def _uspc_p56_data() -> pd.DataFrame:
    """USPC p56: raw data (Value, Subgroup) — subgroups I/II/III, 8 values each."""
    data = {
        'Value': [
            4, 5, 5, 4, 8, 4, 3, 7,
            0, 2, 1, 5, 3, 2, 0, 3,
            6, 9, 9, 7, 8, 7, 9, 9,
        ],
        'Subgroup': (['I'] * 8 + ['II'] * 8 + ['III'] * 8),
    }  # fmt: skip
    return pd.DataFrame(data)


def _uspc_p56():
    """USPC p56: XmR with phases (Subgroup I/II/III)."""
    df = calc_xmr(_uspc_p56_data(), value_column='Value', phase='Subgroup')
    return df, ChartType.XMR, 'uspc_p56_xmr', 'USPC p56 XmR (phases)'


def _uspc_p56_xbar_r():
    """USPC p56: X-bar R (subgroups I/II/III)."""
    df = calc_xbar_r(
        _uspc_p56_data(),
        value_column='Value',
        subgroup='Subgroup',
    )
    return df, ChartType.XBAR_R, 'uspc_p56_xbar_r', 'USPC p56 X-bar R'


def _uspc_p56_xbar_s():
    """USPC p56: X-bar S (subgroups I/II/III)."""
    df = calc_xbar_s(
        _uspc_p56_data(),
        value_column='Value',
        subgroup='Subgroup',
    )
    return df, ChartType.XBAR_S, 'uspc_p56_xbar_s', 'USPC p56 X-bar S'


def _uspc_p27_data() -> pd.DataFrame:
    """USPC p27: raw data (ID, Group, Value), 204 points, 51 groups of 4."""
    data = {
        'ID': list(range(1, 205)),
        'Group': [g for g in range(1, 52) for _ in range(4)],
        'Value': [
            5045, 4350, 4350, 3975, 4290, 4430, 4485, 4285,
            3980, 3925, 3645, 3760, 3300, 3685, 3463, 5200,
            5100, 4635, 5100, 5450, 4635, 4720, 4810, 4565,
            4410, 4065, 4565, 5190, 4725, 4640, 4640, 4895,
            4790, 4845, 4700, 4600, 4110, 4410, 4180, 4790,
            4790, 4340, 4895, 5750, 4740, 5000, 4895, 4255,
            4170, 3850, 4445, 4650, 4170, 4255, 4170, 4375,
            4175, 4550, 4450, 2855, 2920, 4375, 4375, 4355,
            4090, 5000, 4335, 5000, 4640, 4335, 5000, 4615,
            4215, 4275, 4275, 5000, 4615, 4735, 4215, 4700,
            4700, 4700, 4700, 4095, 4095, 3940, 3700, 3650,
            4445, 4000, 4845, 5000, 4560, 4700, 4310, 4310,
            5000, 4575, 4700, 4430, 4850, 4850, 4570, 4570,
            4855, 4160, 4325, 4125, 4100, 4340, 4575, 3875,
            4050, 4050, 4685, 4685, 4430, 4300, 4690, 4560,
            3075, 2965, 4080, 4080, 4425, 4300, 4430, 4840,
            4840, 4310, 4185, 4570, 4700, 4440, 4850, 4125,
            4450, 4450, 4850, 4450, 3635, 3635, 3635, 3900,
            4340, 4340, 3665, 3775, 5000, 4850, 4775, 4500,
            4770, 4500, 4770, 5150, 4850, 4700, 5000, 5000,
            5000, 4700, 4500, 4840, 5075, 5000, 4770, 4570,
            4925, 4775, 5075, 4925, 5075, 4925, 5250, 4915,
            5600, 5075, 4450, 4215, 4325, 4665, 4615, 4615,
            4500, 4765, 4500, 4500, 4850, 4930, 4700, 4890,
            4625, 4425, 4135, 4190, 4080, 3690, 5050, 4625,
            5150, 5250, 5000, 5000,
        ],
    }  # fmt: skip
    return pd.DataFrame(data)


def _uspc_p27():
    """USPC p27: XmR, 204 points."""
    df = calc_xmr(_uspc_p27_data(), value_column='Value')
    return df, ChartType.XMR, 'uspc_p27_xmr', 'USPC p27 XmR'


def _uspc_p27_xbar_r():
    """USPC p27: X-bar R, 204 points, 51 groups of 4."""
    df = calc_xbar_r(
        _uspc_p27_data(),
        value_column='Value',
        subgroup='Group',
    )
    return df, ChartType.XBAR_R, 'uspc_p27_xbar_r', 'USPC p27 X-bar R'


def _uspc_p27_xbar_s():
    """USPC p27: X-bar S, 204 points, 51 groups of 4."""
    df = calc_xbar_s(
        _uspc_p27_data(),
        value_column='Value',
        subgroup='Group',
    )
    return df, ChartType.XBAR_S, 'uspc_p27_xbar_s', 'USPC p27 X-bar S'


def _uspc_p264_data() -> pd.DataFrame:
    """USPC p264: raw data (incomplete invoices)."""
    data = {
        'Date': [
            '27.9.2018', '28.9.2018', '29.9.2018', '30.9.2018', '1.10.2018',
            '4.10.2018', '5.10.2018', '6.10.2018', '7.10.2018', '8.10.2018',
            '11.10.2018', '12.10.2018', '13.10.2018', '14.10.2018', '15.10.2018',
            '18.10.2018', '19.10.2018', '20.10.2018', '21.10.2018', '22.10.2018',
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
    return pd.DataFrame(data)


def _uspc_p264_p_chart(*, label: str | None = 'Date', phase: list | None = None):
    """USPC p264: p-chart (incomplete invoices). Returns (df, ChartType.P)."""
    df = calc_p(
        _uspc_p264_data(),
        value_column='NofIncompleteInvoices',
        label=label,
        sample_size_column='NofInvoices',
        phase=phase,
    )
    return df, ChartType.P


def _uspc_p262():
    """USPC p262: np-chart (number defective, n=60)."""
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
    return df, ChartType.NP, 'uspc_p262_np', 'USPC p262 np-chart'


def _uspc_p276_data() -> pd.DataFrame:
    """USPC p276: raw data (NofLeaks / NofRadiators)."""
    data = {
        'Date': [
            '3.6.1948', '4.6.1948', '5.6.1948', '6.6.1948', '7.6.1948',
            '10.6.1948', '11.6.1948', '12.6.1948', '13.6.1948', '14.6.1948',
            '17.6.1948', '18.6.1948', '19.6.1948', '20.6.1948', '24.6.1948',
            '25.6.1948', '26.6.1948', '27.6.1948',
        ],
        'NofLeaks': [
            14, 4, 5, 13, 6, 2, 4, 11, 8, 10, 3, 11, 1, 3, 6, 8, 5, 2,
        ],
        'NofRadiators': [
            39, 45, 46, 48, 40, 58, 50, 50, 50, 50,
            32, 50, 33, 50, 50, 50, 50, 50,
        ],
    }  # fmt: skip
    return pd.DataFrame(data)


def _uspc_p276_u_chart(*, phase: list | None = None):
    """USPC p276: u-chart variable area. Returns (df, ChartType.U)."""
    df = calc_u(
        _uspc_p276_data(),
        value_column='NofLeaks',
        label='Date',
        area_column='NofRadiators',
        phase=phase,
    )
    return df, ChartType.U


def _uspc_p273():
    """USPC p273: u-chart constant area."""
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
    return df, ChartType.U, 'uspc_p273_u', 'USPC p273 u-chart'


def _uspc_p273_c():
    """USPC p273: c-chart (same counts as u-chart constant area)."""
    counts = [
        2, 4, 1, 1, 4, 5, 2, 1, 2, 4,
        4, 3, 5, 2, 1, 1, 2, 3, 2, 4,
        3, 2, 4, 3, 2, 3, 5, 1, 4, 3,
        4, 2, 3, 6, 4, 0, 1, 2, 3, 1,
    ]  # fmt: skip
    df = calc_c(counts)
    return df, ChartType.C, 'uspc_p273_c', 'USPC p273 c-chart'


def _uspc_p220_c_chart():
    """USPC p220: c-chart (monthly injury counts, 24 months)."""
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
    return df, ChartType.C, 'uspc_p220_c', 'USPC p220 c-chart'


def _get_data(fn):
    """Return (df, chart_type) from helper that returns (df, chart_type, stem, title)."""
    result = fn()
    return result[0], result[1]


_TESTS = [
    {
        'get_data': lambda: _get_data(_uspc_p49),
        'plot_kwargs': {
            'show_variation': True,
            'show_sigma_1_lines': True,
            'show_sigma_2_lines': True,
        },
        'filename_stem': 'uspc_p49_xmr_var_sigma',
        'csv_stem': 'uspc_p49_xmr',
        'base_title': 'USPC p49 XmR',
        'config_str': 'variation, sigma_lines',
    },
    {
        'get_data': lambda: _get_data(_uspc_p215),
        'plot_kwargs': {
            'show_variation': True,
            'show_sigma_1_lines': True,
            'show_sigma_2_lines': True,
            'show_spec_lines': True,
        },
        'filename_stem': 'uspc_p215_xmr_var_sigma_spec',
        'csv_stem': 'uspc_p215_xmr',
        'base_title': 'USPC p215 XmR',
        'config_str': 'variation, sigma_lines, spec_lines',
    },
    {
        'get_data': lambda: _get_data(_uspc_p215),
        'plot_kwargs': {'show_variation': False},
        'filename_stem': 'uspc_p215_xmr_no_var',
        'csv_stem': 'uspc_p215_xmr',
        'base_title': 'USPC p215 XmR',
        'config_str': 'no variation',
    },
    {
        'get_data': lambda: _get_data(_gtda_p134),
        'plot_kwargs': {'show_variation': True},
        'filename_stem': 'gtda_p134_xmr_phases_var',
        'csv_stem': 'gtda_p134_xmr',
        'base_title': 'GTDA p134 XmR (phases)',
        'config_str': 'variation',
    },
    {
        'get_data': lambda: _get_data(_gtda_p134),
        'plot_kwargs': {'show_variation': False},
        'filename_stem': 'gtda_p134_xmr_phases_no_var',
        'csv_stem': 'gtda_p134_xmr',
        'base_title': 'GTDA p134 XmR (phases)',
        'config_str': 'no variation',
    },
    {
        'get_data': lambda: _get_data(_uspc_p56_xbar_r),
        'plot_kwargs': {'show_variation': True},
        'filename_stem': 'uspc_p56_xbar_r_var',
        'csv_stem': 'uspc_p56_xbar_r',
        'base_title': 'USPC p56 X-bar R',
        'config_str': 'variation',
    },
    {
        'get_data': lambda: _get_data(_uspc_p56_xbar_r),
        'plot_kwargs': {'show_variation': False},
        'filename_stem': 'uspc_p56_xbar_r_no_var',
        'csv_stem': 'uspc_p56_xbar_r',
        'base_title': 'USPC p56 X-bar R',
        'config_str': 'no variation',
    },
    {
        'get_data': lambda: _get_data(_uspc_p56_xbar_s),
        'plot_kwargs': {'show_variation': True},
        'filename_stem': 'uspc_p56_xbar_s_var',
        'csv_stem': 'uspc_p56_xbar_s',
        'base_title': 'USPC p56 X-bar S',
        'config_str': 'variation',
    },
    {
        'get_data': lambda: _get_data(_uspc_p56_xbar_s),
        'plot_kwargs': {'show_variation': False},
        'filename_stem': 'uspc_p56_xbar_s_no_var',
        'csv_stem': 'uspc_p56_xbar_s',
        'base_title': 'USPC p56 X-bar S',
        'config_str': 'no variation',
    },
    {
        'get_data': lambda: _get_data(_uspc_p27_xbar_r),
        'plot_kwargs': {'show_variation': True},
        'filename_stem': 'uspc_p27_xbar_r_var',
        'csv_stem': 'uspc_p27_xbar_r',
        'base_title': 'USPC p27 X-bar R',
        'config_str': 'variation',
    },
    {
        'get_data': lambda: _get_data(_uspc_p27_xbar_s),
        'plot_kwargs': {'show_variation': True},
        'filename_stem': 'uspc_p27_xbar_s_var',
        'csv_stem': 'uspc_p27_xbar_s',
        'base_title': 'USPC p27 X-bar S',
        'config_str': 'variation',
    },
    {
        'get_data': lambda: _get_data(_uspc_p56),
        'plot_kwargs': {'show_variation': True, 'force_y_axis_to_zero': False},
        'filename_stem': 'uspc_p56_xmr_var',
        'csv_stem': 'uspc_p56_xmr',
        'base_title': 'USPC p56 XmR (phases)',
        'config_str': 'variation',
    },
    {
        'get_data': lambda: _get_data(_uspc_p56),
        'plot_kwargs': {'show_variation': True, 'force_y_axis_to_zero': True},
        'filename_stem': 'uspc_p56_xmr_var_yzero',
        'csv_stem': 'uspc_p56_xmr',
        'base_title': 'USPC p56 XmR (phases)',
        'config_str': 'variation, force_y_zero',
    },
    {
        'get_data': lambda: _get_data(_uspc_p27),
        'plot_kwargs': {'show_variation': True},
        'filename_stem': 'uspc_p27_xmr_var',
        'csv_stem': 'uspc_p27_xmr',
        'base_title': 'USPC p27 XmR',
        'config_str': 'variation',
    },
    {
        'get_data': lambda: _uspc_p264_p_chart(label='Date', phase=None),
        'plot_kwargs': {},
        'filename_stem': 'uspc_p264_p_label',
        'csv_stem': 'uspc_p264_p_label',
        'base_title': 'USPC p264 p-chart',
        'config_str': 'label',
    },
    {
        'get_data': lambda: _uspc_p264_p_chart(label=None, phase=None),
        'plot_kwargs': {},
        'filename_stem': 'uspc_p264_p_no_label',
        'csv_stem': 'uspc_p264_p_no_label',
        'base_title': 'USPC p264 p-chart',
        'config_str': 'no label',
    },
    {
        'get_data': lambda: _uspc_p264_p_chart(
            label='Date', phase=['P1'] * 10 + ['P2'] * 10
        ),
        'plot_kwargs': {},
        'filename_stem': 'uspc_p264_p_label_2phases',
        'csv_stem': 'uspc_p264_p_label_2phases',
        'base_title': 'USPC p264 p-chart',
        'config_str': 'label, 2 phases',
    },
    {
        'get_data': lambda: _get_data(_uspc_p262),
        'plot_kwargs': {},
        'filename_stem': 'uspc_p262_np',
        'csv_stem': 'uspc_p262_np',
        'base_title': 'USPC p262 np-chart',
        'config_str': None,
    },
    {
        'get_data': lambda: _uspc_p276_u_chart(phase=None),
        'plot_kwargs': {},
        'filename_stem': 'uspc_p276_u',
        'csv_stem': 'uspc_p276_u',
        'base_title': 'USPC p276 u-chart',
        'config_str': None,
    },
    {
        'get_data': lambda: _uspc_p276_u_chart(phase=['P1'] * 9 + ['P2'] * 9),
        'plot_kwargs': {},
        'filename_stem': 'uspc_p276_u_2phases',
        'csv_stem': 'uspc_p276_u_2phases',
        'base_title': 'USPC p276 u-chart',
        'config_str': '2 phases',
    },
    {
        'get_data': lambda: _get_data(_uspc_p273),
        'plot_kwargs': {},
        'filename_stem': 'uspc_p273_u',
        'csv_stem': 'uspc_p273_u',
        'base_title': 'USPC p273 u-chart',
        'config_str': None,
    },
    {
        'get_data': lambda: _get_data(_uspc_p273_c),
        'plot_kwargs': {},
        'filename_stem': 'uspc_p273_c',
        'csv_stem': 'uspc_p273_c',
        'base_title': 'USPC p273 c-chart',
        'config_str': None,
    },
    {
        'get_data': lambda: _get_data(_uspc_p220_c_chart),
        'plot_kwargs': {
            'show_sigma_1_lines': True,
            'show_sigma_2_lines': True,
        },
        'filename_stem': 'uspc_p220_c',
        'csv_stem': 'uspc_p220_c',
        'base_title': 'USPC p220 c-chart',
        'config_str': 'sigma_lines',
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Write USPC/GTDA reference charts to HTML for visual inspection.',
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('chart_output'),
        help='Directory for HTML files (default: chart_output)',
    )
    parser.add_argument(
        '--write-csv',
        action='store_true',
        help='Write chart data to CSV (one file per unique dataset)',
    )
    parser.add_argument(
        '--write-json',
        action='store_true',
        help='Write chart data to JSON (one file per chart, orient=records)',
    )
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    for entry in _TESTS:
        chart_df, chart_type = entry['get_data']()
        plot_kwargs = entry['plot_kwargs'].copy()
        config_parts = entry.get('config_str')
        if config_parts:
            full_title = f'{entry["base_title"]} | {config_parts}'
        else:
            full_title = entry['base_title']
        plot_kwargs['title'] = full_title
        fig = plot_control_chart(chart_df, chart_type, **plot_kwargs)
        path = out / f'{entry["filename_stem"]}.html'
        fig.write_html(str(path))
        print(path)
        if args.write_csv:
            chart_df.to_csv(out / f'{entry["filename_stem"]}.csv', index=True)
        if args.write_json:
            json_path = out / f'{entry["filename_stem"]}.json'
            # orient=records gives list of row dicts; index as column for parity with CSV
            chart_df.reset_index().to_json(
                json_path, orient='records', date_format='iso', indent=2
            )
            print(json_path)


if __name__ == '__main__':
    main()
