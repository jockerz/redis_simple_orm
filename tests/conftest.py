import pytest
import pytest_twisted

import aioredis
import txredisapi
# from fakeredis import FakeRedis, aioredis as fake_aioredis
from redis import Redis as SyncRedis
from twisted.internet.defer import inlineCallbacks

REDIS_DB = 15
REDIS_PASS = 'RedisPassword'


@pytest.fixture
def sync_redis():
    # server = FakeRedis(decode_responses=True)
    # server.connected = True
    server = SyncRedis(db=REDIS_DB, password=REDIS_PASS, decode_responses=True)
    server.flushdb()
    return server


@pytest.fixture
async def async_redis():
    if aioredis.__version__ >= '2.0.0':
        r = await aioredis.Redis(
            db=REDIS_DB, password=REDIS_PASS,
            decode_responses=True, encoding='utf-8'
        )
    else:
        r = await aioredis.create_redis(
            db=REDIS_DB, password=REDIS_PASS,
            encoding='utf-8'
        )
    await r.flushdb()
    return r


@pytest.fixture
def tx_redis():
    d = txredisapi.Connection(dbid=REDIS_DB, password=REDIS_PASS)

    @inlineCallbacks
    def cb(conn):
        yield conn.ping()
        yield conn.flushdb()
        return conn
    d.addCallback(cb)

    return pytest_twisted.blockon(d)
