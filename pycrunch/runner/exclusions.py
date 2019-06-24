py_test_exclusions = [
    '*_pytest/*',
    '*site-packages/*',
    '*.pytest_cache/*',

]

exclude_list = py_test_exclusions + [
    '*PyCharm.app/Contents/helpers/pydev/pydevd_file_utils.py',
    '*PyCharm.app/Contents/helpers/pydev/_pydevd_bundle/pydevd_comm.py',
    '*PyCharm.app/Contents/helpers/pydev/_pydevd_frame_eval/pydevd_frame_tracing.py',
    '*PyCharm.app/Contents/helpers/pydev/_pydevd_frame_eval/pydevd_modify_bytecode.py',
    '*site-packages/werkzeug/serving.py',
    '*runner/simple_test_runner.py',
    '*runner/execution_result.py',
    '*plugins/pytest_support/hot_reload.py',
    '*runner/interception.py'

]

