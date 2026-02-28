"""
Core functions for run test detection and violation marking.

Run tests are implemented as in the TypeScript SPC reference: we detect
*runs* (consecutive points satisfying a rule) and mark every point in each run,
not only the point that completes the run.
"""

from typing import Any, Iterator

import pandas as pd

from pycontrolcharts.chart_helpers import create_empty_chart_dataframe
from pycontrolcharts.input_handlers import normalize_simple_input
from pycontrolcharts.models import CustomLimits, RunType, RunTestConfig
from pycontrolcharts.output_builder import build_output_dataframe, create_violation_dict
from pycontrolcharts.utils import calc_moving_range, is_finite


def _limits_at(
    control_limits_per_point: list[dict[str, float]], i: int, n: int
) -> dict[str, float]:
    """Return the limit dict for point index i (single dict or per-point)."""
    if len(control_limits_per_point) > 1:
        return control_limits_per_point[i]
    return control_limits_per_point[0]


# --- Run type: (start_idx, end_idx_inclusive, run_type, description) ---
_Run = tuple[int, int, int, str]


def _runs_test1(
    values: list[float],
    control_limits_per_point: list[dict[str, float]],
    n: int,
) -> Iterator[_Run]:
    """Run test 1: points beyond UCL or LCL. Yields (start, end_incl, type, desc)."""
    count = 0
    direction: str = 'none'  # "over" | "under" | "none"
    desc_over = 'Point beyond upper control limit'
    desc_under = 'Point beyond lower control limit'

    for i in range(n):
        v = values[i]
        if not is_finite(v):
            continue
        lim = _limits_at(control_limits_per_point, i, n)
        ucl, lcl = lim['ucl'], lim['lcl']

        if v > ucl:
            if direction == 'under':
                if count >= 1:
                    yield (i - count, i - 1, RunType.UNDER_LCL, desc_under)
                direction = 'over'
                count = 1
            elif direction == 'over':
                count += 1
            else:
                direction = 'over'
                count = 1
        elif v < lcl:
            if direction == 'over':
                if count >= 1:
                    yield (i - count, i - 1, RunType.OVER_UCL, desc_over)
                direction = 'under'
                count = 1
            elif direction == 'under':
                count += 1
            else:
                direction = 'under'
                count = 1
        else:
            if count >= 1:
                run_type = (
                    RunType.OVER_UCL if direction == 'over' else RunType.UNDER_LCL
                )
                desc = desc_over if direction == 'over' else desc_under
                yield (i - count, i - 1, run_type, desc)
            direction = 'none'
            count = 0

        if i == n - 1 and count >= 1:
            run_type = RunType.OVER_UCL if direction == 'over' else RunType.UNDER_LCL
            desc = desc_over if direction == 'over' else desc_under
            yield (i - count + 1, i, run_type, desc)


def _runs_test2(
    values: list[float],
    control_limits_per_point: list[dict[str, float]],
    n: int,
    threshold: int,
) -> Iterator[_Run]:
    """Run test 2: N consecutive points same side of center. Yields runs."""
    count = 0
    direction: str = 'none'  # "up" | "down" | "none"
    desc_up = f'{threshold} consecutive points above center line'
    desc_down = f'{threshold} consecutive points below center line'

    for i in range(n):
        v = values[i]
        lim = _limits_at(control_limits_per_point, i, n)
        cl = lim['center_line']

        if not is_finite(v):
            direction = 'none'
            count = 0
        elif v < cl:
            if direction == 'up':
                if count >= threshold:
                    yield (i - count, i - 1, RunType.X_OVER_AVG, desc_up)
                direction = 'down'
                count = 1
            elif direction == 'down':
                count += 1
            else:
                direction = 'down'
                count = 1
        elif v > cl:
            if direction == 'down':
                if count >= threshold:
                    yield (i - count, i - 1, RunType.X_UNDER_AVG, desc_down)
                direction = 'up'
                count = 1
            elif direction == 'up':
                count += 1
            else:
                direction = 'up'
                count = 1
        else:
            if count >= threshold:
                run_type = (
                    RunType.X_OVER_AVG if direction == 'up' else RunType.X_UNDER_AVG
                )
                desc = desc_up if direction == 'up' else desc_down
                yield (i - count, i - 1, run_type, desc)
            direction = 'none'
            count = 0

        if i == n - 1 and count >= threshold:
            run_type = RunType.X_OVER_AVG if direction == 'up' else RunType.X_UNDER_AVG
            desc = desc_up if direction == 'up' else desc_down
            yield (i - count + 1, i, run_type, desc)


def _runs_test3(
    values: list[float],
    n: int,
    threshold: int,
) -> Iterator[_Run]:
    """Run test 3: N consecutive strictly increasing or decreasing. Yields runs."""
    count = 0
    direction: str = 'none'  # "up" | "down" | "none"
    prev: float | None = None
    desc_up = f'{threshold} consecutive increasing points'
    desc_down = f'{threshold} consecutive decreasing points'

    for i in range(n):
        cur = values[i]
        if not is_finite(cur):
            direction = 'none'
            count = 0
            prev = cur
            continue

        if prev is None:
            prev = cur
            direction = 'up' if cur > 0 else ('down' if cur < 0 else 'none')
            count = 1 if direction != 'none' else 0
            continue

        if cur > prev:
            if direction == 'down':
                if count >= threshold:
                    yield (i - count, i - 1, RunType.X_DECREASING, desc_down)
                direction = 'up'
                count = 1
            elif direction == 'up':
                count += 1
            else:
                direction = 'up'
                count = 1
        elif cur < prev:
            if direction == 'up':
                if count >= threshold:
                    yield (i - count, i - 1, RunType.X_INCREASING, desc_up)
                direction = 'down'
                count = 1
            elif direction == 'down':
                count += 1
            else:
                direction = 'down'
                count = 1
        else:
            if count >= threshold:
                run_type = (
                    RunType.X_INCREASING if direction == 'up' else RunType.X_DECREASING
                )
                desc = desc_up if direction == 'up' else desc_down
                yield (i - count, i - 1, run_type, desc)
            direction = 'none'
            count = 0

        if i == n - 1 and count >= threshold:
            run_type = (
                RunType.X_INCREASING if direction == 'up' else RunType.X_DECREASING
            )
            desc = desc_up if direction == 'up' else desc_down
            yield (i - count + 1, i, run_type, desc)

        prev = cur


def _sigma2_present(lim: dict[str, float]) -> bool:
    u, lo = lim.get('sigma_2_upper'), lim.get('sigma_2_lower')
    if u is None or lo is None:
        return False
    return is_finite(u) and is_finite(lo)


def _sigma1_present(lim: dict[str, float]) -> bool:
    u, lo = lim.get('sigma_1_upper'), lim.get('sigma_1_lower')
    if u is None or lo is None:
        return False
    return is_finite(u) and is_finite(lo)


def _runs_test5(
    values: list[float],
    control_limits_per_point: list[dict[str, float]],
    n: int,
) -> Iterator[_Run]:
    """Run test 5: 2 of 3 points beyond 2-sigma (one inside allowed). Yields runs.
    This is implemented as a state machine. Possible states are:
    "up", "down", "up_skipping", "down_skipping", "none".

    "Up"/"down", is a continuous series of type 5 errors, the previous value was above/below 2s line.
    "Up_skipping"/"down_skipping", we have a skipped point, the previous value was above/below 2s line
    but above/below the center line.
    None, previous value moved to another side of the center line or we just started.

    In plain english, the state is "up" or "down" as long as the value stays above or under the 2s line,
    "x_skipping" to allow skipping a single point. Run ends when to consecutive points not
    above or under the 2s line or we change to other side of the center line.

    State changes:
    - None -> up: current value > cl
    - None -> down: current value < cl
    - Up -> up_skipping: cl < current value < 2s line
    - Up -> none: current value < cl (check if we have long enough run and create error if needed)
    - Up_skipping -> up: current value > 2s line
    - Up_skipping -> none: current value < cl (check if we have long enough run and create error if needed)
    - Down -> down_skipping: cl > current value > 2s line
    - Down -> none: current value > cl (check if we have long enough run and create error if needed)
    - Down_skipping -> down: current value < 2s line
    - Down_skipping -> none: current value > cl (check if we have long enough run and create error if needed)
    """
    count = 0
    state: str = 'none'  # "up" | "down" | "up_skipping" | "down_skipping" | "none"
    desc_over = '2 of 3 points beyond +2 sigma'
    desc_under = '2 of 3 points beyond -2 sigma'

    for i in range(n):
        v = values[i]
        lim = _limits_at(control_limits_per_point, i, n)
        if not _sigma2_present(lim):
            state = 'none'
            count = 0
            continue
        cl = lim['center_line']
        s2u = lim['sigma_2_upper']
        s2l = lim['sigma_2_lower']

        if not is_finite(v):
            state = 'none'
            count = 0
            continue

        if v < s2l:
            if state == 'down':
                count += 1
            elif state == 'down_skipping':
                count += 1
                state = 'down'
            else:
                if state == 'up' and count >= 2:
                    yield (i - count, i - 1, RunType.X_OVER_2SIGMA, desc_over)
                elif state == 'up_skipping' and count >= 3:
                    yield (i - count + 1, i - 1, RunType.X_OVER_2SIGMA, desc_over)
                state = 'down'
                count = 1
        elif v < cl:
            if state == 'down':
                count += 1
                state = 'down_skipping'
            elif state in ('down_skipping', 'up_skipping'):
                if state == 'down_skipping' and count >= 3:
                    yield (i - count, i - 2, RunType.X_UNDER_2SIGMA, desc_under)
                elif state == 'up_skipping' and count >= 3:
                    yield (i - count, i - 2, RunType.X_OVER_2SIGMA, desc_over)
                state = 'none'
                count = 0
            elif state == 'up':
                if count >= 2:
                    yield (i - count, i - 1, RunType.X_OVER_2SIGMA, desc_over)
                state = 'none'
                count = 0
            else:
                state = 'none'
                count = 0
        elif v > s2u:
            if state == 'up':
                count += 1
            elif state == 'up_skipping':
                count += 1
                state = 'up'
            else:
                if state == 'down' and count >= 2:
                    yield (i - count, i - 1, RunType.X_UNDER_2SIGMA, desc_under)
                elif state == 'down_skipping' and count >= 3:
                    yield (i - count + 1, i - 1, RunType.X_UNDER_2SIGMA, desc_under)
                state = 'up'
                count = 1
        elif v > cl:
            if state == 'up':
                count += 1
                state = 'up_skipping'
            elif state in ('down_skipping', 'up_skipping'):
                if state == 'down_skipping' and count >= 3:
                    yield (i - count, i - 2, RunType.X_UNDER_2SIGMA, desc_under)
                elif state == 'up_skipping' and count >= 3:
                    yield (i - count, i - 2, RunType.X_OVER_2SIGMA, desc_over)
                state = 'none'
                count = 0
            elif state == 'down':
                if count >= 2:
                    yield (i - count, i - 1, RunType.X_UNDER_2SIGMA, desc_under)
                state = 'none'
                count = 0
            else:
                state = 'none'
                count = 0
        else:
            state = 'none'
            count = 0

        if i == n - 1:
            if (state in ('up', 'down') and count >= 2) or count >= 3:
                run_type = (
                    RunType.X_OVER_2SIGMA
                    if state in ('up', 'up_skipping')
                    else RunType.X_UNDER_2SIGMA
                )
                desc = desc_over if run_type == RunType.X_OVER_2SIGMA else desc_under
                yield (i - count + 1, i, run_type, desc)


def _runs_test6(
    values: list[float],
    control_limits_per_point: list[dict[str, float]],
    n: int,
) -> Iterator[_Run]:
    """Run test 6: 4 of 5 points beyond 1-sigma (one inside allowed). Yields runs.

    Test 6: 4 of 5 beyond 1-sigma, one point allowed inside. Same state machine with 1σ.
    See the documentation for _runs_test5 for the state machine details. The difference to test 5
    is that test 5 uses only three states up/down/none and skipping_point variable to indicate the
    one allowed point inside the 1s line (but on the same side of center line).
    """
    count = 0
    state: str = 'none'  # up | down | none
    skipped_point = False
    desc_over = '4 of 5 points beyond +1 sigma'
    desc_under = '4 of 5 points beyond -1 sigma'

    def reset_state():
        nonlocal state, count, skipped_point
        state = 'none'
        count = 0
        skipped_point = False

    for i in range(n):
        v = values[i]
        lim = _limits_at(control_limits_per_point, i, n)

        if not _sigma1_present(lim) or not is_finite(v):
            reset_state()
            continue

        cl = lim['center_line']
        s1u = lim['sigma_1_upper']
        s1l = lim['sigma_1_lower']

        if v <= s1l:
            if state == 'down':
                count += 1
            elif state == 'up' and count >= 5:
                yield (i - count, i - 1, RunType.X_OVER_1SIGMA, desc_over)
                reset_state()
            else:  # (none or up) reset state
                reset_state()
                state = 'down'
                count = 1
        elif v < cl:
            if state == 'down' and not skipped_point:
                count += 1
                skipped_point = True
            elif state == 'up' and count >= 5:
                yield (i - count, i - 1, RunType.X_OVER_1SIGMA, desc_over)
                reset_state()
            elif state == 'down' and count >= 5:  # skipped already a point
                yield (i - count, i - 1, RunType.X_UNDER_1SIGMA, desc_under)
                reset_state()
            else:  # (down & skipped a point, up, none)
                reset_state()
        elif v >= s1u:
            if state == 'up':
                count += 1
            elif state == 'down' and count >= 5:
                yield (i - count, i - 1, RunType.X_UNDER_1SIGMA, desc_under)
                reset_state()
            else:  # (down, none)
                reset_state()
                state = 'up'
                count = 1
        elif v > cl:
            if state == 'up' and not skipped_point:
                count += 1
                skipped_point = True
            elif state == 'down' and count >= 5:
                yield (i - count, i - 1, RunType.X_UNDER_1SIGMA, desc_under)
                reset_state()
            elif state == 'up' and count >= 5:  # skipped already a point
                yield (i - count, i - 1, RunType.X_OVER_1SIGMA, desc_over)
                reset_state()
            else:  # (up & skipped a point, up, none)
                reset_state()
        else:
            reset_state()

        if i == n - 1:  # catch the last one
            if state == 'up':
                if (count >= 4 and skipped_point is False) or (count >= 5):
                    yield (
                        i - count + 1,
                        i,
                        RunType.X_OVER_1SIGMA,
                        desc_over,
                    )  # +1 because we still on the same round
                    reset_state()
            elif state == 'down':
                if (count >= 4 and not skipped_point) or (count >= 5):
                    yield (
                        i - count + 1,
                        i,
                        RunType.X_UNDER_1SIGMA,
                        desc_under,
                    )  # +1 because we still on the same round
                    reset_state()
            else:
                reset_state()


def _apply_run_tests_to_slice(
    values: list[float],
    control_limits_per_point: list[dict[str, float]],
    config: RunTestConfig,
) -> list[list[dict]]:
    """
    Apply run tests to a single contiguous slice (e.g. one phase).
    Marks every point in each run, matching the TypeScript implementation.
    """
    n = len(values)
    violations: list[list[dict]] = [[] for _ in range(n)]

    def add_run(start: int, end_incl: int, run_type: int, description: str) -> None:
        v = create_violation_dict(run_type, description)
        for idx in range(start, end_incl + 1):
            if 0 <= idx < n:
                violations[idx].append(v)

    if config.test1:
        for start, end_incl, run_type, desc in _runs_test1(
            values, control_limits_per_point, n
        ):
            add_run(start, end_incl, run_type, desc)

    if config.test2:
        for start, end_incl, run_type, desc in _runs_test2(
            values, control_limits_per_point, n, config.test2_n
        ):
            add_run(start, end_incl, run_type, desc)

    if config.test3:
        for start, end_incl, run_type, desc in _runs_test3(values, n, config.test3_n):
            add_run(start, end_incl, run_type, desc)

    if config.test5:
        for start, end_incl, run_type, desc in _runs_test5(
            values, control_limits_per_point, n
        ):
            add_run(start, end_incl, run_type, desc)

    if config.test6:
        for start, end_incl, run_type, desc in _runs_test6(
            values, control_limits_per_point, n
        ):
            add_run(start, end_incl, run_type, desc)

    return violations


def apply_run_tests(
    values: list[float],
    control_limits_per_point: list[dict[str, float]],
    config: RunTestConfig | None,
    phase_boundaries: list[tuple[int, int, Any]] | None = None,
) -> list[list[dict]]:
    """
    Apply run tests to all points and return violations list.

    When phase_boundaries is provided with more than one phase, run tests
    are evaluated separately within each phase (sliding windows do not
    cross phase boundaries). Every point in a run is marked with the violation,
    matching the TypeScript SPC implementation.

    Args:
        values: List of data values
        control_limits_per_point: Control limits for each point
        config: Run test configuration (None to disable)
        phase_boundaries: Optional list of (start, end, label) per phase.
            When None or a single phase, one pass over all data.
            When multiple phases, run tests are applied per phase.

    Returns:
        List of violation lists (one per point)
    """
    if config is None:
        return [[] for _ in range(len(values))]

    if phase_boundaries is None or len(phase_boundaries) <= 1:
        return _apply_run_tests_to_slice(values, control_limits_per_point, config)

    all_violations = []
    for start, end, _ in phase_boundaries:
        phase_values = values[start:end]
        phase_limits = control_limits_per_point[start:end]
        all_violations.extend(
            _apply_run_tests_to_slice(phase_values, phase_limits, config)
        )
    return all_violations


def _custom_limits_to_dict(
    limits: CustomLimits | dict[str, Any],
) -> dict[str, float]:
    """
    Convert CustomLimits or dict to the 7-key limit dict for run tests and output.

    Missing sigma values are set to float('nan'); run-test logic skips test5/test6
    when sigma is NaN.
    """
    nan = float('nan')
    if isinstance(limits, CustomLimits):
        return {
            'center_line': limits.center_line,
            'ucl': limits.ucl,
            'lcl': limits.lcl,
            'sigma_1_upper': limits.sigma_1_upper
            if limits.sigma_1_upper is not None
            else nan,
            'sigma_1_lower': limits.sigma_1_lower
            if limits.sigma_1_lower is not None
            else nan,
            'sigma_2_upper': limits.sigma_2_upper
            if limits.sigma_2_upper is not None
            else nan,
            'sigma_2_lower': limits.sigma_2_lower
            if limits.sigma_2_lower is not None
            else nan,
        }
    d = limits
    return {
        'center_line': float(d['center_line']),
        'ucl': float(d['ucl']),
        'lcl': float(d['lcl']),
        'sigma_1_upper': float(d['sigma_1_upper'])
        if d.get('sigma_1_upper') is not None
        else nan,
        'sigma_1_lower': float(d['sigma_1_lower'])
        if d.get('sigma_1_lower') is not None
        else nan,
        'sigma_2_upper': float(d['sigma_2_upper'])
        if d.get('sigma_2_upper') is not None
        else nan,
        'sigma_2_lower': float(d['sigma_2_lower'])
        if d.get('sigma_2_lower') is not None
        else nan,
    }


def _custom_limits_to_control_limits(
    limits: CustomLimits | dict[str, Any],
    n_points: int,
) -> list[dict[str, float]]:
    """Return a list of n_points identical main-chart limit dicts."""
    one = _custom_limits_to_dict(limits)
    return [dict(one) for _ in range(n_points)]


def _has_variation_limits(limits: CustomLimits | dict[str, Any]) -> bool:
    """Return True if limits define all three variation chart limits."""
    if isinstance(limits, CustomLimits):
        return (
            limits.variation_ucl is not None
            and limits.variation_cl is not None
            and limits.variation_lcl is not None
        )
    d = limits
    return (
        d.get('variation_ucl') is not None
        and d.get('variation_cl') is not None
        and d.get('variation_lcl') is not None
    )


def _get_spec_from_limits(
    limits: CustomLimits | dict[str, Any],
    n_points: int,
) -> tuple[list[float], list[float]]:
    """Return (spec_upper_list, spec_lower_list) from limits; NaN when not set."""
    nan = float('nan')
    if isinstance(limits, CustomLimits):
        su = limits.spec_upper
        sl = limits.spec_lower
    else:
        d = limits
        su = d.get('spec_upper')
        sl = d.get('spec_lower')
    spec_upper = [float(su)] * n_points if su is not None else [nan] * n_points
    spec_lower = [float(sl)] * n_points if sl is not None else [nan] * n_points
    return spec_upper, spec_lower


def run_tests_with_custom_limits(
    data: list[float] | pd.Series | pd.DataFrame,
    *,
    limits: CustomLimits | dict[str, Any],
    value_column: str | None = None,
    label: str | list | None = None,
    run_tests: RunTestConfig = RunTestConfig(),
) -> pd.DataFrame:
    """
    Run run tests against custom limits and return a standardized DataFrame.

    No limit calculation from data; limits are taken from the provided
    CustomLimits or dict. When sigma lines are not set on limits, output
    sigma columns are NaN and run tests 5 and 6 are not performed. Empty
    data returns an empty DataFrame with the same column schema.

    Args:
        data: Values to evaluate (list, Series, or DataFrame; use value_column
            when DataFrame).
        limits: Custom limits (main chart; optional spec and variation chart).
        value_column: Column name for values when data is DataFrame; omit
            when data is list or Series.
        label: Column name (when data is DataFrame) or list of labels; omit
            for default labels 1, 2, ..., n.
        run_tests: Which run tests to apply (default: all enabled).

    Raises:
        ValueError: If data is DataFrame and value_column is missing or not a column,
            or if a given column name is not found or list lengths do not match.
        TypeError: If data is not a list, Series, or DataFrame.

    Returns:
        DataFrame with point_id, value, label, limits, spec_upper, spec_lower,
        phase (None), violations; optional variation columns when limits
        set variation_ucl, variation_cl, variation_lcl.
    """
    values, labels, _ = normalize_simple_input(data, value_column, label, None)
    n_points = len(values)

    if n_points == 0:
        return create_empty_chart_dataframe(
            include_variation=_has_variation_limits(limits)
        )

    control_limits_per_point = _custom_limits_to_control_limits(limits, n_points)
    violations = apply_run_tests(
        values, control_limits_per_point, run_tests, phase_boundaries=None
    )
    spec_upper_list, spec_lower_list = _get_spec_from_limits(limits, n_points)

    variation_values: list[float | None] | None = None
    variation_limits: list[dict[str, float]] | None = None
    variation_violations: list[list[dict]] | None = None

    if _has_variation_limits(limits):
        mr_list = calc_moving_range(values)
        nan = float('nan')
        if isinstance(limits, CustomLimits):
            v_ucl, v_cl, v_lcl = (
                limits.variation_ucl,
                limits.variation_cl,
                limits.variation_lcl,
            )
        else:
            d = limits
            v_ucl = d['variation_ucl']
            v_cl = d['variation_cl']
            v_lcl = d['variation_lcl']
        variation_values = [mr if mr is not None else nan for mr in mr_list]
        var_limit_dict = {
            'ucl': float(v_ucl),
            'sigma_2_upper': nan,
            'sigma_1_upper': nan,
            'center_line': float(v_cl),
            'sigma_1_lower': nan,
            'sigma_2_lower': nan,
            'lcl': float(v_lcl),
        }
        variation_limits = [dict(var_limit_dict) for _ in range(n_points)]
        variation_violations = apply_run_tests(
            variation_values,
            variation_limits,
            run_tests,
            phase_boundaries=None,
        )

    return build_output_dataframe(
        values=values,
        labels=labels,
        control_limits=control_limits_per_point,
        phases=None,
        spec_upper=spec_upper_list,
        spec_lower=spec_lower_list,
        violations=violations,
        variation_values=variation_values,
        variation_limits=variation_limits,
        variation_violations=variation_violations,
    )
