# Minimal locust stub for testing import

def task(weight=1):
    """Decorator used in tests; simply returns the function unchanged."""
    def decorator(func):
        return func
    return decorator

def between(min_wait, max_wait):
    return (min_wait, max_wait)

class HttpUser:
    host = ""
    def __init__(self):
        pass
