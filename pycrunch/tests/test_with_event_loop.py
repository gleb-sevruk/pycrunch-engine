import asyncio
from unittest import TestCase


class Something:
    def __init__(self):
        event_loop = asyncio.get_event_loop()
        # RuntimeError: This event loop is already running
        # candidate fix: pip install nest-asyncio
        event_loop.run_until_complete(asyncio.sleep(0.01))
        print('So what about now? nest-loop in action!')
        # asyncio.ensure_future(asyncio.sleep(0.11))

    def method_under_test(self):
        # This should be discovered regardless of event loop call
        return 42


smth = Something()

class TestMySomething(TestCase):
    def test_async_loop_wont_break(self):
        self.assertEqual(42, smth.method_under_test())