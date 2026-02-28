"""
Input handlers for normalizing various input formats to standard internal format.

This module provides utilities to convert pandas DataFrames, lists, and Series
into a standardized internal representation for chart calculations.
"""

from typing import Any
import pandas as pd


def normalize_simple_input(
    data: list | pd.Series | pd.DataFrame,
    value_column: str | None = None,
    label: str | list | None = None,
    phase: str | list | None = None,
) -> tuple[list[float], list[Any], list[str] | None]:
    """
    Normalize input data to standard format: (values, labels, phases).

    Args:
        data: Input data (list, Series, or DataFrame)
        value_column: Column name for values (required if DataFrame)
        label: Column name or list for labels
        phase: Column name or list for phase labels

    Returns:
        Tuple of (values, labels, phases)
        - values: list of float
        - labels: list of labels (1, 2, …, n if not provided)
        - phases: list of phase labels or None

    Raises:
        ValueError: If input is invalid
        TypeError: If unsupported data type is provided
    """
    # Handle DataFrame input
    if isinstance(data, pd.DataFrame):
        if value_column is None:
            raise ValueError('value_column parameter required when data is a DataFrame')

        if value_column not in data.columns:
            raise ValueError(f"Column '{value_column}' not found in DataFrame")

        values = data[value_column].tolist()

        # Extract labels
        if isinstance(label, str):
            if label not in data.columns:
                raise ValueError(f"Column '{label}' not found in DataFrame")
            labels = data[label].tolist()
        elif isinstance(label, list):
            if len(label) != len(values):
                raise ValueError(
                    f'label list length ({len(label)}) must match data length ({len(values)})'
                )
            labels = label
        else:
            labels = list(range(1, len(values) + 1))

        # Extract phases
        if isinstance(phase, str):
            if phase not in data.columns:
                raise ValueError(f"Column '{phase}' not found in DataFrame")
            phases = data[phase].tolist()
        elif isinstance(phase, list):
            if len(phase) != len(values):
                raise ValueError(
                    f'phase list length ({len(phase)}) must match data length ({len(values)})'
                )
            phases = phase
        else:
            phases = None

        return values, labels, phases

    # Handle Series input
    if isinstance(data, pd.Series):
        values = data.tolist()

        # Use Series index as labels if available
        if label is None:
            labels = data.index.tolist()
        elif isinstance(label, list):
            if len(label) != len(values):
                raise ValueError(
                    f'label list length ({len(label)}) must match data length ({len(values)})'
                )
            labels = label
        else:
            labels = list(range(1, len(values) + 1))

        # Handle phases
        if isinstance(phase, list):
            if len(phase) != len(values):
                raise ValueError(
                    f'phase list length ({len(phase)}) must match data length ({len(values)})'
                )
            phases = phase
        else:
            phases = None

        return values, labels, phases

    # Handle dict input - raise helpful error
    if isinstance(data, dict):
        raise TypeError(
            'Dict input is no longer supported. Use a pandas DataFrame instead:\n'
            "  df = pd.DataFrame({'value': [...], 'label': [...]})\n"
            "  chart_function(df, value_column='value', label='label')"
        )

    # Handle list input
    if isinstance(data, list):
        values = data

        # Handle labels
        if isinstance(label, list):
            if len(label) != len(values):
                raise ValueError(
                    f'label list length ({len(label)}) must match data length ({len(values)})'
                )
            labels = label
        else:
            labels = list(range(1, len(values) + 1))

        # Handle phases
        if isinstance(phase, list):
            if len(phase) != len(values):
                raise ValueError(
                    f'phase list length ({len(phase)}) must match data length ({len(values)})'
                )
            phases = phase
        else:
            phases = None

        return values, labels, phases

    raise TypeError(f'Unsupported data type: {type(data)}')


def normalize_dual_input(
    data: list | pd.Series | pd.DataFrame,
    data1_column: str | None,
    data2_column: str | None,
    value_column: str | None,
    data2_value: int | list[int] | str | None,
    label: str | list | None = None,
    phase: str | list | None = None,
) -> tuple[list[float], list[float] | int, list[Any], list[str] | None]:
    """
    Normalize input for charts requiring two data series (e.g., p-chart, u-chart).

    Args:
        data: Input data (list, Series, or DataFrame)
        data1_column: First series column name (for DataFrame)
        data2_column: Second series column name (for DataFrame)
        value_column: Alternative name for data1_column (for DataFrame)
        data2_value: Second series as int (constant), list (variable), or str (column name)
        label: Column name or list for labels
        phase: Column name or list for phase labels

    Returns:
        Tuple of (values1, values2, labels, phases)
        - labels: list of labels (1, 2, …, n if not provided)

    Raises:
        ValueError: If input is invalid
        TypeError: If unsupported data type is provided
    """
    # Handle dict input - raise helpful error
    if isinstance(data, dict):
        raise TypeError(
            'Dict input is no longer supported. Use a pandas DataFrame instead:\n'
            "  df = pd.DataFrame({'defectives': [...], 'sample_size': [...]})\n"
            "  chart_function(df, value_column='defectives', sample_size_column='sample_size')"
        )

    # Handle DataFrame input
    if isinstance(data, pd.DataFrame):
        # Determine which column name to use for data1
        col1 = data1_column or value_column
        if col1 is None:
            raise ValueError(
                'Either data1_column or value_column must be specified when data is a DataFrame'
            )

        # Get first series
        if col1 not in data.columns:
            raise ValueError(f"Column '{col1}' not found in DataFrame")
        values1 = data[col1].tolist()

        # Get second series - can be from column or from data2_value parameter
        if data2_column is not None:
            # From DataFrame column
            if data2_column not in data.columns:
                raise ValueError(f"Column '{data2_column}' not found in DataFrame")
            values2 = data[data2_column].tolist()
        elif isinstance(data2_value, str):
            # Column name passed as data2_value
            if data2_value not in data.columns:
                raise ValueError(f"Column '{data2_value}' not found in DataFrame")
            values2 = data[data2_value].tolist()
        elif isinstance(data2_value, int):
            # Constant value
            values2 = data2_value
        elif isinstance(data2_value, list):
            # List of values
            if len(data2_value) != len(values1):
                raise ValueError('data2_value list length must match data length')
            values2 = data2_value
        else:
            raise ValueError(
                'data2_column or data2_value must be provided when data is a DataFrame'
            )

        # Extract labels
        if isinstance(label, str):
            if label not in data.columns:
                raise ValueError(f"Column '{label}' not found in DataFrame")
            labels = data[label].tolist()
        elif isinstance(label, list):
            if len(label) != len(values1):
                raise ValueError('label list length must match data length')
            labels = label
        else:
            labels = list(range(1, len(values1) + 1))

        # Extract phases
        if isinstance(phase, str):
            if phase not in data.columns:
                raise ValueError(f"Column '{phase}' not found in DataFrame")
            phases = data[phase].tolist()
        elif isinstance(phase, list):
            if len(phase) != len(values1):
                raise ValueError('phase list length must match data length')
            phases = phase
        else:
            phases = None

        return values1, values2, labels, phases

    # Handle Series input
    if isinstance(data, pd.Series):
        values1 = data.tolist()

        # Get second series from data2_value parameter
        if isinstance(data2_value, int):
            values2 = data2_value
        elif isinstance(data2_value, list):
            if len(data2_value) != len(values1):
                raise ValueError('data2_value list length must match data length')
            values2 = data2_value
        else:
            raise ValueError(
                'data2_value (sample_size/area) must be provided when data is a Series'
            )

        # Handle labels
        if isinstance(label, list):
            if len(label) != len(values1):
                raise ValueError('label list length must match data length')
            labels = label
        else:
            labels = list(range(1, len(values1) + 1))

        # Handle phases
        if isinstance(phase, list):
            if len(phase) != len(values1):
                raise ValueError('phase list length must match data length')
            phases = phase
        else:
            phases = None

        return values1, values2, labels, phases

    # Handle direct list input
    if isinstance(data, list):
        values1 = data

        # Get second series from data2_value parameter
        if isinstance(data2_value, int):
            values2 = data2_value
        elif isinstance(data2_value, list):
            if len(data2_value) != len(values1):
                raise ValueError('data2_value list length must match data length')
            values2 = data2_value
        else:
            raise ValueError(
                'data2_value (sample_size/area) must be provided when data is a list'
            )

        # Handle labels
        if isinstance(label, list):
            if len(label) != len(values1):
                raise ValueError('label list length must match data length')
            labels = label
        else:
            labels = list(range(1, len(values1) + 1))

        # Handle phases
        if isinstance(phase, list):
            if len(phase) != len(values1):
                raise ValueError('phase list length must match data length')
            phases = phase
        else:
            phases = None

        return values1, values2, labels, phases

    raise ValueError('Invalid input: data must be a list, Series, or DataFrame')


def normalize_spec_limits(
    data: pd.DataFrame | None,
    spec_limit: float | list[float] | str | None,
    data_length: int,
    limit_name: str = 'spec limit',
) -> list[float] | None:
    """
    Normalize specification limit input to a list of floats.

    Args:
        data: Input DataFrame (if spec_limit is a column name)
        spec_limit: Spec limit as float, list, column name, or None
        data_length: Expected length of the data
        limit_name: Name for error messages ("spec_upper" or "spec_lower")

    Returns:
        List of floats (one per point) or None if no spec limit provided

    Raises:
        ValueError: If input is invalid or lengths don't match

    Example:
        >>> normalize_spec_limits(None, 50.0, 10)
        [50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0]
        >>> normalize_spec_limits(None, [50.0, 51.0], 2)
        [50.0, 51.0]
    """
    if spec_limit is None:
        return None

    # Single float - broadcast to all points
    if isinstance(spec_limit, (float, int)):
        return [float(spec_limit)] * data_length

    # List of floats - validate length
    if isinstance(spec_limit, list):
        if len(spec_limit) != data_length:
            raise ValueError(
                f'{limit_name} list length ({len(spec_limit)}) must match '
                f'data length ({data_length})'
            )
        return [float(v) for v in spec_limit]

    # Column name from DataFrame
    if isinstance(spec_limit, str):
        if data is None or not isinstance(data, pd.DataFrame):
            raise ValueError(
                f'{limit_name} cannot be a column name when data is not a DataFrame'
            )
        if spec_limit not in data.columns:
            raise ValueError(f"Column '{spec_limit}' not found in DataFrame")
        return data[spec_limit].tolist()

    raise TypeError(
        f'{limit_name} must be float, list of floats, column name (str), or None'
    )


def normalize_subgroup_input(
    data: pd.DataFrame,
    value_column: str,
    subgroup: str,
    label: str | list | None = None,
    phase: str | list | None = None,
) -> tuple[list[list[float]], list[Any], list[str] | None, list[int]]:
    """
    Extract variable-sized subgroups from DataFrame.

    Groups the DataFrame by the subgroup column and extracts values, labels, and phases
    for each subgroup. This enables control charts with variable subgroup sizes.

    Args:
        data: Input DataFrame
        value_column: Column name containing measurement values
        subgroup: Column name containing subgroup identifiers
        label: Optional column name or list for x-axis labels
        phase: Optional column name or list for phase labels

    Returns:
        Tuple of:
        - subgroup_data: List of lists, each inner list contains values for one subgroup
        - subgroup_labels: Labels for each subgroup (from first measurement in subgroup)
        - subgroup_phases: Phase for each subgroup (from first measurement) or None
        - subgroup_sizes: Size of each subgroup

    Raises:
        ValueError: If columns not found or input is invalid

    Example:
        >>> df = pd.DataFrame({
        ...     'measurement': [10, 11, 12, 9, 10],
        ...     'batch': ['A', 'A', 'A', 'B', 'B']
        ... })
        >>> subgroup_data, labels, phases, sizes = normalize_subgroup_input(
        ...     df, value_column='measurement', subgroup='batch'
        ... )
        >>> # subgroup_data = [[10, 11, 12], [9, 10]]
        >>> # sizes = [3, 2]
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError('data must be a DataFrame when using subgroup parameter')

    # Validate required columns exist
    if value_column not in data.columns:
        raise ValueError(f"Column '{value_column}' not found in DataFrame")

    if subgroup not in data.columns:
        raise ValueError(f"Column '{subgroup}' not found in DataFrame")

    # Extract labels column/list
    if isinstance(label, str):
        if label not in data.columns:
            raise ValueError(f"Column '{label}' not found in DataFrame")
        labels_series = data[label]
    elif isinstance(label, list):
        if len(label) != len(data):
            raise ValueError(
                f'label list length ({len(label)}) must match data length ({len(data)})'
            )
        labels_series = pd.Series(label, index=data.index)
    else:
        # Generate sequential labels
        labels_series = pd.Series(range(1, len(data) + 1), index=data.index)

    # Extract phases column/list
    if isinstance(phase, str):
        if phase not in data.columns:
            raise ValueError(f"Column '{phase}' not found in DataFrame")
        phases_series = data[phase]
    elif isinstance(phase, list):
        if len(phase) != len(data):
            raise ValueError(
                f'phase list length ({len(phase)}) must match data length ({len(data)})'
            )
        phases_series = pd.Series(phase, index=data.index)
    else:
        phases_series = None

    # Group by subgroup column (maintains order of first appearance)
    grouped = data.groupby(subgroup, sort=False)

    subgroup_data: list[list[float]] = []
    subgroup_labels: list[Any] = []
    subgroup_phases: list[str] | None = [] if phases_series is not None else None
    subgroup_sizes: list[int] = []

    for subgroup_id, group in grouped:
        # Extract values for this subgroup
        values = group[value_column].tolist()
        subgroup_data.append(values)

        # Take first label from this subgroup
        first_idx = group.index[0]
        subgroup_labels.append(labels_series.loc[first_idx])

        # Take first phase from this subgroup (if phases exist)
        if phases_series is not None:
            subgroup_phases.append(phases_series.loc[first_idx])

        # Record subgroup size
        subgroup_sizes.append(len(values))

    return subgroup_data, subgroup_labels, subgroup_phases, subgroup_sizes
