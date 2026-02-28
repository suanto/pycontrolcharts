# API Reference

Detailed reference for the public API of pycontrolcharts. For getting started and usage patterns, see the [User guide](USER_GUIDE.md).

---

## Output DataFrame schema

Every `calc_*` function returns a pandas DataFrame with a standardized set of columns. Column presence depends on chart type (variables charts include variation columns; attribute charts do not).

### Core columns (all charts)

| Column          | Type        | Description / expected values |
|-----------------|-------------|-------------------------------|
| `point_id`     | `int`       | Sequential index 0, 1, 2, ... |
| `value`        | `float`     | The plotted statistic: individual measurement (XmR), subgroup mean (X-bar), proportion (p), or count (np, c, u) |
| `label`        | any         | X-axis label; type matches input (e.g. str, int, datetime) |
| `ucl`          | `float`     | Upper control limit |
| `sigma_2_upper` | `float`     | Upper 2-sigma line |
| `sigma_1_upper` | `float`     | Upper 1-sigma line |
| `center_line`  | `float`     | Process center line |
| `sigma_1_lower`  | `float`     | Lower 1-sigma line |
| `sigma_2_lower`  | `float`     | Lower 2-sigma line |
| `lcl`          | `float`     | Lower control limit |
| `spec_upper`   | `float`     | Upper specification limit; **NaN** when not provided |
| `spec_lower`   | `float`     | Lower specification limit; **NaN** when not provided |
| `phase`        | `str` or None | Phase label; **None** when no phase column/list was passed |
| `violations`   | `list` of dict | Run-test violations at this point; **empty list `[]`** when none. See [Violation item schema](#violation-item-schema). |

### Variables charts only (XmR, X-bar/R, X-bar/S)

| Column                 | Type        | Description / expected values |
|------------------------|-------------|-------------------------------|
| `variation`            | `float`     | Moving range (XmR), subgroup range (X-bar/R), or subgroup std dev (X-bar/S). May be None for first point (XmR). |
| `variation_ucl`        | `float`     | Upper control limit for variation chart |
| `variation_cl`         | `float`     | Center line for variation chart |
| `variation_lcl`        | `float`     | Lower control limit for variation chart |
| `variation_violations` | `list` of dict | Same schema as `violations`; run-test violations on the variation chart. Empty list when none. |

### Violation item schema

Each element of `violations` (and `variation_violations`) is a dict:

- **`type`** (`int`): Run-test type code. Values 1–10 correspond to the `RunType` enum (see [RunType](#runtype)).
- **`description`** (`str`): Human-readable description of the violation (e.g. `"Point beyond upper control limit"`, `"9 consecutive points above center line"`). The text may include the run length N when relevant.

Example: `{"type": 1, "description": "Point beyond upper control limit"}`.

---

## Chart functions

All chart functions accept list, pandas Series, or DataFrame input (DataFrame requires the appropriate column-name arguments). Common parameters:

- **label**: Column name or list for x-axis labels.
- **phase**: Column name or list for phase labels (multi-phase analysis).
- **spec_upper** / **spec_lower**: Float (broadcast), list of floats (per point), or column name (str).
- **run_tests**: `True` (default, all tests), `False` (no tests), or a `RunTestConfig` instance.

Return value: pandas DataFrame with the [output schema](#output-dataframe-schema) above. **Empty input** (empty list/Series/DataFrame or no subgroups): each `calc_*` returns an empty DataFrame with the same column schema (no rows).

**Raises (all chart functions):**

- **ValueError** — When `data` is a DataFrame and `value_column` is missing or not a column name; when a given column name (`value_column`, `label`, `phase`, `spec_upper`/`spec_lower` as column name) is not found in the DataFrame; when `label`, `phase`, or spec limit list lengths do not match the data length. For **calc_xbar_r** and **calc_xbar_s**: when neither `subgroup_size` nor `subgroup` is provided, or when subgroup size is less than 2, or when `subgroup` is used with non-DataFrame input and lengths do not match.
- **TypeError** — When `data` is not a list, Series, or DataFrame; when `subgroup` is used with list/Series input (DataFrame required for `subgroup`).

---

### calc_xmr

```python
def calc_xmr(
    data: list | pd.Series | pd.DataFrame,
    *,
    value_column: str | None = None,
    label: str | list | None = None,
    phase: str | list | None = None,
    spec_upper: float | list[float] | str | None = None,
    spec_lower: float | list[float] | str | None = None,
    run_tests: bool | RunTestConfig = True,
) -> pd.DataFrame
```

**XmR (Individuals and Moving Range)** — One row per individual measurement.

| Parameter       | Required for DataFrame? | Description |
|-----------------|--------------------------|-------------|
| `data`          | —                        | List of values, Series, or DataFrame |
| `value_column`  | Yes                      | Column name for the measurement values |
| `label`         | No                       | X-axis labels |
| `phase`         | No                       | Phase labels |
| `spec_upper`    | No                       | Upper specification limit(s) |
| `spec_lower`    | No                       | Lower specification limit(s) |
| `run_tests`     | No                       | Run test configuration |

**Returns:** DataFrame with core columns plus `variation`, `variation_ucl`, `variation_cl`, `variation_lcl`, `variation_violations` (moving range chart).

---

### calc_xbar_r

```python
def calc_xbar_r(
    data: list | pd.Series | pd.DataFrame,
    *,
    subgroup_size: int | None = None,
    subgroup: str | None = None,
    value_column: str | None = None,
    label: str | list | None = None,
    phase: str | list | None = None,
    spec_upper: float | list[float] | str | None = None,
    spec_lower: float | list[float] | str | None = None,
    run_tests: bool | RunTestConfig = True,
) -> pd.DataFrame
```

**X-bar and R (Mean and Range)** — One row per subgroup. Requires either fixed `subgroup_size` or a `subgroup` column for variable-size subgroups.

| Parameter       | Required for DataFrame? | Description |
|-----------------|--------------------------|-------------|
| `data`          | —                        | Flat list/Series of values, or DataFrame with value + optional subgroup column |
| `subgroup_size` | Yes (or `subgroup`)      | Integer; fixed subgroup size (e.g. 5). Mutually exclusive with `subgroup`. |
| `subgroup`      | No                       | Column name that identifies subgroup (e.g. batch ID). Mutually exclusive with `subgroup_size`. |
| `value_column`  | Yes (DataFrame)          | Column name for measurements |
| `label`         | No                       | X-axis labels (one per subgroup) |
| `phase`         | No                       | Phase labels (one per subgroup) |
| `spec_upper`    | No                       | Upper specification limit(s) |
| `spec_lower`    | No                       | Lower specification limit(s) |
| `run_tests`     | No                       | Run test configuration |

**Returns:** DataFrame with core columns plus variation columns (`variation` = subgroup range, etc.).

---

### calc_xbar_s

```python
def calc_xbar_s(
    data: list | pd.Series | pd.DataFrame,
    *,
    subgroup_size: int | None = None,
    subgroup: str | None = None,
    value_column: str | None = None,
    label: str | list | None = None,
    phase: str | list | None = None,
    spec_upper: float | list[float] | str | None = None,
    spec_lower: float | list[float] | str | None = None,
    run_tests: bool | RunTestConfig = True,
) -> pd.DataFrame
```

**X-bar and S (Mean and Standard Deviation)** — One row per subgroup. Same parameters as `calc_xbar_r`; `variation` column holds subgroup standard deviation. Recommended when subgroup size ≥ 10.

---

### calc_p

```python
def calc_p(
    data: list | pd.Series | pd.DataFrame,
    *,
    sample_size_column: str | None = None,
    value_column: str | None = None,
    sample_size: int | list[int] | str | None = None,
    label: str | list | None = None,
    phase: str | list | None = None,
    spec_upper: float | list[float] | str | None = None,
    spec_lower: float | list[float] | str | None = None,
    run_tests: bool | RunTestConfig = True,
) -> pd.DataFrame
```

**p-chart (Proportion defective)** — One row per sample. `value` is proportion defective (defect count / sample size). Supports variable or constant sample size.

| Parameter             | Required for DataFrame? | Description |
|-----------------------|--------------------------|-------------|
| `data`                | —                        | Defect counts: list, Series, or DataFrame |
| `sample_size_column`  | No (or constant `sample_size`) | Column name for sample sizes |
| `value_column`        | Yes (DataFrame)          | Column name for number of defectives |
| `sample_size`         | Yes (or `sample_size_column`) | Constant int, list of ints, or column name (str) |
| `label`               | No                       | X-axis labels |
| `phase`               | No                       | Phase labels |
| `spec_upper` / `spec_lower` | No                  | Specification limits |
| `run_tests`           | No                       | Run test configuration |

---

### calc_np

```python
def calc_np(
    data: list | pd.Series | pd.DataFrame,
    *,
    value_column: str | None = None,
    sample_size: int,
    label: str | list | None = None,
    phase: str | list | None = None,
    spec_upper: float | list[float] | str | None = None,
    spec_lower: float | list[float] | str | None = None,
    run_tests: bool | RunTestConfig = True,
) -> pd.DataFrame
```

**np-chart (Number defective)** — One row per sample; constant sample size only. `value` is the count of defectives (integer conceptually; stored as float in DataFrame).

| Parameter     | Required | Description |
|---------------|----------|-------------|
| `data`        | Yes      | Defect counts: list, Series, or DataFrame |
| `value_column` | Yes (DataFrame) | Column name for defect counts |
| `sample_size` | Yes      | Constant integer sample size for all samples |
| `label`       | No       | X-axis labels |
| `phase`       | No       | Phase labels |
| `spec_upper` / `spec_lower` | No | Specification limits |
| `run_tests`   | No       | Run test configuration |

---

### calc_c

```python
def calc_c(
    data: list | pd.Series | pd.DataFrame,
    *,
    value_column: str | None = None,
    label: str | list | None = None,
    phase: str | list | None = None,
    spec_upper: float | list[float] | str | None = None,
    spec_lower: float | list[float] | str | None = None,
    run_tests: bool | RunTestConfig = True,
) -> pd.DataFrame
```

**c-chart (Count of defects)** — One row per sample; constant area of opportunity. `value` is the defect count per unit/sample.

| Parameter     | Required for DataFrame? | Description |
|---------------|--------------------------|-------------|
| `data`        | —                        | Defect counts: list, Series, or DataFrame |
| `value_column` | Yes (DataFrame)         | Column name for defect counts |
| `label`       | No                       | X-axis labels |
| `phase`       | No                       | Phase labels |
| `spec_upper` / `spec_lower` | No                | Specification limits |
| `run_tests`   | No                       | Run test configuration |

---

### calc_u

```python
def calc_u(
    data: list | pd.Series | pd.DataFrame,
    *,
    area_column: str | None = None,
    value_column: str | None = None,
    area: int | list[int] | str | None = None,
    label: str | list | None = None,
    phase: str | list | None = None,
    spec_upper: float | list[float] | str | None = None,
    spec_lower: float | list[float] | str | None = None,
    run_tests: bool | RunTestConfig = True,
) -> pd.DataFrame
```

**u-chart (Defects per unit)** — One row per sample; variable or constant area of opportunity. `value` is defects per unit (defects / area).

| Parameter       | Required for DataFrame? | Description |
|-----------------|--------------------------|-------------|
| `data`          | —                        | Defect counts: list, Series, or DataFrame |
| `area_column`   | No (or constant `area`)  | Column name for area of opportunity |
| `value_column`  | Yes (DataFrame)          | Column name for defect counts |
| `area`          | Yes (or `area_column`)   | Constant int, list of ints, or column name (str) |
| `label`         | No                       | X-axis labels |
| `phase`         | No                       | Phase labels |
| `spec_upper` / `spec_lower` | No                  | Specification limits |
| `run_tests`     | No                       | Run test configuration |

---

## run_tests_with_custom_limits

Run run tests against **custom limits** (no limit calculation from data). Use when you have your own control limits and only need violation detection and the standardized output DataFrame.

```python
def run_tests_with_custom_limits(
    data: list[float] | pd.Series | pd.DataFrame,
    *,
    limits: CustomLimits | dict,
    value_column: str | None = None,
    label: str | list | None = None,
    run_tests: RunTestConfig = RunTestConfig(),
) -> pd.DataFrame
```

| Parameter       | Type | Default | Description |
|-----------------|------|---------|-------------|
| `data`          | list, Series, or DataFrame | — | Values to evaluate. Use `value_column` when DataFrame. |
| `limits`        | `CustomLimits` or dict | — | Custom limits (main chart; optional spec and variation). See [CustomLimits](#customlimits). |
| `value_column`  | str | — | Column name for values when `data` is DataFrame; omit for list/Series. |
| `label`         | str or list | — | Column name (DataFrame) or list of labels; omit for default 1, 2, ..., n. |
| `run_tests`     | `RunTestConfig` | `RunTestConfig()` | Which run tests to apply. To disable all: `RunTestConfig(test1=False, test2=False, test3=False, test5=False, test6=False)`. |

- **Sigma lines**: When sigma fields are not set on `limits`, output sigma columns are NaN and **run tests 5 and 6 are not performed** (the run-test logic skips them when sigma is missing).
- **Empty data**: Returns an empty DataFrame with the same column schema (no variation columns unless variation limits are set).
- **Returns**: Same [output schema](#output-dataframe-schema) as `calc_*` (core columns; optional variation columns when `limits` set `variation_ucl`, `variation_cl`, `variation_lcl`). `phase` is always `None`.
- **Raises**: **ValueError** if `data` is a DataFrame and `value_column` is missing or not a column, or if a given column name is not found or list lengths do not match. **TypeError** if `data` is not a list, Series, or DataFrame.

Example:

```python
from pycontrolcharts import run_tests_with_custom_limits, CustomLimits, RunTestConfig

limits = CustomLimits(center_line=10.0, ucl=15.0, lcl=5.0, spec_upper=20.0, spec_lower=0.0)
df = run_tests_with_custom_limits([9, 11, 14, 16, 10], limits=limits, run_tests=RunTestConfig())
```

---

## CustomLimits

Dataclass for custom control limits (no derivation from data). Used by `run_tests_with_custom_limits`. All main-chart limits are required; sigma lines, spec, and variation chart are optional.

**Dict form:** When passing a plain `dict` instead of `CustomLimits`, use the same keys as the dataclass attributes. Required: `center_line`, `ucl`, `lcl`. Optional: `sigma_1_upper`, `sigma_1_lower`, `sigma_2_upper`, `sigma_2_lower`, `spec_upper`, `spec_lower`, `variation_ucl`, `variation_cl`, `variation_lcl`. Any optional key not present is treated as not set (e.g. sigma columns will be NaN and run tests 5/6 are skipped if sigma keys are omitted).

**Main chart (required)**

| Field | Type | Description |
|-------|------|-------------|
| `center_line` | float | Process center line |
| `ucl` | float | Upper control limit |
| `lcl` | float | Lower control limit |

**Main chart (optional — sigma lines)**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sigma_1_upper` | float or None | None | Upper 1σ; when not set, output is NaN and **test 6** is not performed |
| `sigma_1_lower` | float or None | None | Lower 1σ; when not set, output is NaN and **test 6** is not performed |
| `sigma_2_upper` | float or None | None | Upper 2σ; when not set, output is NaN and **test 5** is not performed |
| `sigma_2_lower` | float or None | None | Lower 2σ; when not set, output is NaN and **test 5** is not performed |

**Spec limits (optional, single value each)**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `spec_upper` | float or None | None | Upper specification limit (one value for all points) |
| `spec_lower` | float or None | None | Lower specification limit (one value for all points) |

**Variation chart (optional)** — When all three are set, variation is computed as moving range and variation columns/violations are included.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `variation_ucl` | float or None | None | UCL for variation chart |
| `variation_cl` | float or None | None | Center line for variation chart |
| `variation_lcl` | float or None | None | LCL for variation chart |

`limits` may also be a dict with at least `center_line`, `ucl`, `lcl` (and optionally the keys above).

---

## plot_control_chart

```python
def plot_control_chart(
    chart_df: pd.DataFrame,
    chart_type: ChartType | str,
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
) -> plotly.graph_objects.Figure
```

Builds a Plotly figure from a DataFrame returned by one of the `calc_*` functions. Requires: `pip install pycontrolcharts[plotly]`.

| Parameter         | Type     | Default | Description |
|-------------------|----------|---------|-------------|
| `chart_df`        | DataFrame | —     | Output of a `calc_*` function |
| `chart_type`      | `ChartType` or str | — | One of: `XMR`, `XBAR_R`, `XBAR_S`, `P`, `NP`, `C`, `U` (or lowercase strings e.g. `"xmr"`) |
| `title`           | str or None | None | Figure title; default is chart-type-based |
| `show_variation`  | bool     | True   | For XmR/X-bar/R/X-bar/S: draw variation chart below. Ignored for attribute charts. |
| `show_sigma_1_lines`| bool     | False  | Draw ±1σ lines |
| `show_sigma_2_lines`| bool     | False  | Draw ±2σ lines |
| `show_spec_lines`| bool     | False   | Draw spec_upper/spec_lower if present in DataFrame |
| `show_legend`     | bool     | False  | Show legend |
| `show_limit_labels` | bool   | True   | Draw the numeric value at the end of each limit line (UCL, LCL, center, etc.) |
| `limit_label_precision` | int | 2 | Decimal places for limit labels |
| `force_y_axis_to_zero` | bool | False | Force the main panel y-axis to include zero |
| `height`          | int or None | None | Plot height in pixels |
| `width`           | int or None | None | Plot width in pixels |
| `layout`          | dict or None | None | Merged into figure layout (`fig.update_layout(**layout)`) |

**Returns:** `plotly.graph_objects.Figure`. Use `.show()` or `.write_html(...)` as needed.

**Multi-phase:** When `chart_df` has multiple phases (e.g. different `phase` values), the plotter draws control limits as step lines at phase boundaries so each phase shows its own limits.

**Raises:** `ImportError` if plotly is not installed; `ValueError` if DataFrame is empty or missing required columns; `NotImplementedError` if `chart_type` is not supported.

---

## RunType

Enum of run-test violation type codes. Used as the integer `type` in each violation dict in the `violations` and `variation_violations` columns.

| Value | Member           | Description |
|-------|------------------|-------------|
| 1     | `OVER_UCL`       | Point beyond upper control limit |
| 2     | `UNDER_LCL`      | Point beyond lower control limit |
| 3     | `X_OVER_AVG`     | N consecutive points above center line |
| 4     | `X_UNDER_AVG`    | N consecutive points below center line |
| 5     | `X_INCREASING`   | N consecutive increasing points |
| 6     | `X_DECREASING`   | N consecutive decreasing points |
| 7     | `X_OVER_2SIGMA`  | 2 of 3 points beyond +2σ |
| 8     | `X_UNDER_2SIGMA` | 2 of 3 points beyond -2σ |
| 9     | `X_UNDER_1SIGMA` | 4 of 5 points beyond -1σ |
| 10    | `X_OVER_1SIGMA`  | 4 of 5 points beyond +1σ |

Usage: `from pycontrolcharts import RunType`; compare `v["type"] == RunType.OVER_UCL` when inspecting violations.

---

## RunTestConfig

Dataclass to configure which run tests are applied and their thresholds. Pass to any `calc_*` function as `run_tests=RunTestConfig(...)`.

| Attribute  | Type | Default | Description |
|------------|------|---------|-------------|
| `test1`    | bool | True    | Points beyond control limits |
| `test2`    | bool | True    | N consecutive points on same side of center |
| `test3`    | bool | True    | N consecutive increasing or decreasing |
| `test5`    | bool | True    | 2 of 3 points beyond 2-sigma |
| `test6`    | bool | True    | 4 of 5 points beyond 1-sigma |
| `test2_n`   | int  | 9       | N for test 2 (e.g. 8 for Western Electric) |
| `test3_n`   | int  | 6       | N for test 3 (consecutive trend) |

Example:

```python
from pycontrolcharts import calc_xmr, RunTestConfig

config = RunTestConfig(test2_n=8, test5=False)
df = calc_xmr(data, run_tests=config)
```

---

## ChartType

Enum of supported chart types for `plot_control_chart`. Can also pass the string value (e.g. `"xmr"`).

| Member   | Value     | Description |
|----------|-----------|-------------|
| `XMR`    | `"xmr"`   | Individuals and Moving Range |
| `XBAR_R` | `"xbar_r"`| X-bar and R |
| `XBAR_S` | `"xbar_s"`| X-bar and S |
| `P`      | `"p"`     | p-chart (proportion defective) |
| `NP`     | `"np"`    | np-chart (number defective) |
| `C`      | `"c"`     | c-chart (count of defects) |
| `U`      | `"u"`     | u-chart (defects per unit) |

Example: `plot_control_chart(df, ChartType.XMR, title="Pressure")`.
