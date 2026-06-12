import ast
import copy
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, FrozenSet, Optional, Sequence


@dataclass(frozen=True)
class FunctionFingerprint:
    qualname: str
    body_hash: str
    line_start: int
    line_end: int
    has_decorators: bool
    is_test: bool = False
    is_fixture: bool = False


@dataclass(frozen=True)
class FileFingerprint:
    functions: Dict[str, FunctionFingerprint]
    module_level_hash: str
    import_targets: FrozenSet[str]
    test_file: bool = False


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _strip_locations(node: ast.AST) -> ast.AST:
    for child in ast.walk(node):
        for attr in ('lineno', 'col_offset', 'end_lineno', 'end_col_offset'):
            if hasattr(child, attr):
                setattr(child, attr, 0)
    return node


def _remove_docstring(body: list) -> list:
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return body[1:]
    return body


def _is_test_name(name: str, prefixes: Sequence[str] = ('test_',)) -> bool:
    return any(name.startswith(p) for p in prefixes)


def _is_fixture_decorator(node: ast.expr) -> bool:
    func = node
    if isinstance(node, ast.Call):
        func = node.func
    if isinstance(func, ast.Name):
        return func.id == 'fixture'
    if isinstance(func, ast.Attribute):
        return func.attr == 'fixture'
    return False


def _is_fixture_function(func_node: ast.FunctionDef) -> bool:
    return any(_is_fixture_decorator(d) for d in func_node.decorator_list)


def _is_test_function_node(
    func_node: ast.FunctionDef,
    class_name: str,
    prefixes: Sequence[str],
) -> bool:
    name_ok = _is_test_name(func_node.name, prefixes)
    if class_name:
        # Methods in a class are tests only when both the method name and class name match
        return name_ok and (
            class_name.startswith('Test') or class_name.endswith('Test')
        )
    return name_ok


def _hash_function_node(func_node: ast.FunctionDef) -> str:
    node = copy.deepcopy(func_node)
    node.body = _remove_docstring(node.body)
    # strip signature (args/defaults/annotations) — only body+decorators matter for body_hash
    node.args = ast.arguments(
        posonlyargs=[],
        args=[],
        vararg=None,
        kwonlyargs=[],
        kw_defaults=[],
        kwarg=None,
        defaults=[],
    )
    node.returns = None
    _strip_locations(node)
    return _sha256(ast.dump(node, include_attributes=False))


def _collect_imports(
    tree: ast.AST, filename: str, root: Optional[str]
) -> FrozenSet[str]:
    targets = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                targets.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            level = node.level
            if level > 0:
                resolved = _resolve_relative(filename, root, module, level, node.names)
                targets.update(resolved)
            else:
                if module:
                    targets.add(module)
                for alias in node.names:
                    if module:
                        targets.add(f'{module}.{alias.name}')
                    else:
                        targets.add(alias.name)
    return frozenset(targets)


def _resolve_relative(
    filename: str, root: Optional[str], module: str, level: int, names
) -> list:
    try:
        file_path = Path(filename).resolve()
        if root:
            root_path = Path(root).resolve()
        else:
            root_path = file_path.parent

        pkg_path = file_path.parent
        for _ in range(level - 1):
            pkg_path = pkg_path.parent

        def path_to_module(p: Path) -> str:
            try:
                rel = p.relative_to(root_path)
                parts = list(rel.parts)
                if parts and parts[-1].endswith('.py'):
                    parts[-1] = parts[-1][:-3]
                if parts and parts[-1] == '__init__':
                    parts = parts[:-1]
                return '.'.join(parts)
            except ValueError:
                return p.stem

        pkg_module = path_to_module(pkg_path)

        results = []
        if module:
            full = f'{pkg_module}.{module}' if pkg_module else module
            results.append(full)
            for alias in names:
                results.append(f'{full}.{alias.name}')
        else:
            for alias in names:
                full = f'{pkg_module}.{alias.name}' if pkg_module else alias.name
                results.append(full)
        return results
    except Exception:
        return []


def _strip_function_bodies(
    stmts,
    test_file: bool = False,
    function_prefixes: Sequence[str] = ('test_',),
    class_name: str = '',
) -> None:
    for node in stmts:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.body = [ast.Pass()]
            if test_file:
                # Strip decorators from test-functions and fixtures so that
                # @pytest.mark.parametrize / @skip / @fixture(scope=...) changes
                # don't affect the module skeleton hash.
                if _is_fixture_function(node) or _is_test_function_node(
                    node, class_name, function_prefixes
                ):
                    node.decorator_list = []
        elif isinstance(node, ast.ClassDef):
            _strip_function_bodies(
                node.body, test_file, function_prefixes, class_name=node.name
            )


def _compute_module_level_hash(
    tree: ast.Module,
    test_file: bool = False,
    function_prefixes: Sequence[str] = ('test_',),
) -> str:
    skeleton = copy.deepcopy(tree)
    _strip_function_bodies(skeleton.body, test_file, function_prefixes)
    _strip_locations(skeleton)
    return _sha256(ast.dump(skeleton, include_attributes=False))


def _collect_functions(
    tree: ast.AST,
    function_prefixes: Sequence[str] = ('test_',),
) -> Dict[str, FunctionFingerprint]:
    result = {}

    def _process_body(stmts, prefix, class_name: str = ''):
        for node in stmts:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualname = f'{prefix}.{node.name}' if prefix else node.name
                decorators = node.decorator_list
                line_start = min((d.lineno for d in decorators), default=node.lineno)
                line_end = node.end_lineno
                body_hash = _hash_function_node(node)
                is_fixture = _is_fixture_function(node)
                is_test = (not is_fixture) and _is_test_function_node(
                    node, class_name, function_prefixes
                )
                result[qualname] = FunctionFingerprint(
                    qualname=qualname,
                    body_hash=body_hash,
                    line_start=line_start,
                    line_end=line_end,
                    has_decorators=bool(decorators),
                    is_test=is_test,
                    is_fixture=is_fixture,
                )
            elif isinstance(node, ast.ClassDef):
                cls_qualname = f'{prefix}.{node.name}' if prefix else node.name
                _process_body(node.body, cls_qualname, class_name=node.name)

    if isinstance(tree, ast.Module):
        _process_body(tree.body, '')
    return result


def fingerprint_source(
    source: str,
    filename: str,
    root: Optional[str] = None,
    *,
    test_file: bool = False,
    function_prefixes: Sequence[str] = ('test_',),
) -> FileFingerprint:
    tree = ast.parse(source, filename=filename)  # raises SyntaxError on bad input

    functions = _collect_functions(tree, function_prefixes=function_prefixes)
    module_level_hash = _compute_module_level_hash(
        tree, test_file=test_file, function_prefixes=function_prefixes
    )
    import_targets = _collect_imports(tree, filename, root)
    return FileFingerprint(
        functions=functions,
        module_level_hash=module_level_hash,
        import_targets=import_targets,
        test_file=test_file,
    )
