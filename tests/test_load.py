"""Load testing configuration using Locust."""

from locust import HttpUser, task, between


class SupportFormUser(HttpUser):
    """Simulates users submitting support requests via the web form."""

    wait_time = between(1, 5)
    host = "http://localhost:8000"

    @task(3)
    def submit_support_request(self):
        """Submit a support form request."""
        self.client.post(
            "/api/support/submit",
            json={
                "name": "Load Test User",
                "email": "loadtest@example.com",
                "subject": "Performance test ticket",
                "category": "technical",
                "priority": "medium",
                "message": "This is a load test message to verify system performance under stress.",
            },
        )

    @task(1)
    def check_health(self):
        """Check the health endpoint."""
        self.client.get("/health")

    @task(2)
    def check_ticket_status(self):
        """Check a ticket status (will return 404 for non-existent tickets)."""
        self.client.get("/api/support/ticket/test-ticket-1")

    @task(1)
    def get_metrics(self):
        """Fetch metrics endpoint."""
        self.client.get("/api/metrics")
