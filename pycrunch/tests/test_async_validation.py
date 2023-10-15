import pytest

@pytest.mark.asyncio
async def test_async_simple():
    print(1)
    assert 1 == 1