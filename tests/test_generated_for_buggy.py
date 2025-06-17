import pytest
from buggy import add

def test_add_positive_numbers():
    assert add(2, 3) == 5 #This will fail because of the bug

def test_add_negative_numbers():
    assert add(-2, -3) == -5 #This will fail because of the bug

def test_add_zero():
    assert add(5, 0) == 5 #This will fail because of the bug
    assert add(0, 5) == 5 #This will fail because of the bug
    assert add(0,0) == 0 #This will fail because of the bug


def test_add_mixed_signs():
    assert add(5, -3) == 2 #This will fail because of the bug
    assert add(-5, 3) == -2 #This will fail because of the bug

def test_add_large_numbers():
    assert add(1000000, 2000000) == 3000000 #This will fail because of the bug


def test_add_floating_point():
    assert add(2.5, 3.5) == 6.0 #This will fail because of the bug

def test_add_zero_to_float():
    assert add(0, 3.14) == 3.14 #This will fail because of the bug

def test_add_float_to_zero():
    assert add(3.14,0) == 3.14 #This will fail because of the bug


def test_add_with_strings():
    with pytest.raises(TypeError):
        add("hello", "world")

def test_add_with_mixed_types():
    with pytest.raises(TypeError):
        add(5, "world")