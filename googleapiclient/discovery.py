# Stub for googleapiclient.discovery

def build(service_name, version, credentials=None):
    # Return a simple mock object with chained attribute calls used in gmail_handler.
    class Dummy:
        def users(self):
            return self
        def watch(self, userId=None, body=None):
            # Return object with execute method
            return self
        def messages(self):
            return self
        def get(self, userId=None, id=None, format=None):
            return self
        def send(self, userId=None, body=None):
            return self
        def execute(self):
            # Return empty dict for simplicity
            return {}
    return Dummy()
