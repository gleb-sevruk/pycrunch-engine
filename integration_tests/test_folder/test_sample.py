from shared_file import some_shared_method


def test_one():
    print('output from test_one')
    some_shared_method()


def test_two():
    some_shared_method()
