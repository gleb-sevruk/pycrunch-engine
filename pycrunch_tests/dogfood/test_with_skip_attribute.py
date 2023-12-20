from pytest import skip, mark


def test_without_skip():
    pass

@mark.skip
def test_with_skip():
    pass