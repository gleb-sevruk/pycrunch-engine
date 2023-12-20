import time
from pprint import pprint
from time import sleep
from unittest import mock

import pytest

from pycrunch.introspection import timings
from pycrunch.introspection.history import execution_history
from pycrunch.introspection.timings import Timeline


def test_timesheet_duration_single_interval():
    sut = Timeline('test 1')
    with use_clock_mock() as clock_mock:
        clock_mock.now.return_value = 1.0
        sut.start()
        clock_mock.now.return_value = 2.0
        sut.stop()
        assert sut.duration() == 1.0
        print_duration(sut)


def test_complex_nesting():
    sut = Timeline('complex')
    # 1 - root
    #   2 ... 4.5 nested_1
    #       3.1 ... 4.1 double_nested
    #  5 end root
    sut.start()

    sut.begin_nested_interval('nested_1')

    sut.begin_nested_interval('a')
    sut.end_nested_interval()

    sut.begin_nested_interval('b')
    sut.end_nested_interval()

    sut.begin_nested_interval('c')
    sut.end_nested_interval()

    sut.end_nested_interval()

    sut.begin_nested_interval('1')
    sut.end_nested_interval()

    sut.begin_nested_interval('2')

    sut.begin_nested_interval('2.1')
    sut.end_nested_interval()

    sut.begin_nested_interval('2.2')

    sut.begin_nested_interval('2.2.1')
    sut.end_nested_interval()

    sut.end_nested_interval()

    sut.end_nested_interval()

    sut.begin_nested_interval('3')
    sut.end_nested_interval()


    sut.stop()
    sut.to_console()

def test_serialization():
    sut = Timeline('complex')
    # 1 - root
    #   2 ... 4.5 nested_1
    #       3.1 ... 4.1 double_nested
    #  5 end root
    sut.start()
    # assert 1 == 2
    sut.begin_nested_interval('nested_1')

    sut.begin_nested_interval('a')
    sut.end_nested_interval()

    sut.begin_nested_interval('b')
    sut.end_nested_interval()

    sut.begin_nested_interval('c')
    sut.end_nested_interval()

    sut.end_nested_interval()

    sut.begin_nested_interval('1')
    sut.end_nested_interval()

    sut.begin_nested_interval('2')

    sut.begin_nested_interval('2.1')
    sut.end_nested_interval()

    sut.begin_nested_interval('2.2')

    sut.begin_nested_interval('2.2.1')
    sut.end_nested_interval()


    sut.end_nested_interval()

    sut.end_nested_interval()
    sut.mark_event('aaa')
    sut.begin_nested_interval('3')
    sut.end_nested_interval()

    sut.stop()

    execution_history.save(sut)
    pprint(execution_history.to_json())

def test_marker_inside_interval():
    sut = Timeline('test 1')
    with use_clock_mock() as clock_mock:
        clock_mock.now.return_value = 1.0
        sut.start()
        clock_mock.now.return_value = 2.0
        sut.begin_nested_interval('nested')
        clock_mock.now.return_value = 3.0
        sut.mark_event('event_1')
        clock_mock.now.return_value = 4.0
        sut.end_nested_interval()
        sut.mark_event('outer')
        clock_mock.now.return_value = 5.0
        sut.stop()
        sut.to_console()

    assert len(sut.root.events) == 1
    assert sut.root.events[0].name == 'outer'
    assert sut.root.events[0].timestamp == 4.0
    assert sut.root.intervals[0].events[0].timestamp == 3.0
    assert sut.root.intervals[0].events[0].name == 'event_1'

def test_double_nesting():
    sut = Timeline('test_double_nest')
    with use_clock_mock() as clock_mock:
        # 1 - root
        #   2 ... 4.5 nested_1
        #       3.1 ... 4.1 double_nested
        #  5 end root
        clock_mock.now.return_value = 1.0
        sut.start()
        clock_mock.now.return_value = 2.0
        sut.begin_nested_interval('nested_1')
        clock_mock.now.return_value = 3.1
        sut.begin_nested_interval('double_nested')
        clock_mock.now.return_value = 4.1

        sut.end_nested_interval()
        clock_mock.now.return_value = 4.5
        sut.end_nested_interval()

        clock_mock.now.return_value = 5
        sut.stop()
        sut.to_console()
        assert len(sut.root.intervals) == 1
        assert sut.root.duration() == 4
        nested_1 = sut.root.intervals[0]
        assert nested_1.duration() == 2.5
        double_nested = nested_1.intervals[0]
        assert double_nested.duration() == pytest.approx(1)

        print_duration(sut)


def test_nested_interval():
    sut = Timeline('test_intervals')
    with use_clock_mock() as clock_mock:
        clock_mock.now.return_value = 1.0
        sut.start()
        clock_mock.now.return_value = 2.0
        sut.begin_nested_interval('nested')
        clock_mock.now.return_value = 12.0

        sut.end_nested_interval()
        clock_mock.now.return_value = 13.0

        sut.stop()
        assert len(sut.root.intervals) == 1
        assert sut.root.duration() == 12.0
        sub_interval = sut.root.intervals[0]
        assert sub_interval.duration() == 10.0
        print_duration(sut)


def test_multiple_intervals():
    sut = Timeline('test_intervals')
    with use_clock_mock() as clock_mock:
        # 1 - root
        #   2 ... 3 nested_1
        #   3.1 ... 4.1 nested_2
        #  5 end root
        clock_mock.now.return_value = 1.0
        sut.start()
        clock_mock.now.return_value = 2.0
        sut.begin_nested_interval('nested_1')
        clock_mock.now.return_value = 3.0
        sut.end_nested_interval()
        clock_mock.now.return_value = 3.1
        sut.begin_nested_interval('nested_2')
        clock_mock.now.return_value = 4.6
        sut.end_nested_interval()

        clock_mock.now.return_value = 5
        sut.stop()

        assert len(sut.root.intervals) == 2
        assert sut.root.duration() == 4
        nested_interval_1 = sut.root.intervals[0]
        assert nested_interval_1.duration() == 1
        nested_interval_2 = sut.root.intervals[1]
        assert nested_interval_2.duration() == pytest.approx(1.5)
        print_duration(sut)



def use_clock_mock():
    return mock.patch('pycrunch.introspection.timings.clock')


def print_duration(sut):
    print(f'start {sut.root.started_at}')
    print(f'end {sut.root.stopped_at}')
    print(f'duration {sut.root.duration()}')
    # dump(sut)


def dump(obj):
  for attr in dir(obj):
    print("obj.%s = %r" % (attr, getattr(obj, attr)))