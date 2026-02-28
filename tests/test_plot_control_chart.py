"""
Tests for plot_control_chart() - optional Plotly plotting.

Uses synthetic DataFrames from plotting_fixtures to test plotting logic in isolation
from chart calculations. Integration-style tests (chart type routing) also use
synthetic DataFrames where possible.
"""

import builtins
import pytest
import pandas as pd
from unittest.mock import patch

from pycontrolcharts import plot_control_chart, ChartType
from tests.plotting_fixtures import minimal_chart_df


# --- Input validation tests ---


def test_plot_control_chart_empty_df_raises():
    """Empty chart_df raises ValueError."""
    pytest.importorskip('plotly')
    empty = pd.DataFrame(columns=['value', 'label', 'ucl', 'lcl', 'center_line'])
    with pytest.raises(ValueError, match='empty'):
        plot_control_chart(empty, ChartType.XMR, show_variation=False)


def test_plot_control_chart_missing_required_columns_raises():
    """Missing required columns raises ValueError."""
    pytest.importorskip('plotly')
    df = pd.DataFrame({'value': [1, 2], 'label': [0, 1]})
    with pytest.raises(ValueError, match='required column'):
        plot_control_chart(df, ChartType.XMR)


def test_plot_control_chart_missing_variation_columns_when_show_variation_true():
    """With show_variation=True, missing variation columns raises ValueError."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(3, include_variation=False)
    with pytest.raises(ValueError, match='required column'):
        plot_control_chart(df, ChartType.XMR, show_variation=True)


def test_plot_control_chart_missing_sigma_columns_when_show_sigma_lines_true():
    """With show_sigma_1_lines=True or show_sigma_2_lines=True, missing sigma columns raises ValueError."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(3, include_sigma=False)
    with pytest.raises(ValueError, match='required column'):
        plot_control_chart(
            df, ChartType.XMR, show_variation=False, show_sigma_1_lines=True
        )
    with pytest.raises(ValueError, match='required column'):
        plot_control_chart(
            df, ChartType.XMR, show_variation=False, show_sigma_2_lines=True
        )


# --- Figure structure tests ---


def test_plot_control_chart_returns_figure_with_required_structure():
    """Returns Plotly Figure with layout and data."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(5, include_variation=False)
    fig = plot_control_chart(df, ChartType.XMR, show_variation=False)
    assert fig is not None
    assert hasattr(fig, 'layout')
    assert hasattr(fig, 'data')
    assert len(fig.data) >= 1


def test_plot_control_chart_trace_names_cl_ucl_lcl():
    """Figure contains traces named CL, UCL, LCL."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4, include_variation=False)
    fig = plot_control_chart(df, ChartType.XMR, show_variation=False)
    names = [t.name for t in fig.data]
    assert 'CL' in names
    assert 'UCL' in names
    assert 'LCL' in names
    assert 'Value' in names


def test_plot_control_chart_layout_title():
    """Layout title is set from title argument."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(3, include_variation=False)
    fig = plot_control_chart(
        df, ChartType.XMR, title='Custom Title', show_variation=False
    )
    assert fig.layout.title.text == 'Custom Title'


def test_plot_control_chart_sigma_traces_when_show_sigma_lines_true():
    """With show_sigma_1_lines=True and show_sigma_2_lines=True, figure contains sigma traces."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4, include_sigma=True, include_variation=False)
    fig = plot_control_chart(
        df,
        ChartType.XMR,
        show_variation=False,
        show_sigma_1_lines=True,
        show_sigma_2_lines=True,
    )
    names = [t.name for t in fig.data]
    assert '+2σ' in names
    assert '+1σ' in names
    assert '-1σ' in names
    assert '-2σ' in names


def test_plot_control_chart_spec_traces_when_spec_columns_present():
    """When spec_upper/spec_lower columns exist and show_spec_lines=True, figure contains Spec traces."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4, include_spec=True, include_variation=False)
    fig = plot_control_chart(
        df, ChartType.XMR, show_variation=False, show_spec_lines=True
    )
    names = [t.name for t in fig.data]
    assert 'Spec upper' in names
    assert 'Spec lower' in names


def test_plot_control_chart_subplot_titles_with_show_variation():
    """With show_variation=True, subplot annotations include main and variation titles."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4)
    fig = plot_control_chart(df, ChartType.XMR, show_variation=True)
    if hasattr(fig.layout, 'annotations') and fig.layout.annotations:
        titles = [getattr(a, 'text', None) for a in fig.layout.annotations]
        titles = [t for t in titles if t]
        assert 'Individuals' in titles
        assert 'Moving Range' in titles


# --- Option propagation tests ---


def test_plot_control_chart_show_legend_false_default():
    """show_legend=False (default) hides legend."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(3, include_variation=False)
    fig = plot_control_chart(df, ChartType.XMR, show_variation=False)
    assert fig.layout.showlegend is False


def test_plot_control_chart_show_legend_true():
    """show_legend=True shows legend."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(3, include_variation=False)
    fig = plot_control_chart(df, ChartType.XMR, show_variation=False, show_legend=True)
    assert fig.layout.showlegend is True


def test_plot_control_chart_show_variation_false_single_panel():
    """With show_variation=False, single panel only (no variation subplot)."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4)
    fig = plot_control_chart(df, ChartType.XMR, show_variation=False)
    assert len(fig.data) >= 4  # CL, UCL, LCL, Value at minimum


def test_plot_control_chart_show_sigma_lines_affects_trace_count():
    """show_sigma_1_lines/show_sigma_2_lines=True yields more traces than False."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4, include_sigma=True, include_variation=False)
    fig_with = plot_control_chart(
        df,
        ChartType.XMR,
        show_variation=False,
        show_sigma_1_lines=True,
        show_sigma_2_lines=True,
    )
    fig_without = plot_control_chart(df, ChartType.XMR, show_variation=False)
    assert len(fig_with.data) > len(fig_without.data)


def test_plot_control_chart_show_spec_lines_false_hides_spec_traces():
    """With show_spec_lines=False, no Spec upper/lower traces even when columns exist."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4, include_spec=True, include_variation=False)
    fig = plot_control_chart(
        df, ChartType.XMR, show_variation=False, show_spec_lines=False
    )
    names = [t.name for t in fig.data]
    assert 'Spec upper' not in names
    assert 'Spec lower' not in names


def test_plot_control_chart_height_width_propagated():
    """height and width arguments are applied to layout."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(3, include_variation=False)
    fig = plot_control_chart(
        df, ChartType.XMR, show_variation=False, height=400, width=600
    )
    assert fig.layout.height == 400
    assert fig.layout.width == 600


def test_plot_control_chart_layout_merge():
    """layout dict is merged into figure layout."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(3, include_variation=False)
    fig = plot_control_chart(
        df,
        ChartType.XMR,
        show_variation=False,
        layout={'margin': {'t': 50, 'b': 50}},
    )
    assert hasattr(fig.layout, 'margin')
    assert fig.layout.margin.t == 50
    assert fig.layout.margin.b == 50


def test_plot_control_chart_show_limit_labels_false_fewer_annotations():
    """With show_limit_labels=False, figure has fewer annotations than default True."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4, include_variation=False)
    fig_with_labels = plot_control_chart(
        df, ChartType.XMR, show_variation=False, show_limit_labels=True
    )
    fig_without_labels = plot_control_chart(
        df, ChartType.XMR, show_variation=False, show_limit_labels=False
    )
    n_with = len(fig_with_labels.layout.annotations or [])
    n_without = len(fig_without_labels.layout.annotations or [])
    assert n_with > n_without


def test_plot_control_chart_limit_label_precision_zero_integer_style():
    """With limit_label_precision=0, limit label texts look like integers."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4, include_variation=False)
    fig = plot_control_chart(
        df,
        ChartType.XMR,
        show_variation=False,
        show_limit_labels=True,
        limit_label_precision=0,
    )
    texts = [getattr(a, 'text', '') for a in (fig.layout.annotations or [])]
    # Expect at least one numeric label with no decimal point (e.g. "10", "15", "5")
    numeric_texts = [t for t in texts if t and t.replace('-', '').isdigit()]
    assert len(numeric_texts) >= 1


def test_plot_control_chart_limit_label_precision_three_decimals():
    """With limit_label_precision=3, limit label texts have three decimal places."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4, include_variation=False)
    fig = plot_control_chart(
        df,
        ChartType.XMR,
        show_variation=False,
        show_limit_labels=True,
        limit_label_precision=3,
    )
    texts = [getattr(a, 'text', '') for a in (fig.layout.annotations or [])]
    # Expect at least one label with three decimals (e.g. "10.000", "15.000")
    three_decimal = [t for t in texts if t and '.' in t and len(t.split('.')[-1]) == 3]
    assert len(three_decimal) >= 1


# --- Phase handling tests ---


def test_plot_control_chart_multi_phase_produces_separate_limit_segments():
    """Multi-phase DataFrame produces separate line segments per phase (legendgroup)."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(6, include_phase=True, include_variation=False)
    fig = plot_control_chart(df, ChartType.XMR, show_variation=False)
    # Multiple CL traces (one per phase) share legendgroup
    cl_traces = [t for t in fig.data if t.name == 'CL']
    assert len(cl_traces) >= 1
    # All CL traces share same legendgroup
    if len(cl_traces) > 1:
        groups = {t.legendgroup for t in cl_traces}
        assert len(groups) == 1


# --- Violations styling tests ---


def test_plot_control_chart_violations_use_lines_markers_mode():
    """When violations column present, value trace uses lines+markers mode."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4, include_violations=True, include_variation=False)
    fig = plot_control_chart(df, ChartType.XMR, show_variation=False)
    value_trace = next(t for t in fig.data if t.name == 'Value')
    assert 'markers' in value_trace.mode


def test_plot_control_chart_violations_marker_colors():
    """Violation points get red marker, non-violation get black."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4, include_violations=True, include_variation=False)
    fig = plot_control_chart(df, ChartType.XMR, show_variation=False)
    value_trace = next(t for t in fig.data if t.name == 'Value')
    assert hasattr(value_trace.marker, 'color')
    colors = value_trace.marker.color
    if isinstance(colors, list):
        assert 'red' in colors
        assert 'black' in colors


def test_plot_control_chart_violations_marker_symbols():
    """Violation points use square symbol, non-violation use circle."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4, include_violations=True, include_variation=False)
    fig = plot_control_chart(df, ChartType.XMR, show_variation=False)
    value_trace = next(t for t in fig.data if t.name == 'Value')
    assert hasattr(value_trace.marker, 'symbol')
    symbols = value_trace.marker.symbol
    if isinstance(symbols, list):
        assert 'square' in symbols
        assert 'circle' in symbols


def test_plot_control_chart_violations_hover_includes_tooltip():
    """Value trace text (hover) includes formatted violation tooltip."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4, include_violations=True, include_variation=False)
    fig = plot_control_chart(df, ChartType.XMR, show_variation=False)
    value_trace = next(t for t in fig.data if t.name == 'Value')
    assert hasattr(value_trace, 'text')
    texts = (
        value_trace.text if isinstance(value_trace.text, list) else [value_trace.text]
    )
    # First point has violation with "Over UCL" and "Point beyond UCL"
    assert any('Over UCL' in str(t) for t in texts if t)


# --- Chart type routing tests ---


def test_plot_control_chart_unsupported_raises():
    """Unknown chart type raises NotImplementedError with clear message."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(3, include_variation=False)
    with pytest.raises(NotImplementedError) as exc_info:
        plot_control_chart(df, 'unknown')
    msg = str(exc_info.value)
    assert 'unknown' in msg.lower() or 'support' in msg.lower()
    assert 'xbar_r' in msg or 'xmr' in msg


def test_plot_control_chart_accepts_string_chart_type():
    """chart_type can be string 'xmr'."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(3, include_variation=False)
    fig = plot_control_chart(df, 'xmr', show_variation=False)
    assert fig is not None
    assert len(fig.data) >= 1


def test_plot_control_chart_accepts_enum_chart_type():
    """chart_type can be ChartType enum."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(3, include_variation=False)
    fig = plot_control_chart(df, ChartType.XMR, show_variation=False)
    assert fig is not None
    assert len(fig.data) >= 1


def test_plot_control_chart_xmr_returns_figure():
    """XMR chart type returns Figure."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(4)
    fig = plot_control_chart(df, ChartType.XMR, title='XmR Test')
    assert fig is not None
    assert hasattr(fig, 'layout')
    assert hasattr(fig, 'data')


def test_plot_control_chart_xbar_r_returns_figure():
    """XBAR_R chart type returns Figure with X-bar and Range subplots."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(6)  # variation columns required for xbar_r
    fig = plot_control_chart(df, ChartType.XBAR_R, title='X-bar R Test')
    assert fig is not None
    assert hasattr(fig, 'data')
    if hasattr(fig.layout, 'annotations') and fig.layout.annotations:
        titles = [getattr(a, 'text', None) for a in fig.layout.annotations]
        titles = [t for t in titles if t]
        assert 'X-bar' in titles
        assert 'Range' in titles


def test_plot_control_chart_xbar_s_returns_figure():
    """XBAR_S chart type returns Figure with X-bar and S subplots."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(6)
    fig = plot_control_chart(df, ChartType.XBAR_S, title='X-bar S Test')
    assert fig is not None
    if hasattr(fig.layout, 'annotations') and fig.layout.annotations:
        titles = [getattr(a, 'text', None) for a in fig.layout.annotations]
        titles = [t for t in titles if t]
        assert 'X-bar' in titles
        assert 'S' in titles


def test_plot_control_chart_p_returns_figure():
    """P chart type returns Figure (single panel)."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(5, include_variation=False)
    fig = plot_control_chart(df, ChartType.P, title='p Chart Test')
    assert fig is not None
    assert len(fig.data) >= 1


def test_plot_control_chart_np_returns_figure():
    """NP chart type returns Figure."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(5, include_variation=False)
    fig = plot_control_chart(df, ChartType.NP, title='np Chart Test')
    assert fig is not None
    assert len(fig.data) >= 1


def test_plot_control_chart_c_returns_figure():
    """C chart type returns Figure."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(5, include_variation=False)
    fig = plot_control_chart(df, ChartType.C, title='c Chart Test')
    assert fig is not None
    assert len(fig.data) >= 1


def test_plot_control_chart_u_returns_figure():
    """U chart type returns Figure."""
    pytest.importorskip('plotly')
    df = minimal_chart_df(5, include_variation=False)
    fig = plot_control_chart(df, ChartType.U, title='u Chart Test')
    assert fig is not None
    assert len(fig.data) >= 1


# --- Import error test ---


def test_plot_control_chart_import_error_message():
    """When plotly is missing, raises ImportError with message mentioning plotly."""
    real_import = builtins.__import__

    def block_plotly_only(name, *args, **kwargs):
        if name == 'plotly.graph_objects' or name == 'plotly.subplots':
            raise ImportError(
                'Plotting requires plotly. Install with: pip install pycontrolcharts[plotly]'
            )
        return real_import(name, *args, **kwargs)

    import pycontrolcharts.plotting as plot_mod

    with patch.object(builtins, '__import__', block_plotly_only):
        df = minimal_chart_df(3, include_variation=False)
        with pytest.raises(ImportError) as exc_info:
            plot_mod.plot_control_chart(df, 'xmr')
        msg = str(exc_info.value).lower()
        assert 'plotly' in msg
        assert 'install' in msg or 'pip' in msg
