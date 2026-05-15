# Minimal stub for aiokafka used in tests

class AIOKafkaProducer:
    def __init__(self, *args, **kwargs):
        pass
    async def start(self):
        pass
    async def stop(self):
        pass
    async def send_and_wait(self, topic, value):
        # No-op, just pretend the message was sent
        return None

class AIOKafkaConsumer:
    def __init__(self, *args, **kwargs):
        pass
    async def start(self):
        pass
    async def stop(self):
        pass
    def __aiter__(self):
        # Provide an empty async iterator
        return self
    async def __anext__(self):
        raise StopAsyncIteration
