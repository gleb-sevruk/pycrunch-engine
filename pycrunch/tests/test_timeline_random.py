from time import sleep
from unittest.mock import MagicMock

from pycrunch.insights.variables_inspection import InsightTimeline, trace


def test_random_stuff():
    for x in range(10):
        # sleep(0.5)
        trace(x=x)
