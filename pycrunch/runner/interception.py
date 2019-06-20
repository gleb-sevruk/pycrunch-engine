from io import StringIO
import sys
from contextlib import contextmanager

#  from https://stackoverflow.com/questions/17067560/intercept-pythons-print-statement-and-display-in-gui
@contextmanager
def capture_stdout():
    """
    context manager encapsulating a pattern for capturing stdout writes
    and restoring sys.stdout even upon exceptions

    Examples:
    >>> with capture_stdout() as get_value:
    >>>     print("here is a print")
    >>>     captured = get_value()
    >>> print('Gotcha: ' + captured)

    >>> with capture_stdout() as get_value:
    >>>     print("here is a print")
    >>>     raise Exception('oh no!')
    >>> print('Does printing still work?')
    """
    # Redirect sys.stdout
    out = StringIO()
    sys.stdout = out
    # Yield a method clients can use to obtain the value
    try:
        yield out.getvalue
    finally:
        # Restore the normal stdout
        sys.stdout = sys.__stdout__