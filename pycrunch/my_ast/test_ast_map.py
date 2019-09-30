import unittest

from pycrunch.my_ast.ast_map import AstMap


def test_file_parsed():
    sut = AstMap()
    print('x')
    print('x')
    sut.add_file('pycrunch/my_ast/ast_dogfood.py')
    files = sut.files
    assert 1 == len(files)
    my_file = files['pycrunch/my_ast/ast_dogfood.py']
    assert my_file.filename == 'pycrunch/my_ast/ast_dogfood.py'
    methods_map = my_file.methods_map
    assert len(methods_map) == 1

    print(methods_map.keys())
    expected_checksum = '0bdf7e15f78abb80e9118eca4b425af363d7028b985ecef6131ae365c8f801b8b6df48ba2bce97c0057ccf52551f8815437e4875f57e33c9d8b7b8d6bb1924cd'
    assert expected_checksum == methods_map['method_a'].checksum

