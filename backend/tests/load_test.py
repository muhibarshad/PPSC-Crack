"""
PPSC Crack — Locust Load Test
===============================
Simulates 500 concurrent users hitting the API.

Usage:
  cd backend
  locust -f tests/load_test.py --host=http://localhost:8000

  Then open http://localhost:8089 to start the test.
  Configure: 500 users, spawn rate 10/sec.

Scenarios tested:
  1. Health check (unauthenticated)
  2. Login flow
  3. Dashboard home (authenticated)
  4. Learning path fetch
  5. Practice test generation
  6. Practice test submission
  7. Current affairs feed
  8. Prediction viewing
  9. Analytics fetch
"""

import json
import random

from locust import HttpUser, task, between, tag


class UnauthenticatedUser(HttpUser):
    """Simulates users who are not logged in — hitting public endpoints."""
    weight = 2
    wait_time = between(1, 5)

    @tag("health")
    @task(5)
    def health_check(self):
        self.client.get("/api/v1/health")

    @tag("public")
    @task(3)
    def get_root(self):
        self.client.get("/")

    @tag("auth")
    @task(2)
    def attempt_login(self):
        self.client.post(
            "/api/v1/auth/login",
            json={
                "email": f"loadtest_{random.randint(1, 1000)}@example.com",
                "password": "TestPassword123!",
            },
            name="/api/v1/auth/login",
        )


class AuthenticatedStudent(HttpUser):
    """Simulates logged-in students using the platform."""
    weight = 8
    wait_time = between(2, 8)

    def on_start(self):
        """Login and store the access token."""
        # Try to login — in load test, use a pre-seeded test account
        resp = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "loadtest@ppsc-crack.pk",
                "password": "LoadTest2026!",
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token", "")
        else:
            # If login fails, use empty token (will get 401s — that's fine)
            self.token = ""

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    @tag("dashboard")
    @task(10)
    def dashboard_home(self):
        self.client.get("/api/v1/dashboard/home", headers=self.headers)

    @tag("learning")
    @task(6)
    def learning_path(self):
        # Use a placeholder job type ID
        self.client.get(
            "/api/v1/dashboard/learning-path/00000000-0000-0000-0000-000000000001",
            headers=self.headers,
            name="/api/v1/dashboard/learning-path/[id]",
        )

    @tag("practice")
    @task(4)
    def generate_practice_test(self):
        self.client.get(
            "/api/v1/student/practice/generate?num_questions=10&timed=false",
            headers=self.headers,
        )

    @tag("practice")
    @task(2)
    def submit_practice_test(self):
        # Simulate submission with random answers
        answers = [
            {"question_id": f"q_{i}", "selected_answer": random.choice(["a", "b", "c", "d"])}
            for i in range(10)
        ]
        self.client.post(
            "/api/v1/student/practice/submit",
            json={
                "test_id": "load-test-dummy",
                "answers": answers,
                "time_taken_seconds": random.randint(60, 600),
            },
            headers=self.headers,
        )

    @tag("current-affairs")
    @task(5)
    def current_affairs(self):
        self.client.get(
            "/api/v1/student/current-affairs?page=1",
            headers=self.headers,
        )

    @tag("predictions")
    @task(3)
    def predictions(self):
        self.client.get(
            "/api/v1/student/predictions/latest",
            headers=self.headers,
        )

    @tag("analytics")
    @task(3)
    def student_analytics(self):
        self.client.get("/api/v1/student/analytics", headers=self.headers)

    @tag("topics")
    @task(4)
    def browse_topics(self):
        self.client.get("/api/v1/job-types/", headers=self.headers)


class AdminUser(HttpUser):
    """Simulates admin users checking dashboards."""
    weight = 1
    wait_time = between(5, 15)

    def on_start(self):
        resp = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@ppsc-crack.pk",
                "password": "AdminTest2026!",
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token", "")
        else:
            self.token = ""

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    @tag("admin")
    @task(5)
    def admin_dashboard(self):
        self.client.get("/api/v1/admin/dashboard", headers=self.headers)

    @tag("admin")
    @task(3)
    def admin_analytics(self):
        self.client.get(
            "/api/v1/admin/analytics?period=30d",
            headers=self.headers,
        )

    @tag("admin")
    @task(2)
    def admin_papers(self):
        self.client.get("/api/v1/admin/papers", headers=self.headers)

    @tag("admin")
    @task(2)
    def admin_review_queue(self):
        self.client.get("/api/v1/admin/review-queue", headers=self.headers)
