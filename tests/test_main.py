from yt_uv import add, multiply


def test_add():
    assert add(1, 2) == 3


def test_multiply():
    assert multiply(2.5, 2) == 5
