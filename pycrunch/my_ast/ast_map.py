import _ast
import ast
import hashlib
import io


class MethodMetadata:
    def __init__(self, method_name, start_line, end_line, checksum):
        self.method_name = method_name
        self.checksum = checksum
        self.end_line = end_line
        self.start_line = start_line

class AstForFile:
    def __init__(self, filename, methods_map):
        self.filename = filename
        # method_name -> sha256 ?
        # maybe use intervalTree for storing/searching ranges?
        self.methods_map = methods_map


class AstMap:
    def __init__(self):
        # filename -> my_ast tree
        self.files = dict()

    def add_file(self, filename):
        print(f'reading {filename}')
        with io.open(filename, encoding='utf-8', mode='r') as file:
            print('contents:')
            contents = file.read()
            # print(contents)
            tree = ast.parse(contents)
            map_with_methods = self.parse_methods(tree)
            self.files[filename] = AstForFile(filename, map_with_methods)

    def parse_methods(self, ast_tree):
        # todo: find methods in class definitions
        methods_map = dict()
        for node in ast_tree.body:
            is_method = self.is_method_definition(node)
            if is_method:
                # output start and end of the function
                method_start = node.lineno
                method_end = self.try_find_ending(node)
                method_name = node.name
                dump = ast.dump(node)
                print(dump)
                print(f'start->end: {method_start}->{method_end}')
                string_with_dump = dump
                # is this recipe for disaster waiting?
                checksum = hashlib.sha512(string_with_dump.encode()).hexdigest()
                # print(checksum)
                methods_map[method_name] = MethodMetadata(method_name, start_line=method_start, end_line=method_end, checksum=checksum)

        return methods_map


    def is_method_definition(self, node):
        is_method_definition = isinstance(node, _ast.FunctionDef) or isinstance(node, _ast.AsyncFunctionDef)
        return is_method_definition

    def try_find_ending(self, node):
        # this can be replaced with end_lineno in python 3.9 :(
        # recurse in depth without explosion of callstack
        leaf = node
        while hasattr(leaf, 'body'):
            # pprint(leaf)
            leaf = leaf.body[-1]
        return leaf.lineno
