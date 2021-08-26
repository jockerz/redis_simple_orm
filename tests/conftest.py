import pytest

from fakeredis import FakeRedis, aioredis


@pytest.fixture
def sync_redis():
	server = FakeRedis(decode_responses=True)
	server.connected = True
	return server


@pytest.fixture
async def async_redis():
	return await aioredis.FakeRedis(
		decode_responses=True, encoding='utf-8'
	)
