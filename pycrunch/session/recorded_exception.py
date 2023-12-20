class RecordedException:
    def __init__(self, filename, line_number, full_traceback, _locals):
        """
        @type filename: str
        @type line_number: int
        @type full_traceback: str
        @type _locals: dict
        """
        self.filename = filename  # type: str
        self.line_number = line_number  # type: int
        self.full_traceback = full_traceback  # type: str
        self.variables = _locals  # type: Optional[Dict[str, Any]]

    def make_safe_for_pickle(self):
        self.variables = {
            'cannot pickle all variables with depth 3': 'pickle error, check pycrunch.plugins.pytest_support.exception_utilities.custom_repr depth'
        }
