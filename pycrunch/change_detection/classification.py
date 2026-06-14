def is_module_with_tests(module_name, configuration):
    # Todo take pytest configs into account
    module_short_name = module_name.split('.')[-1]
    return module_short_name.startswith((
        'test_',
        'tests_',
        *configuration.module_prefixes,
    )) or module_short_name.endswith(('_test', 'tests', '_tests'))


def looks_like_test_class(name: str) -> bool:
    return name.startswith('Test') or name.endswith('Test')


def compute_module_name_from_path(current_file_path):
    if len(current_file_path.parts) > 1:
        module_name = (
            str.join('.', current_file_path.parts[:-1]) + '.' + current_file_path.stem
        )
    else:
        module_name = current_file_path.stem
    return module_name
