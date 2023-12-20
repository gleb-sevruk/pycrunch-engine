def test_generate_code():
    template =\
"""

def test_{number}():
    print('number is {number}')

"""
    # useful for testing a lot of tests
    for x in range(1, 1000):
        print(template.replace('{number}', str(x)))
