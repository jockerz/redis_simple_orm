import os

import pytest
import pytest_twisted

import txredisapi
from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis
from twisted.internet.defer import inlineCallbacks

REDIS_DB = int(os.getenv('REDIS_TEST_DB', 14))
REDIS_PASS = os.getenv('REDIS_TEST_PASS', 'RedisPassword')


@pytest.fixture
def sync_redis() -> SyncRedis:
    server = SyncRedis(db=REDIS_DB, password=REDIS_PASS, decode_responses=True)
    server.flushdb()
    return server


@pytest.fixture
async def async_redis() -> AsyncRedis:
    conn = AsyncRedis(db=REDIS_DB, password=REDIS_PASS, decode_responses=True)
    await conn.flushdb()
    return conn


@pytest.fixture
def tx_redis():
    d = txredisapi.Connection(dbid=REDIS_DB, password=REDIS_PASS)

    @inlineCallbacks
    def cb(conn):
        yield conn.flushdb()
        return conn
    d.addCallback(cb)

    return pytest_twisted.blockon(d)
