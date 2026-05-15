class RequestValidator:
    def __init__(self, token):
        self.token = token
    def validate(self, url, params, signature):
        # Simple placeholder: always return False (invalid) for testing purposes.
        return False
