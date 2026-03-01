"""
Optional Plotly-based plotting for control chart DataFrames.

Requires the [plotly] extra: pip install pycontrolcharts[plotly]
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

# Subplot layout for XmR with variation chart
_SUBPLOT_VERTICAL_SPACING = 0.09
_MAIN_ROW_HEIGHT = 0.7
_VARIATION_ROW_HEIGHT = 0.3

# Max x points for "tick at every value"; above this use automatic tick spacing
_X_TICK_EVERY_VALUE_MAX_POINTS = 50

# RunType int -> display name for tooltip "Error type : tooltip text"
_RUN_TYPE_LABELS: dict[int, str] = {
    1: 'Over UCL',
    2: 'Under LCL',
    3: 'Above average',
    4: 'Below average',
    5: 'Increasing run',
    6: 'Decreasing run',
    7: '2 of 3 above +2σ',
    8: '2 of 3 below -2σ',
    9: '4 of 5 below -1σ',
    10: '4 of 5 above +1σ',
}


def _format_violations_description(violations: list[dict[str, Any]]) -> str:
    """Format a list of violation dicts as 'Error type : description' lines (HTML <br>)."""
    if not violations:
        return ''
    lines = []
    for v in violations:
        label = _RUN_TYPE_LABELS.get(v.get('type'), f'Test {v.get("type", "?")}')
        lines.append(f'{label} : {v.get("description", "")}')
    return '<br>'.join(lines)


def _get_phase_ranges(phases: list) -> list[tuple[int, int]]:
    """Return [(start, end), ...] for each contiguous phase."""
    if not phases:
        return [(0, 0)]
    ranges: list[tuple[int, int]] = []
    start = 0
    for i in range(1, len(phases)):
        if phases[i] != phases[i - 1]:
            ranges.append((start, i))
            start = i
    ranges.append((start, len(phases)))
    return ranges


def _x_midpoint(x: list, i: int, j: int) -> float:
    """Midpoint between x[i] and x[j] for segment extension between phases."""
    try:
        return (float(x[i]) + float(x[j])) / 2.0
    except (TypeError, ValueError):
        return (i + j) / 2.0


def _phase_x_extended(x: list, start: int, end: int) -> list:
    """Extend phase x segment to midpoints between phases so lines meet at boundaries."""
    if start >= end:
        return []
    left = _x_midpoint(x, start - 1, start) if start > 0 else x[start]
    right = _x_midpoint(x, end - 1, end) if end < len(x) else x[end - 1]
    return [left] + x[start:end] + [right]


def _step_xy_at_midpoints(x: list, y: list) -> tuple[list, list]:
    """Build (x_ext, y_ext) so that a linear line has vertical steps at midpoints between points."""
    n = len(x)
    if n == 0:
        return [], []
    if n == 1:
        return list(x), list(y)
    x_ext: list[Any] = [x[0]]
    y_ext: list[Any] = [y[0]]
    for i in range(n - 1):
        mid = _x_midpoint(x, i, i + 1)
        x_ext.extend([mid, mid])
        y_ext.extend([y[i], y[i + 1]])
    x_ext.append(x[n - 1])
    y_ext.append(y[n - 1])
    return x_ext, y_ext


def _limit_label_annotation(
    x: float,
    y: float,
    precision: int,
    xref: str,
    yref: str,
    font_color: str | None = None,
) -> dict[str, Any]:
    """Build a Plotly annotation dict for a limit value at the end of a line."""
    out: dict[str, Any] = dict(
        x=x,
        y=y,
        text=f'{y:.{precision}f}',
        xref=xref,
        yref=yref,
        showarrow=False,
        xanchor='right',
        yanchor='bottom',
        yshift=-4,
    )
    if font_color is not None:
        out['font'] = dict(color=font_color)
    return out


def plot_control_chart(
    chart_df: pd.DataFrame,
    chart_type: Any,
    *,
    title: str | None = None,
    show_variation: bool = True,
    show_sigma_1_lines: bool = False,
    show_sigma_2_lines: bool = False,
    show_spec_lines: bool = False,
    show_legend: bool = False,
    show_limit_labels: bool = True,
    limit_label_precision: int = 2,
    force_y_axis_to_zero: bool = False,
    height: int | None = None,
    width: int | None = None,
    layout: dict[str, Any] | None = None,
) -> 'plotly.graph_objects.Figure':  # noqa: F821
    """
    Build a Plotly figure from a control chart DataFrame.

    Requires the optional dependency: pip install pycontrolcharts[plotly]

    Args:
        chart_df: DataFrame returned by one of the calc_* functions.
        chart_type: Which chart type. Supported: ChartType.XMR / "xmr",
            ChartType.XBAR_R / "xbar_r", ChartType.XBAR_S / "xbar_s",
            ChartType.P / "p", ChartType.NP / "np", ChartType.C / "c", ChartType.U / "u".
        title: Figure title. Defaults to a label based on chart_type.
        show_variation: For XmR/Xbar-R/Xbar-S only, also draw the variation chart below.
            Ignored for p, np, c, u (attribute charts are always single-panel).
        show_sigma_1_lines: Draw ±1σ lines (default False). Opacity 0.15.
        show_sigma_2_lines: Draw ±2σ lines (default False). Opacity 0.3.
        show_spec_lines: Draw spec_upper/spec_lower if present (default False).
        show_legend: Show the legend panel (default False).
        show_limit_labels: Draw the numeric value at the end of each limit line (default True).
        limit_label_precision: Decimal places for limit labels (default 2).
        force_y_axis_to_zero: Force main panel y-axis to include zero (default False).
        height: Plot height in pixels (optional).
        width: Plot width in pixels (optional).
        layout: Optional dict merged into the figure layout (fig.update_layout(**layout)).

    Returns:
        plotly.graph_objects.Figure. Call .show() or .write_html() as needed.

    Raises:
        ImportError: If plotly is not installed.
        ValueError: If chart_df is empty or missing required columns.
        NotImplementedError: If chart_type is not supported.
            Supported: xmr, xbar_r, xbar_s, p, np, c, u.
    """
    # Normalize chart_type to string
    ct = chart_type.value if hasattr(chart_type, 'value') else str(chart_type)

    if ct == 'xmr':
        return _plot_xmr(
            chart_df,
            title=title or 'XmR Chart',
            show_variation=show_variation,
            show_sigma_1_lines=show_sigma_1_lines,
            show_sigma_2_lines=show_sigma_2_lines,
            show_spec_lines=show_spec_lines,
            show_legend=show_legend,
            show_limit_labels=show_limit_labels,
            limit_label_precision=limit_label_precision,
            force_y_axis_to_zero=force_y_axis_to_zero,
            height=height,
            width=width,
            layout=layout,
        )
    if ct == 'xbar_r':
        return _plot_main_and_variation(
            chart_df,
            main_title='X-bar',
            variation_title='Range',
            variation_name='R',
            title=title or 'X-bar R Chart',
            show_variation=show_variation,
            show_sigma_1_lines=show_sigma_1_lines,
            show_sigma_2_lines=show_sigma_2_lines,
            show_spec_lines=show_spec_lines,
            show_legend=show_legend,
            show_limit_labels=show_limit_labels,
            limit_label_precision=limit_label_precision,
            force_y_axis_to_zero=force_y_axis_to_zero,
            height=height,
            width=width,
            layout=layout,
        )
    if ct == 'xbar_s':
        return _plot_main_and_variation(
            chart_df,
            main_title='X-bar',
            variation_title='S',
            variation_name='S',
            title=title or 'X-bar S Chart',
            show_variation=show_variation,
            show_sigma_1_lines=show_sigma_1_lines,
            show_sigma_2_lines=show_sigma_2_lines,
            show_spec_lines=show_spec_lines,
            show_legend=show_legend,
            show_limit_labels=show_limit_labels,
            limit_label_precision=limit_label_precision,
            force_y_axis_to_zero=force_y_axis_to_zero,
            height=height,
            width=width,
            layout=layout,
        )
    if ct == 'p':
        return _plot_main_and_variation(
            chart_df,
            main_title='p',
            variation_title='',
            variation_name='',
            title=title or 'p Chart',
            show_variation=False,
            show_sigma_1_lines=show_sigma_1_lines,
            show_sigma_2_lines=show_sigma_2_lines,
            show_spec_lines=show_spec_lines,
            show_legend=show_legend,
            show_limit_labels=show_limit_labels,
            limit_label_precision=limit_label_precision,
            force_y_axis_to_zero=force_y_axis_to_zero,
            height=height,
            width=width,
            layout=layout,
        )
    if ct == 'np':
        return _plot_main_and_variation(
            chart_df,
            main_title='np',
            variation_title='',
            variation_name='',
            title=title or 'np Chart',
            show_variation=False,
            show_sigma_1_lines=show_sigma_1_lines,
            show_sigma_2_lines=show_sigma_2_lines,
            show_spec_lines=show_spec_lines,
            show_legend=show_legend,
            show_limit_labels=show_limit_labels,
            limit_label_precision=limit_label_precision,
            force_y_axis_to_zero=force_y_axis_to_zero,
            height=height,
            width=width,
            layout=layout,
        )
    if ct == 'c':
        return _plot_main_and_variation(
            chart_df,
            main_title='c',
            variation_title='',
            variation_name='',
            title=title or 'c Chart',
            show_variation=False,
            show_sigma_1_lines=show_sigma_1_lines,
            show_sigma_2_lines=show_sigma_2_lines,
            show_spec_lines=show_spec_lines,
            show_legend=show_legend,
            show_limit_labels=show_limit_labels,
            limit_label_precision=limit_label_precision,
            force_y_axis_to_zero=force_y_axis_to_zero,
            height=height,
            width=width,
            layout=layout,
        )
    if ct == 'u':
        return _plot_main_and_variation(
            chart_df,
            main_title='u',
            variation_title='',
            variation_name='',
            title=title or 'u Chart',
            show_variation=False,
            show_sigma_1_lines=show_sigma_1_lines,
            show_sigma_2_lines=show_sigma_2_lines,
            show_spec_lines=show_spec_lines,
            show_legend=show_legend,
            show_limit_labels=show_limit_labels,
            limit_label_precision=limit_label_precision,
            force_y_axis_to_zero=force_y_axis_to_zero,
            height=height,
            width=width,
            layout=layout,
        )

    raise NotImplementedError(
        f'plot_control_chart does not support chart_type={ct!r}. '
        'Supported: xmr, xbar_r, xbar_s, p, np, c, u.'
    )


def _plot_main_and_variation(
    df: pd.DataFrame,
    *,
    main_title: str,
    variation_title: str,
    variation_name: str,
    title: str,
    show_variation: bool,
    show_sigma_1_lines: bool,
    show_sigma_2_lines: bool,
    show_spec_lines: bool,
    show_legend: bool,
    show_limit_labels: bool = True,
    limit_label_precision: int = 2,
    force_y_axis_to_zero: bool = False,
    height: int | None,
    width: int | None,
    layout: dict[str, Any] | None,
) -> 'plotly.graph_objects.Figure':  # noqa: F821
    """
    Shared plotter for control charts with a main series and a variation series
    (XmR, X-bar R, X-bar S). Same DataFrame contract: value, variation, limits.
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError as e:
        raise ImportError(
            'Plotting requires plotly. Install with: pip install pycontrolcharts[plotly]'
        ) from e

    required = ['value', 'label', 'ucl', 'lcl', 'center_line']
    if show_sigma_1_lines:
        required.extend(['sigma_1_upper', 'sigma_1_lower'])
    if show_sigma_2_lines:
        required.extend(['sigma_2_upper', 'sigma_2_lower'])
    if show_variation:
        required.extend(['variation', 'variation_ucl', 'variation_cl', 'variation_lcl'])
    for col in required:
        if col not in df.columns:
            raise ValueError(f'chart_df missing required column: {col!r}')

    if df.empty:
        raise ValueError('chart_df is empty')

    x_labels = df['label'].tolist()
    n = len(x_labels)
    x_numeric = list(range(n))
    phases = df['phase'].tolist() if 'phase' in df.columns else [None] * n

    if show_variation:
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=_SUBPLOT_VERTICAL_SPACING,
            row_heights=[_MAIN_ROW_HEIGHT, _VARIATION_ROW_HEIGHT],
            subplot_titles=(main_title, variation_title),
        )
        row_main, row_var = 1, 2
    else:
        fig = go.Figure()
        row_main = None
        row_var = None

    # Set colors and styling
    _CL_COLOR = 'rgba(0, 0, 0, 0.5)'  # center line: black, opacity 0.5
    _UCL_LCL_COLOR = 'rgba(0, 0, 0, 0.6)'  # UCL/LCL: black, opacity 0.6
    _UCL_LCL_DASH = '8px 2px'
    _SIGMA_GRAY_RGB = (128, 128, 128)
    _SIGMA_1_OPACITY = 0.4
    _SIGMA_2_OPACITY = 0.5
    sigma_1_color = f'rgba({_SIGMA_GRAY_RGB[0]}, {_SIGMA_GRAY_RGB[1]}, {_SIGMA_GRAY_RGB[2]}, {_SIGMA_1_OPACITY})'
    sigma_2_color = f'rgba({_SIGMA_GRAY_RGB[0]}, {_SIGMA_GRAY_RGB[1]}, {_SIGMA_GRAY_RGB[2]}, {_SIGMA_2_OPACITY})'
    _SPEC_COLOR = 'darkorange'
    _LINE_WIDTH = 1
    _VALUE_MARKER_SIZE = 8
    row_arg = row_main

    def add_trace_to_row(trace: go.Scatter, row: int | None) -> None:
        if row is not None:
            fig.add_trace(trace, row=row, col=1)
        else:
            fig.add_trace(trace)

    # Value trace - all data, continuous (x in index space; labels shown via ticktext and hover)
    values = df['value'].tolist()
    value_hover_texts = (
        [_format_violations_description(list(v)) for v in df['violations']]
        if 'violations' in df.columns
        else [''] * n
    )
    _VALUE_HOVERTEMPLATE = (
        'Label: %{customdata}<br>Value: %{y}<br>%{text}<extra></extra>'
    )
    if 'violations' in df.columns:
        violations_bool = [bool(vl) for vl in df['violations']]
        marker_colors = ['red' if v else 'black' for v in violations_bool]
        marker_symbols = ['square' if v else 'circle' for v in violations_bool]
        value_trace = go.Scatter(
            x=x_numeric,
            y=values,
            name='Value',
            mode='lines+markers',
            line=dict(color='rgba(0, 0, 0, 0.5)', width=1),
            marker=dict(
                size=_VALUE_MARKER_SIZE,
                color=marker_colors,
                symbol=marker_symbols,
                line=dict(width=0),
            ),
            text=value_hover_texts,
            customdata=x_labels,
            hovertemplate=_VALUE_HOVERTEMPLATE,
        )
        add_trace_to_row(value_trace, row_arg)
    else:
        value_trace = go.Scatter(
            x=x_numeric,
            y=values,
            name='Value',
            line=dict(color='rgba(0, 0, 0, 0.5)', width=1),
            text=value_hover_texts,
            customdata=x_labels,
            hovertemplate=_VALUE_HOVERTEMPLATE,
        )
        add_trace_to_row(value_trace, row_arg)

    # Limit lines: step at midpoints between points (same approach as phase boundaries)
    center_line = df['center_line'].tolist()
    ucl = df['ucl'].tolist()
    lcl = df['lcl'].tolist()
    spec_upper = df['spec_upper'].tolist() if 'spec_upper' in df.columns else None
    spec_lower = df['spec_lower'].tolist() if 'spec_lower' in df.columns else None
    sigma_2_upper = df['sigma_2_upper'].tolist() if show_sigma_2_lines else None
    sigma_1_upper = df['sigma_1_upper'].tolist() if show_sigma_1_lines else None
    sigma_1_lower = df['sigma_1_lower'].tolist() if show_sigma_1_lines else None
    sigma_2_lower = df['sigma_2_lower'].tolist() if show_sigma_2_lines else None

    _LIMIT_HOVERTEMPLATE = '%{customdata}: %{y}<extra></extra>'
    phase_ranges = _get_phase_ranges(phases)
    x_step, center_line_step = _step_xy_at_midpoints(x_numeric, center_line)
    _, ucl_step = _step_xy_at_midpoints(x_numeric, ucl)
    _, lcl_step = _step_xy_at_midpoints(x_numeric, lcl)
    n_step = len(x_step)
    line_kw: dict[str, Any] = {'width': _LINE_WIDTH, 'shape': 'linear'}

    trace_cl = go.Scatter(
        x=x_step,
        y=center_line_step,
        name='CL',
        legendgroup='CL',
        showlegend=True,
        mode='lines',
        line={**line_kw, 'color': _CL_COLOR},
        customdata=['CL'] * n_step,
        hovertemplate=_LIMIT_HOVERTEMPLATE,
    )
    add_trace_to_row(trace_cl, row_arg)

    trace_ucl = go.Scatter(
        x=x_step,
        y=ucl_step,
        name='UCL',
        legendgroup='UCL',
        showlegend=True,
        mode='lines',
        line={**line_kw, 'color': _UCL_LCL_COLOR, 'dash': _UCL_LCL_DASH},
        customdata=['UCL'] * n_step,
        hovertemplate=_LIMIT_HOVERTEMPLATE,
    )
    add_trace_to_row(trace_ucl, row_arg)

    trace_lcl = go.Scatter(
        x=x_step,
        y=lcl_step,
        name='LCL',
        legendgroup='LCL',
        showlegend=True,
        mode='lines',
        line={**line_kw, 'color': _UCL_LCL_COLOR, 'dash': _UCL_LCL_DASH},
        customdata=['LCL'] * n_step,
        hovertemplate=_LIMIT_HOVERTEMPLATE,
    )
    add_trace_to_row(trace_lcl, row_arg)

    if show_sigma_2_lines and sigma_2_upper is not None:
        _, sigma_2_upper_step = _step_xy_at_midpoints(x_numeric, sigma_2_upper)
        _, sigma_2_lower_step = _step_xy_at_midpoints(x_numeric, sigma_2_lower)
        for name, y_vals in [
            ('+2σ', sigma_2_upper_step),
            ('-2σ', sigma_2_lower_step),
        ]:
            t = go.Scatter(
                x=x_step,
                y=y_vals,
                name=name,
                legendgroup=name,
                showlegend=True,
                mode='lines',
                line={**line_kw, 'color': sigma_2_color, 'dash': _UCL_LCL_DASH},
                customdata=[name] * n_step,
                hovertemplate=_LIMIT_HOVERTEMPLATE,
            )
            add_trace_to_row(t, row_arg)

    if show_sigma_1_lines and sigma_1_upper is not None:
        _, sigma_1_upper_step = _step_xy_at_midpoints(x_numeric, sigma_1_upper)
        _, sigma_1_lower_step = _step_xy_at_midpoints(x_numeric, sigma_1_lower)
        for name, y_vals in [
            ('+1σ', sigma_1_upper_step),
            ('-1σ', sigma_1_lower_step),
        ]:
            t = go.Scatter(
                x=x_step,
                y=y_vals,
                name=name,
                legendgroup=name,
                showlegend=True,
                mode='lines',
                line={**line_kw, 'color': sigma_1_color, 'dash': _UCL_LCL_DASH},
                customdata=[name] * n_step,
                hovertemplate=_LIMIT_HOVERTEMPLATE,
            )
            add_trace_to_row(t, row_arg)

    if show_spec_lines and spec_upper is not None and any(pd.notna(spec_upper)):
        _, spec_upper_step = _step_xy_at_midpoints(x_numeric, spec_upper)
        t = go.Scatter(
            x=x_step,
            y=spec_upper_step,
            name='Spec upper',
            legendgroup='Spec upper',
            showlegend=True,
            mode='lines',
            line={**line_kw, 'color': _SPEC_COLOR},
            customdata=['Spec upper'] * n_step,
            hovertemplate=_LIMIT_HOVERTEMPLATE,
        )
        add_trace_to_row(t, row_arg)
    if show_spec_lines and spec_lower is not None and any(pd.notna(spec_lower)):
        _, spec_lower_step = _step_xy_at_midpoints(x_numeric, spec_lower)
        t = go.Scatter(
            x=x_step,
            y=spec_lower_step,
            name='Spec lower',
            legendgroup='Spec lower',
            showlegend=True,
            mode='lines',
            line={**line_kw, 'color': _SPEC_COLOR},
            customdata=['Spec lower'] * n_step,
            hovertemplate=_LIMIT_HOVERTEMPLATE,
        )
        add_trace_to_row(t, row_arg)

    if show_variation:
        var_vals = df['variation'].tolist()
        var_hover_texts = (
            [
                _format_violations_description(list(v))
                for v in df['variation_violations']
            ]
            if 'variation_violations' in df.columns
            else [''] * n
        )
        var_hovertemplate = f'Label: %{{customdata}}<br>{variation_name}: %{{y}}<br>%{{text}}<extra></extra>'
        var_ucl_label = f'{variation_name} UCL'
        var_cl_label = f'{variation_name} CL'
        var_lcl_label = f'{variation_name} LCL'
        if 'variation_violations' in df.columns:
            var_violations_bool = [bool(vl) for vl in df['variation_violations']]
            var_marker_colors = ['red' if v else 'black' for v in var_violations_bool]
            var_marker_symbols = [
                'square' if v else 'circle' for v in var_violations_bool
            ]
            var_trace = go.Scatter(
                x=x_numeric,
                y=var_vals,
                name=variation_name,
                mode='lines+markers',
                line=dict(color='black', width=0.5),
                marker=dict(
                    size=_VALUE_MARKER_SIZE,
                    color=var_marker_colors,
                    symbol=var_marker_symbols,
                    line=dict(width=0),
                ),
                text=var_hover_texts,
                customdata=x_labels,
                hovertemplate=var_hovertemplate,
            )
        else:
            var_trace = go.Scatter(
                x=x_numeric,
                y=var_vals,
                name=variation_name,
                line=dict(color='black', width=0.5),
                text=var_hover_texts,
                customdata=x_labels,
                hovertemplate=var_hovertemplate,
            )
        fig.add_trace(var_trace, row=row_var, col=1)
        var_ucl = df['variation_ucl'].tolist()
        var_cl = df['variation_cl'].tolist()
        var_lcl = df['variation_lcl'].tolist()
        _, var_ucl_step = _step_xy_at_midpoints(x_numeric, var_ucl)
        _, var_cl_step = _step_xy_at_midpoints(x_numeric, var_cl)
        _, var_lcl_step = _step_xy_at_midpoints(x_numeric, var_lcl)
        var_line_kw: dict[str, Any] = {
            'width': _LINE_WIDTH,
            'shape': 'linear',
        }
        fig.add_trace(
            go.Scatter(
                x=x_step,
                y=var_ucl_step,
                name=var_ucl_label,
                legendgroup=var_ucl_label,
                showlegend=True,
                mode='lines',
                line={**var_line_kw, 'color': _UCL_LCL_COLOR, 'dash': _UCL_LCL_DASH},
                customdata=[var_ucl_label] * n_step,
                hovertemplate=_LIMIT_HOVERTEMPLATE,
            ),
            row=row_var,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=x_step,
                y=var_cl_step,
                name=var_cl_label,
                legendgroup=var_cl_label,
                showlegend=True,
                mode='lines',
                line={**var_line_kw, 'color': _CL_COLOR},
                customdata=[var_cl_label] * n_step,
                hovertemplate=_LIMIT_HOVERTEMPLATE,
            ),
            row=row_var,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=x_step,
                y=var_lcl_step,
                name=var_lcl_label,
                legendgroup=var_lcl_label,
                showlegend=True,
                mode='lines',
                line={
                    **var_line_kw,
                    'color': _UCL_LCL_COLOR,
                    'dash': _UCL_LCL_DASH,
                },
                customdata=[var_lcl_label] * n_step,
                hovertemplate=_LIMIT_HOVERTEMPLATE,
            ),
            row=row_var,
            col=1,
        )

    if show_limit_labels:
        xref_main, yref_main = 'x', 'y'
        prec = limit_label_precision
        for start, end in phase_ranges:
            if start >= end:
                continue
            x_end = (
                _x_midpoint(x_numeric, end - 1, end) if end < n else x_numeric[end - 1]
            )
            for y_val in (center_line[end - 1], ucl[end - 1], lcl[end - 1]):
                if math.isfinite(y_val):
                    fig.add_annotation(
                        **_limit_label_annotation(
                            x_end, y_val, prec, xref_main, yref_main
                        )
                    )
            if show_sigma_2_lines and sigma_2_upper is not None:
                for y_vals in (sigma_2_upper, sigma_2_lower):
                    y_val = y_vals[end - 1]
                    if math.isfinite(y_val):
                        fig.add_annotation(
                            **_limit_label_annotation(
                                x_end,
                                y_val,
                                prec,
                                xref_main,
                                yref_main,
                                font_color=sigma_2_color,
                            )
                        )
            if show_sigma_1_lines and sigma_1_upper is not None:
                for y_vals in (sigma_1_upper, sigma_1_lower):
                    y_val = y_vals[end - 1]
                    if math.isfinite(y_val):
                        fig.add_annotation(
                            **_limit_label_annotation(
                                x_end,
                                y_val,
                                prec,
                                xref_main,
                                yref_main,
                                font_color=sigma_1_color,
                            )
                        )
            if show_spec_lines and spec_upper is not None and any(pd.notna(spec_upper)):
                y_val = spec_upper[end - 1]
                if math.isfinite(y_val):
                    fig.add_annotation(
                        **_limit_label_annotation(
                            x_end, y_val, prec, xref_main, yref_main
                        )
                    )
            if show_spec_lines and spec_lower is not None and any(pd.notna(spec_lower)):
                y_val = spec_lower[end - 1]
                if math.isfinite(y_val):
                    fig.add_annotation(
                        **_limit_label_annotation(
                            x_end, y_val, prec, xref_main, yref_main
                        )
                    )
        if show_variation:
            xref_var, yref_var = 'x2', 'y2'
            var_ucl = df['variation_ucl'].tolist()
            var_cl = df['variation_cl'].tolist()
            var_lcl = df['variation_lcl'].tolist()
            for start, end in phase_ranges:
                if start >= end:
                    continue
                x_end = (
                    _x_midpoint(x_numeric, end - 1, end)
                    if end < n
                    else x_numeric[end - 1]
                )
                for y_val in (
                    var_ucl[end - 1],
                    var_cl[end - 1],
                    var_lcl[end - 1],
                ):
                    if math.isfinite(y_val):
                        fig.add_annotation(
                            **_limit_label_annotation(
                                x_end, y_val, prec, xref_var, yref_var
                            )
                        )

    _PLOT_BG_COLOR = '#f5f5f5'
    _AXIS_FRAME = {
        'showgrid': False,
        'zeroline': False,
        'showline': True,
        'linecolor': 'black',
        'linewidth': 1,
        'ticks': 'outside',
        'ticklen': 4,
        'tickcolor': 'black',
        'mirror': True,
    }
    # Plot in index space; show original labels via ticktext
    _X_TICKS_EVERY_VALUE = (
        {
            'tickmode': 'array',
            'tickvals': x_numeric,
            'ticktext': x_labels,
        }
        if n <= _X_TICK_EVERY_VALUE_MAX_POINTS
        else {}
    )
    x_range_padding = max(x_numeric) * 0.02
    _X_RANGE = (
        {'range': [0 - x_range_padding, max(x_numeric) + x_range_padding]}
        if n > 0
        else {}
    )
    _yaxis_main: dict[str, Any] = {**_AXIS_FRAME}
    if force_y_axis_to_zero:
        _yaxis_main['rangemode'] = 'tozero'
    layout_kw: dict[str, Any] = {
        'title': title,
        'showlegend': show_legend,
        'paper_bgcolor': 'white',
        'plot_bgcolor': _PLOT_BG_COLOR,
        'xaxis': {**_AXIS_FRAME, **_X_TICKS_EVERY_VALUE, **_X_RANGE},
        'yaxis': _yaxis_main,
    }
    if show_variation:
        layout_kw['xaxis'] = {
            **_AXIS_FRAME,
            **_X_TICKS_EVERY_VALUE,
            **_X_RANGE,
            'showticklabels': True,
        }
        layout_kw['xaxis2'] = {
            **_AXIS_FRAME,
            **_X_TICKS_EVERY_VALUE,
            **_X_RANGE,
            'showticklabels': False,
            'ticklen': 0,
        }
        layout_kw['yaxis2'] = {**_AXIS_FRAME, 'ticklen': 0}
    if height is not None:
        layout_kw['height'] = height
    if width is not None:
        layout_kw['width'] = width

    # layout_kw['margin'] = {
    #     'pad': 10,
    # }
    fig.update_layout(**layout_kw)
    if show_variation and variation_title and len(fig.layout.annotations) >= 2:
        # Move variation subplot title from above to below the chart
        ann = fig.layout.annotations[1]
        ann.update(
            xref='x2 domain',
            yref='y2 domain',
            x=0.5,
            y=-0.08,
            yanchor='top',
        )
    if layout:
        fig.update_layout(**layout)

    return fig


def _plot_xmr(
    df: pd.DataFrame,
    *,
    title: str,
    show_variation: bool,
    show_sigma_1_lines: bool,
    show_sigma_2_lines: bool,
    show_spec_lines: bool,
    show_legend: bool,
    show_limit_labels: bool = True,
    limit_label_precision: int = 2,
    force_y_axis_to_zero: bool = False,
    height: int | None,
    width: int | None,
    layout: dict[str, Any] | None,
) -> 'plotly.graph_objects.Figure':  # noqa: F821
    """XmR (Individuals and Moving Range) plot via shared main+variation plotter."""
    return _plot_main_and_variation(
        df,
        main_title='Individuals',
        variation_title='Moving Range',
        variation_name='MR',
        title=title,
        show_variation=show_variation,
        show_sigma_1_lines=show_sigma_1_lines,
        show_sigma_2_lines=show_sigma_2_lines,
        show_spec_lines=show_spec_lines,
        show_legend=show_legend,
        show_limit_labels=show_limit_labels,
        limit_label_precision=limit_label_precision,
        force_y_axis_to_zero=force_y_axis_to_zero,
        height=height,
        width=width,
        layout=layout,
    )
