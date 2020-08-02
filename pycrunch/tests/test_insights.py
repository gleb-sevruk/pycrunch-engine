from unittest.mock import MagicMock

from pycrunch.insights.variables_inspection import InsightTimeline, inject_timeline
from pycrunch.insights import trace
from pycrunch.introspection.clock import clock


def test_should_trace_something_to_timeline():
    future_is_here = 1
    trace(future_is_here=future_is_here)
    trace(traced_variable=42)
    pass

def marker(name_of_the_marker):
    pass

def test_single_trace():
    trace(value_a=1)


def test_marker_single_variable_trace():
    trace(value_a=1)
    marker('point_of_interest')
    trace(value_a=42)
    trace(value_b='after sleep')

def test_marker_multiple_variables_trace():
    for i in range(10):
        trace(loop_counter=i)

    trace(value_a=__name__)
    marker('point_of_interest')
    trace(value_a=42)
    some_local = dict(
        x=1,
        y=2,
        size=dict(
            w=10,
            h=10),
        string='abc',
    )
    trace(some_local=some_local)


def test_inject_timeline_and_call_it_on_trace():
    future_is_here = 1
    mock = MagicMock()
    inject_timeline(mock)
    trace(future_is_here=future_is_here)
    mock.record.assert_called_with(future_is_here=future_is_here)
    pass

def test_timeline_one_variable():
    variable_name = 42
    x = InsightTimeline(clock)
    x.start()

    x.record(variable_name=42)

    first = x.variables[0]
    assert 'variable_name' == first.name
    assert 42 == first.value


def test_timeline_two_variables():
    variable_a = 42
    variable_b = 'Bret Victor'
    x = InsightTimeline(clock)
    x.start()
    x.record(variable_a=variable_a, brightest_mind=variable_b)

    first = x.variables[0]
    second = x.variables[1]
    assert 'variable_a' == first.name
    assert 'brightest_mind' == second.name
    assert 42 == first.value
    assert variable_b == second.value

def test_timeline_positional_arguments_only():
    variable_a = 42
    x = InsightTimeline(clock)
    x.start()
    x.record(variable_a, 777)

    first = x.variables[0]
    assert '1' == first.name
    assert 42 == first.value

    second = x.variables[1]
    assert '2' == second.name
    assert 777 == second.value
