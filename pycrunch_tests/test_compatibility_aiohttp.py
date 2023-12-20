from unittest.mock import patch

from pycrunch.compatibility.aiohttp_shim import aiohttp_init_parameters


def test_aiohttp_init_parameters_3_7():
    with patch('pycrunch.compatibility.aiohttp_shim.aiohttp') as mock:
        mock.__version__ = '3.7'
        actual = aiohttp_init_parameters()
        assert 'loop' not in actual


def test_aiohttp_init_has_loop_since_3_8():
    with patch('pycrunch.compatibility.aiohttp_shim.aiohttp') as mock:
        mock.__version__ = '3.8'
        actual = aiohttp_init_parameters()
        assert 'loop' in actual
