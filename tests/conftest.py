import pytest
import pytest_twisted

import aioredis as aioredis_
import txredisapi
from fakeredis import FakeRedis, aioredis
from twisted.internet.defer import inlineCallbacks


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


@pytest.fixture
def tx_redis():
    d = txredisapi.Connection(dbid=15, password='RedisPassword')

    @inlineCallbacks
    def cb(conn):
        yield conn.ping()
        yield conn.flushdb()
        return conn
    d.addCallback(cb)

    return pytest_twisted.blockon(d)
