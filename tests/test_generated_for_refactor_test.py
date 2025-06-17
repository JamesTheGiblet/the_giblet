import pytest
from refactor_test import get_squares

def test_get_squares_empty_list():
    assert get_squares([]) == []

def test_get_squares_single_element():
    assert get_squares([2]) == [4]

def test_get_squares_positive_numbers():
    assert get_squares([1, 2, 3, 4, 5]) == [1, 4, 9, 16, 25]

def test_get_squares_negative_numbers():
    assert get_squares([-1, -2, -3]) == [1, 4, 9]

def test_get_squares_mixed_numbers():
    assert get_squares([-2, 0, 2]) == [4, 0, 4]

def test_get_squares_zero():
    assert get_squares([0]) == [0]

def test_get_squares_large_numbers():
    assert get_squares([100, 200, 300]) == [10000, 40000, 90000]


def test_get_squares_floating_point_numbers():
    assert get_squares([1.5, 2.5]) == [2.25, 6.25]

def test_get_squares_non_numeric_input():
    with pytest.raises(TypeError):
        get_squares([1, 'a', 3])

def test_get_squares_None_input():
    with pytest.raises(TypeError):
        get_squares(None)

def test_get_squares_with_string():
    with pytest.raises(TypeError):
        get_squares("abc")