from pycrunch.api.serializers import CoverageRunForSingleFile
from pycrunch.plugins.pytest_support.exception_utilities import custom_repr


def some_error_method():
    raise Exception('some exception')

def test_some_exception():
    print('ssss')
    my_var_1 = 'a'
    my_var_2 = 'b'
    some_error_method()
    assert 1 == 2

def test_small_dict():
    x = dict(x=2)
    assert 1 == 2

def test_custom_rerp():
    # actual = custom_repr(dict(x=2, y=3))
    actual = custom_repr([1,2,3])
    assert actual == "{'x': 2, 'y': 3}"


    pass
def test_long_dict():
    import random
    keys = ['a', 'b', 'c', 'd', 'e']

    # Generate the expected dictionary
    expected = {key: random.randint(1, 10) for key in keys}

    # Generate the actual dictionary with some mismatched values
    actual = expected.copy()
    mismatched_keys = random.sample(keys, 2)  # Choose 2 keys to create mismatches
    for key in mismatched_keys:
        actual[key] = random.randint(11, 20)  # Assign a value different from the expected one

    print("Expected:", expected)
    print("Actual:", actual)
    # x = CoverageRunForSingleFile('file1.py', [1, 2, 3])
    assert expected == actual

def test_custom_obj():
    class Person:
        def __init__(self, name, age, friends):
            self.name = name
            self.age = age
            self.friends = friends

    class Company:
        def __init__(self, name, employees):
            self.name = name
            self.employees = employees

    class Country:
        def __init__(self, name, population, companies):
            self.name = name
            self.population = population
            self.companies = companies

    class Continent:
        def __init__(self, name, countries):
            self.name = name
            self.countries = countries

    # Creating a deep and complex object
    alice = Person("Alice", 28, [])
    bob = Person("Bob", 32, [alice])
    charlie = Person("Charlie", 24, [bob])

    company1 = Company("TechCorp", [alice, bob])
    company2 = Company("BizInc", [charlie])

    country1 = Country("Exampleland", 1000000, [company1, company2])
    country2 = Country("Samplestan", 500000, [])

    continent = Continent("Democontinent", [country1, country2])

    assert continent == Continent("Democontinent2", [country1])