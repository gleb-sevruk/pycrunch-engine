from nose import with_setup


def multiply(a, b):
    return a * b

def test_numbers_3_4():
    actual = multiply(3, 4)
    print(actual)
    assert actual == 12


def setup_func():
    print('setup')

def teardown_func():
    print('teardown_func')

@with_setup(setup_func, teardown_func)
def test_a():
    print('test running...')