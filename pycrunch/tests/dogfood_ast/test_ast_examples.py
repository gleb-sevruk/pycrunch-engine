from unittest import TestCase

from pycrunch.tests.dogfood_ast.ast_test_utils import CrossFileTestCase


class NotTestClass:
    def test_one(self):
        print('should not be found')

class TestClassOne:
    def test_one(self):
        print("I am a test")

class AnotherTest:
    def test_another(self):
        print("This is degraded scenario, pycharm shows it as a test, but")
        print("  pytest won't see it when ran")


class InheritedFromBase(TestCase):
    def test_with_base_class(self):
        print('should be found; because it has base class')

class AdvancedTestCase(TestCase):
    def some_utility(self):
        print('I am very useful ascendant of test case')


class AdvancedScenario(AdvancedTestCase):
    def test_advanced(self):
        print('Surprise, ASSERT!')

class CrossFileScenario(CrossFileTestCase):
    """
      in this, base class implementing testcase is defined in different file
    """
    def test_crossfile(self):
        """
        While discovering more about topic
        I found that pytest is doing full load/compile run
          If I type sleep(1000); test discovery will never finish
          It also executes all code/deps initialization code, so it is not really AST,
          but a combination of something even worse (combined with pluggy)


        :return:
        """
        print('Surprise, ASSERT!')