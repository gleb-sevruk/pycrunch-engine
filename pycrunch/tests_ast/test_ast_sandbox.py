import io
import unittest
from pathlib import Path
from typing import Optional

import libcst as cst
from libcst import ClassDef, FunctionDef
from libcst.tool import dump
from pycrunch.insights import trace


class FNamesPrinter(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (cst.metadata.PositionProvider,)

    def visit_FunctionDef(self, node: "FunctionDef") -> Optional[bool]:
        print(node.name.value)

class ClassNamePrinter(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (cst.metadata.PositionProvider,)


    def visit_ClassDef(self, node: "ClassDef") -> Optional[bool]:
        pos = self.get_metadata(cst.metadata.PositionProvider, node).start


        print(f"{node.name.value} found at line {pos.line}, column {pos.column}")
        node.visit(FNamesPrinter())
        return True


def file_as_text(p: Path):
    with io.FileIO(p, 'r') as stream:
        return stream.readall()
    
class TestAstParse(unittest.TestCase):
    def test_sample(self):
        joinpath = Path(__file__).parent.joinpath('test_case3.py')
        # joinpath = Path(__file__).parent.joinpath('test_simplest.py')
        text = file_as_text(joinpath)
        trace(text)
        trace(text)
        cst_tree = cst.parse_module(text)
        wrapper = cst.metadata.MetadataWrapper(cst_tree)

        wrapper.visit(ClassNamePrinter())
        trace(dump(cst_tree))
