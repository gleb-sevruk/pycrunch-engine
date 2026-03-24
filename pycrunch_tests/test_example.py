def shared():
    a = 1
    return a + 42

def test_success():
    assert shared() == 43

def test_failure():
    assert shared() == 44