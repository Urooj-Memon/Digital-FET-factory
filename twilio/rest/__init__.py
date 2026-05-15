# Minimal twilio stub for tests

class Message:
    def __init__(self, sid="SM123"):
        self.sid = sid

class Messages:
    def create(self, *args, **kwargs):
        return Message()

class Client:
    def __init__(self, *args, **kwargs):
        self.messages = Messages()
