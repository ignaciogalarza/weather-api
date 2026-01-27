"""Load test scenarios for Weather API using Locust."""

import random

from locust import HttpUser, between, tag, task


class WeatherAPIUser(HttpUser):
    """Simulates typical Weather API user behavior."""

    wait_time = between(0.5, 2.0)

    # Sample cities for testing
    CITIES = [
        "London",
        "Paris",
        "Tokyo",
        "New York",
        "Sydney",
        "Berlin",
        "Madrid",
        "Rome",
        "Toronto",
        "Singapore",
        "Mumbai",
        "Dubai",
        "Moscow",
        "Beijing",
        "Seoul",
    ]

    POPULAR_CITIES = ["London", "New York", "Tokyo", "Paris"]

    @task(1)
    @tag("health")
    def health_check(self) -> None:
        """Check health endpoint - lightweight baseline."""
        self.client.get("/health")

    @task(10)
    @tag("forecast")
    def get_forecast_random(self) -> None:
        """Get forecast for a random city."""
        city = random.choice(self.CITIES)
        with self.client.get(
            f"/forecast/{city}",
            name="/forecast/[city]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # City not found is expected for some edge cases
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(5)
    @tag("forecast", "popular")
    def get_forecast_popular(self) -> None:
        """Get forecast for popular cities (more cache-friendly)."""
        city = random.choice(self.POPULAR_CITIES)
        self.client.get(f"/forecast/{city}", name="/forecast/[popular]")

    @task(2)
    @tag("metrics")
    def check_metrics(self) -> None:
        """Verify metrics endpoint is accessible."""
        self.client.get("/metrics", name="/metrics")


class HealthCheckUser(HttpUser):
    """User that only checks health endpoint - for baseline testing."""

    wait_time = between(0.1, 0.5)
    weight = 1  # Lower weight than main user

    @task
    def health_check(self) -> None:
        """Rapid health check requests."""
        self.client.get("/health")


class HeavyUser(HttpUser):
    """Simulates heavy API user making many forecast requests."""

    wait_time = between(0.1, 0.5)
    weight = 1

    CITIES = ["London", "Paris", "Tokyo", "Berlin", "Sydney"]

    @task
    def rapid_forecast(self) -> None:
        """Rapid forecast requests to stress test the API."""
        city = random.choice(self.CITIES)
        self.client.get(f"/forecast/{city}", name="/forecast/[rapid]")
