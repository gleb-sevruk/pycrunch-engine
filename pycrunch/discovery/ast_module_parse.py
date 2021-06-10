import ast
import io
from pathlib import Path
from typing import List
"""
 Todo: this should probably take into consideration current config from pytest.ini regarding match patters

"""
class AstModule:
    def get_names(self, py_file: Path) -> List[str]:
        results_to_return = []
        with io.open(py_file) as my_file:
            source_code = my_file.read()
            results : ast.AST = ast.parse(source_code, str(py_file))
            for _ in results.body:
                if isinstance(_, ast.FunctionDef):
                    # I am a function
                    if self.looks_like_test_name(_.name):
                        results_to_return.append(_.name)
                if isinstance(_, ast.ClassDef):
                    if self.is_test_class(_):
                        results_to_return.extend(self.find_in_class(_))

        return results_to_return

    def find_in_class(self, class_def: ast.ClassDef) -> List[str]:
        results = []
        for _ in class_def.body:
            if isinstance(_, ast.FunctionDef):
                if self.looks_like_test_name(_.name):
                    results.append(class_def.name + '::' + _.name)
        return results

    def looks_like_test_name(self, function_name: str):
        return function_name.startswith('test_') or function_name.endswith('_test')

    def is_test_class(self, _: ast.ClassDef) -> bool:
        """
          Determines, whether given class is a test class
        """
        name :str= _.name.lower()
        # name_matches_pattern = name.startswith('test') or name.endswith('test')
        name_matches_pattern = name.startswith('test')
        if name_matches_pattern:
            return True

        return self.is_descendant_of_testcase(_)

    def is_descendant_of_testcase(self, _: ast.ClassDef) -> bool:
        if _.bases:
            first : ast.Name = _.bases[0]
            return first.id == 'TestCase'
        return False
