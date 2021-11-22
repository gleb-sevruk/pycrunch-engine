from asyncio import get_event_loop
from typing import Any, Dict

import aiohttp
from pycrunch.compatibility.version_utils import parse_version_string


def aiohttp_init_parameters() -> Dict[str, Any]:

    # aiohttp since 3.8 creates new event loop on startup.
    #   https://github.com/aio-libs/aiohttp/pull/5572
    # aiohttp <= 3.7 does not have `loop` argument, we do not want to pass it

    result_arguments = {}
    aio_version = parse_version_string(aiohttp.__version__)
    if aio_version >= (3, 8, 0):
        result_arguments['loop'] = get_event_loop()

    return result_arguments
