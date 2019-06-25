import os
from time import sleep


def test_dummy():
    # print('test_method')
    print('222 ')
    print('222 ')
    print('222 ')
    print('222 ')
    print('222 ')

    print('te st_method 2')

def test_x():
    x = 2
    print('test_x before assert')
    print(f'PID in test: {os.getpid()}')

    assert x == 2
    print('test_method 3')

def test_z():
    print('test_method y')

def test_failing():
    assert 3 == 3
    assert 1 == 2
