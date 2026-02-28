"""
PyControlCharts - Statistical Process Control (SPC) Charts for Python

A pandas-integrated library for creating control charts. Returns DataFrames
with all chart data, control limits, and violations in a single table.

API: calc_* for data, plot_control_chart for optional Plotly.
"""

try:
    from importlib.metadata import version

    __version__ = version('pycontrolcharts')
except Exception:
    __version__ = '0.1.0'

from pycontrolcharts.models import CustomLimits, RunType, RunTestConfig, ChartType
from pycontrolcharts.core import run_tests_with_custom_limits
from pycontrolcharts.charts.xmr import xmr_chart as calc_xmr
from pycontrolcharts.charts.xbar_r import xbar_r_chart as calc_xbar_r
from pycontrolcharts.charts.xbar_s import xbar_s_chart as calc_xbar_s
from pycontrolcharts.charts.p_chart import p_chart as calc_p
from pycontrolcharts.charts.np_chart import np_chart as calc_np
from pycontrolcharts.charts.c_chart import c_chart as calc_c
from pycontrolcharts.charts.u_chart import u_chart as calc_u
from pycontrolcharts.plotting import plot_control_chart

__all__ = [
    'CustomLimits',
    'RunType',
    'RunTestConfig',
    'ChartType',
    'run_tests_with_custom_limits',
    'calc_xmr',
    'calc_xbar_r',
    'calc_xbar_s',
    'calc_p',
    'calc_np',
    'calc_c',
    'calc_u',
    'plot_control_chart',
]
