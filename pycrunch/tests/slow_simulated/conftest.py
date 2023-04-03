import time

import pytest

print('Session fixture; imported conftest.py')
@pytest.fixture(autouse=True, scope='session')
def sleep_1_second():
    print('Autouse fixture')
    time.sleep(1)
