"""
Unit tests for plotting module pure helpers (no Plotly dependency).
"""

from pycontrolcharts.plotting import _format_violations_description, _get_phase_ranges


def test_format_violations_empty_list_returns_empty_string():
    assert _format_violations_description([]) == ''


def test_format_violations_known_type_1_over_ucl():
    result = _format_violations_description(
        [{'type': 1, 'description': 'Point 5 beyond UCL'}]
    )
    assert result == 'Over UCL : Point 5 beyond UCL'


def test_format_violations_known_types_1_to_10():
    violations = [
        {'type': 1, 'description': 't1'},
        {'type': 2, 'description': 't2'},
        {'type': 3, 'description': 't3'},
        {'type': 4, 'description': 't4'},
        {'type': 5, 'description': 't5'},
        {'type': 6, 'description': 't6'},
        {'type': 7, 'description': 't7'},
        {'type': 8, 'description': 't8'},
        {'type': 9, 'description': 't9'},
        {'type': 10, 'description': 't10'},
    ]
    result = _format_violations_description(violations)
    expected = (
        'Over UCL : t1<br>'
        'Under LCL : t2<br>'
        'Above average : t3<br>'
        'Below average : t4<br>'
        'Increasing run : t5<br>'
        'Decreasing run : t6<br>'
        '2 of 3 above +2σ : t7<br>'
        '2 of 3 below -2σ : t8<br>'
        '4 of 5 below -1σ : t9<br>'
        '4 of 5 above +1σ : t10'
    )
    assert result == expected


def test_format_violations_unknown_type_fallback():
    result = _format_violations_description([{'type': 99, 'description': 'Custom'}])
    assert result == 'Test 99 : Custom'


def test_format_violations_missing_type_fallback():
    result = _format_violations_description([{'description': 'No type'}])
    assert 'Test ?' in result or '?' in result
    assert 'No type' in result


def test_format_violations_multiple_br_separated():
    result = _format_violations_description(
        [
            {'type': 1, 'description': 'First'},
            {'type': 2, 'description': 'Second'},
        ]
    )
    assert result == 'Over UCL : First<br>Under LCL : Second'


def test_format_violations_missing_description_uses_empty_string():
    result = _format_violations_description([{'type': 1}])
    assert result == 'Over UCL : '


def test_get_phase_ranges_empty_returns_zero_range():
    assert _get_phase_ranges([]) == [(0, 0)]


def test_get_phase_ranges_single_phase():
    assert _get_phase_ranges([1, 1, 1, 1]) == [(0, 4)]


def test_get_phase_ranges_two_phases():
    assert _get_phase_ranges(['A', 'A', 'B', 'B']) == [(0, 2), (2, 4)]


def test_get_phase_ranges_three_phases():
    assert _get_phase_ranges([1, 1, 2, 2, 3, 3]) == [(0, 2), (2, 4), (4, 6)]


def test_get_phase_ranges_single_point_per_phase():
    assert _get_phase_ranges([1, 2, 3]) == [(0, 1), (1, 2), (2, 3)]


def test_get_phase_ranges_mixed_types():
    assert _get_phase_ranges([None, None, 'x', 'x']) == [(0, 2), (2, 4)]
