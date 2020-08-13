import uuid

from pycrunch.scheduling.scheduler import TestRunScheduler
from pycrunch.shared.primitives import TestMetadata

def generate_test_fake(name):
    filename = str(uuid.uuid4())
    test_name = str(name)
    return TestMetadata(filename, test_name, str(uuid.uuid4()), test_name, 'unknown')


def generate_tests(desired_amount):
    result = []
    for n in range(0, desired_amount):
        result.append(generate_test_fake(n))

    return result


def test_scheduled_single_test():
    tests = generate_tests(1)
    sut = create_sut()
    actual = sut.schedule_into_tasks(tests)
    # actual is list of tasks
    assert len(actual) == 1
    first_task = actual[0]
    assert len(first_task.tests) == 1

def test_up_to_five_tests_should_be_in_single_task():
    tests = generate_tests(5)
    sut = create_sut()
    tasks = sut.schedule_into_tasks(tests)
    assert len(tasks) == 1
    first_task = tasks[0]
    assert len(first_task.tests) == 5


def test_six_tests_should_be_in_two_tasks():
    tests = generate_tests(6)
    sut = create_sut()
    tasks = sut.schedule_into_tasks(tests)
    assert len(tasks) == 2
    assert len(tasks[0].tests) == 3
    assert len(tasks[1].tests) == 3

def test_seven_tests_should_be_in_two_tasks():
    tests = generate_tests(7)
    sut = create_sut()
    tasks = sut.schedule_into_tasks(tests)
    assert len(tasks) == 2
    first_task = tasks[0]
    second_task = tasks[1]
    assert len(first_task.tests) == 4
    assert len(second_task.tests) == 3


def test_14_should_be_in_tree_tasks():
    tests = generate_tests(14)
    sut = create_sut()
    tasks = sut.schedule_into_tasks(tests)
    assert len(tasks) == 3
    assert len(tasks[0].tests) == 5
    assert len(tasks[1].tests) == 5
    assert len(tasks[2].tests) == 4


def test_twenty_should_be_in_four_tasks():
    tests = generate_tests(20)
    sut = create_sut()
    tasks = sut.schedule_into_tasks(tests)
    assert len(tasks) == 4
    assert len(tasks[0].tests) == 5
    assert len(tasks[1].tests) == 5
    assert len(tasks[2].tests) == 5
    assert len(tasks[3].tests) == 5

def test_51_should_be_in_four_tasks():
    tests = generate_tests(51)
    sut = create_sut()
    tasks = sut.schedule_into_tasks(tests)
    assert len(tasks) == 4
    assert len(tasks[0].tests) == 13
    assert len(tasks[1].tests) == 13
    assert len(tasks[2].tests) == 13
    assert len(tasks[3].tests) == 12


def create_sut():
    return TestRunScheduler(cpu_cores=4, threshold=5)
