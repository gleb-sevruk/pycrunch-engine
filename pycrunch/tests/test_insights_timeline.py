from datetime import date, datetime
from unittest.mock import MagicMock

from pycrunch.insights.variables_inspection import InsightTimeline, RecordedVariable, trace


def test_should_adjust_to_clock_start():
    clock = MagicMock()
    now_mock = MagicMock()
    now_mock.side_effect = (100, 101, 110)

    # 100 -- 101 ----------------- 110
    # events should be in timeline time:
    # 1 ----------------- 10
    clock.now = now_mock
    x = InsightTimeline(clock)
    x.start()
    x.record(x=1)
    x.record(y=2)
    variables = x.variables
    assert variables[0].timestamp == 1
    assert variables[1].timestamp == 10

def test_non_traceble_variables_should_cast_to_str():
    sut = RecordedVariable('name', datetime.now(), -1)
    actual = sut.as_json()
    assert type(actual['value']) == str
