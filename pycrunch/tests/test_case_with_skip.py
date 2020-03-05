from unittest import TestCase, skip


class TestWithSkips(TestCase):
    def setUp(self) -> None:
        # by some reason skipped test without reason still runs setup
        pass

    @skip
    def test_should_be_skipped(self):
        print('this should show as success in pycrunch report')

    @skip('reason')
    def test_should_be_skipped_with_reason(self):
        # py.test reporter seems to use different algo to skip test with reason and without
        # make sure both of them works

        print('this should show as success in pycrunch report')

    def test_alongside_with_skipped(self):
        assert True

