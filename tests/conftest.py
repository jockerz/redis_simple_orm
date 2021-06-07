import pytest

from fakeredis import FakeRedis, aioredis


@pytest.fixture
def sync_redis():
	return FakeRedis(decode_responses=True)


@pytest.fixture
async def async_redis():
	return await aioredis.create_redis_pool(encoding='utf-8')
