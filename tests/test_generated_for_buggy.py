import pytest
from buggy import add

def test_add_positive_numbers():
    assert add(2, 3) == 5
    assert add(10, 5) == 15
    assert add(0, 0) == 0

def test_add_negative_numbers():
    assert add(-2, -3) == -5
    assert add(-10, 5) == -5
    assert add(10, -5) == 5

def test_add_mixed_numbers():
    assert add(-2, 3) == 1
    assert add(2, -3) == -1
    assert add(0, -5) == -5
    assert add(-5, 0) == -5

def test_add_zero():
    assert add(5, 0) == 5
    assert add(0, 5) == 5


def test_add_large_numbers():
    assert add(1000, 2000) == 3000
    assert add(1000000, 2000000) == 3000000


def test_add_floating_point_numbers():
    assert add(2.5, 3.5) == 6.0
    assert add(10.5, 5.5) == 16.0
    assert add(-2.5, 3.5) == 1.0

def test_add_invalid_input_string():
    with pytest.raises(TypeError):
        add("2", 3)
    with pytest.raises(TypeError):
        add(2, "3")
    with pytest.raises(TypeError):
        add("2", "3")

def test_add_invalid_input_list():
    with pytest.raises(TypeError):
        add([1,2], 3)
    with pytest.raises(TypeError):
        add(2, [1,2])