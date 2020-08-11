import io
import unittest
from pathlib import Path
from typing import Optional

import libcst as cst
from libcst import ClassDef, FunctionDef
from libcst.tool import dump
from pycrunch_trace.client.api import trace

def file_as_text(p: Path):
    with io.FileIO(p, 'r') as stream:
        return stream.readall()
@trace
def sometesting():
    joinpath = Path(__file__).parent.joinpath('test_case2.py')
    # joinpath = Path(__file__).parent.joinpath('test_simplest.py')
    text = file_as_text(joinpath)
    trace(text)
    cst_tree = cst.parse_module(text)
    wrapper = cst.metadata.MetadataWrapper(cst_tree)

if __name__ == '__main__':
    sometesting()