import ast
import logging
import sys
from pathlib import Path
from typing import List

from pycrunch.discovery.simple import TestSet, TestsInModule
from pycrunch.introspection.clock import Clock
from pycrunch.session import config
from pycrunch.session.file_map import test_map

logger = logging.getLogger(__name__)


class AstTestDiscovery:
    def __init__(self, root_directory=None, configuration=None):
        self.root_directory = root_directory
        self.time_spent = 0.0
        self.clock = Clock()

        self.configuration = configuration if configuration is not None else config

    def find_tests_in_folder(self, folder, search_only_in=None):
        import pathlib
        import sys

        if not self.root_directory:
            MODULE_DIR = folder
        else:
            MODULE_DIR = self.root_directory

        logger.debug(sys.path)
        logger.debug(f'MODULE_DIR {MODULE_DIR}')
        logger.debug(f'Discovering tests in folder {folder}')

        if not MODULE_DIR in sys.path:
            sys.path.insert(0, MODULE_DIR)
            logger.debug(f'after append')
            logger.debug(sys.path)
        # The directory containing your modules needs to be on the search path.

        # Get the stem names (file name, without directory and '.py') of any
        # python files in your directory, load each module by name and run
        # the required function.

        parent_path = pathlib.Path(MODULE_DIR)
        folder_path = pathlib.Path(folder)

        py_files = folder_path.glob('**/*.py')
        test_set = TestSet()

        from os import environ
        for env_name, env_value in config.environment_vars.items():
            environ[env_name] = env_value

        for py_file in py_files:
            if search_only_in:
                if str(py_file) not in search_only_in:
                    continue

            current_file_path = py_file.relative_to(parent_path)
            if self.is_excluded_via_configuration(current_file_path):
                continue

            module_name = self.compute_module_name_from_path(current_file_path)
            if not self.is_module_with_tests(module_name):
                continue

            try:
                logger.debug('Compiling ' + module_name)
                ast_tree = self.load_syntax_tree_from(py_file)
                tests_found = self.load_tests_from_ast_representation(ast_tree)
            except Exception as ex:
                logger.error(f'Failed to parse ast of `{current_file_path}`')
                logger.exception(
                    f' parse {current_file_path} failed with exception: ' + str(ex)
                )
                continue

            filename = str(py_file)

            test_map.did_found_tests_in_file(filename, tests_found, module_name)
            test_set.add_module(TestsInModule(filename, tests_found, module_name))

            logger.debug(f'tests found: {tests_found}')

        logger.info(f' Time spent parsing AST : {round(self.time_spent, 3)} seconds')

        return test_set

    def load_syntax_tree_from(self, file_name) -> ast.Module:
        start = self.clock.now()
        contents = self.read_file(file_name)
        parse = ast.parse(contents, Path(file_name).name)
        end = self.clock.now()
        self.time_spent += end - start
        return parse

    def load_tests_from_ast_representation(self, ast_tree: ast.Module) -> List[str]:
        results = []

        def process_function_def(func: ast.FunctionDef) -> List[str]:
            if self.looks_like_test_name(func.name):
                return [func.name]

            return []

        def process_class_def(class_ast: ast.ClassDef) -> List[str]:
            class_results = []
            class_ast_name = class_ast.name

            c2 = self.looks_like_test_class(class_ast.name)
            if not c2:
                c2 = self.is_subclass_of_unittest(ast_tree, class_ast)

            if c2:
                for member in class_ast.body:
                    # TODO nested classes
                    if type(member) != ast.FunctionDef:
                        continue
                    member: ast.FunctionDef
                    if self.looks_like_test_name(member.name):
                        class_results.append(f"{class_ast_name}::{member.name}")
            return class_results

        mapping = {
            ast.FunctionDef: process_function_def,
            ast.ClassDef: process_class_def,
        }
        for node in ast_tree.body:
            walk_function = mapping.get(type(node))
            if not walk_function:
                continue
            values = walk_function(node)
            results.extend(values)

        return results

    @staticmethod
    def read_file(file_name: str) -> str:
        with open(file_name, "r") as f:
            return f.read()

    def compute_module_name_from_path(self, current_file_path):
        if len(current_file_path.parts) > 1:
            module_name = (
                str.join('.', current_file_path.parts[:-1])
                + '.'
                + current_file_path.stem
            )
        else:
            module_name = current_file_path.stem
        return module_name

    def is_excluded_via_configuration(self, current_file_path):
        s = str(current_file_path)
        x = False
        if s.startswith(self.configuration.discovery_exclusions) or s.endswith(
            self.configuration.discovery_exclusions
        ):
            x = True
        return x

    def is_module_with_tests(self, module_name):
        # Todo take pytest configs into account
        module_short_name = module_name.split('.')[-1]
        return module_short_name.startswith(
            ('test_', 'tests_')
        ) or module_short_name.endswith(('_test', 'tests', '_tests'))

    def looks_like_test_name(self, v):
        return v.startswith('test_') or v.endswith('_test')


    def looks_like_test_class(self, name: str) -> bool:
        return name.startswith('Test') or name.endswith('Test')

    def is_subclass_of_unittest(self, ast_module: ast.Module, class_ast: ast.ClassDef) -> bool:
        def search_via_deep_inheritance_analysis():
            if not self.configuration.deep_inheritance:
                return False

            # Compile and execute module
            code = compile(ast_module, filename='dummy', mode='exec')
            namespace = {}
            exec(code, namespace)

            # Check inheritance hierarchy
            may_null = namespace.get(class_ast.name)
            if may_null is None:
                return False
            may_be_not_loaded = sys.modules.get("unittest")
            is_unit_test_sub = may_be_not_loaded and issubclass(may_null, may_be_not_loaded.TestCase)

            return is_unit_test_sub

        available_subclasses = ['TestCase']

        for _ in class_ast.bases:
            type_of_base = type(_)
            if type_of_base == ast.Name:
                possible_none = getattr(_, 'id')
            elif type_of_base == ast.Attribute:
                possible_none = getattr(_, 'attr')
            else:
               continue

            if possible_none in available_subclasses:
                return True

        deep_inheritance_result = False
        try:
            deep_inheritance_result = search_via_deep_inheritance_analysis()
        except Exception as e:
            hint = 'You can disable this behaviour via `engine->deep-inheritance: false` configuration in .pycrunch-config.yaml'
            logger.warning(f'Failed to compile module to search via deep_inheritance_analysis for {class_ast.name}; Error: {e};\n{hint}')
        return deep_inheritance_result


# for basecls in inspect.getmro(self.obj.__class__):
#            dicts.append(basecls.__dict__)
