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