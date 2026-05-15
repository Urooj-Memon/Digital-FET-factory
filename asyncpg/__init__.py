# Minimal asyncpg stub for testing without a real PostgreSQL server

class _MockConnection:
    async def fetchval(self, query, *args, **kwargs):
        # Return a dummy value; for health check we just need to succeed
        return 1
    async def close(self):
        pass

class _MockPool:
    def __init__(self, *args, **kwargs):
        pass
    async def acquire(self):
        return _MockConnection()
    async def release(self, conn):
        await conn.close()
    async def close(self):
        pass

# Alias class to satisfy type annotations in the codebase
class Pool(_MockPool):
    """Compatibility alias for asyncpg.Pool type hinting."""
    pass

async def create_pool(*args, **kwargs):
    # Return a mock pool that pretends to connect successfully
    return _MockPool()
