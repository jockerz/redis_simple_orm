import pytest

import aioredis as aioredis_
from fakeredis import FakeRedis, aioredis


@pytest.fixture
def sync_redis():
	server = FakeRedis(decode_responses=True)
	server.connected = True
	return server


@pytest.fixture
async def async_redis():
	if aioredis_.__version__ >= '2.0.0':
		return await aioredis.FakeRedis(
			decode_responses=True, encoding='utf-8'
		)
	else:
		return await aioredis.create_redis(encoding='utf-8')
