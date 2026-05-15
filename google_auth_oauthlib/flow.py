# Stub for google_auth_oauthlib.flow

class InstalledAppFlow:
    @staticmethod
    def from_client_secrets_file(file_path, scopes):
        # Return a dummy flow object
        return InstalledAppFlow()
    def run_local_server(self, port=0):
        # Return dummy credentials object
        class Creds:
            def __init__(self):
                self.valid = True
                self.expired = False
                self.refresh_token = None
            def to_json(self):
                return "{}"
        return Creds()
