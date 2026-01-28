"""Integration tests for the observability stack (Prometheus + Grafana).

These tests verify that:
1. Prometheus is scraping the weather-api correctly
2. Grafana datasource is properly configured
3. Grafana can query Prometheus
4. Dashboard is loaded correctly

Note: These tests require a running Kubernetes cluster with the observability
stack deployed. They are skipped if kubectl is not available or cluster
is not reachable.
"""

# ruff: noqa: S603, S607 - subprocess calls to kubectl are intentional for k8s testing

import subprocess

import pytest


def kubectl_available() -> bool:
    """Check if kubectl is available and cluster is reachable."""
    try:
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_kubectl(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    """Run a kubectl command and return the result."""
    return subprocess.run(
        ["kubectl", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_in_cluster(cmd: str, timeout: int = 60) -> str:
    """Run a command inside the cluster using kubectl exec on grafana pod."""
    # Use grafana pod which has wget available
    result = subprocess.run(
        [
            "kubectl", "exec", "deploy/grafana", "-c", "grafana", "--",
            "sh", "-c", cmd.replace("curl -s", "wget -qO-"),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    # Filter out container selection message
    output = result.stdout
    lines = output.split("\n")
    output = "\n".join(
        line for line in lines
        if "Defaulted container" not in line
    )
    return output.strip()


# Skip all tests in this module if kubectl is not available
pytestmark = pytest.mark.skipif(
    not kubectl_available(),
    reason="Kubernetes cluster not available",
)


class TestPrometheusIntegration:
    """Tests for Prometheus integration with weather-api."""

    def test_prometheus_is_running(self) -> None:
        """Prometheus deployment should be running."""
        result = run_kubectl([
            "get", "deployment", "prometheus",
            "-o", "jsonpath={.status.readyReplicas}",
        ])
        assert result.returncode == 0
        assert result.stdout.strip() in ["1", "2", "3"], "Prometheus not ready"

    def test_prometheus_scraping_weather_api(self) -> None:
        """Prometheus should be scraping weather-api target."""
        output = run_in_cluster(
            "curl -s 'http://prometheus:9090/api/v1/targets' | "
            "grep -o '\"job\":\"weather-api\"'"
        )
        assert '"job":"weather-api"' in output

    def test_prometheus_has_weather_api_metrics(self) -> None:
        """Prometheus should have weather-api metrics."""
        output = run_in_cluster(
            "curl -s 'http://prometheus:9090/api/v1/query?query=up{job=\"weather-api\"}'"
        )
        assert "success" in output
        assert "weather-api" in output

    def test_prometheus_service_discovery(self) -> None:
        """Prometheus should resolve weather-api service name."""
        output = run_in_cluster(
            "curl -s 'http://prometheus:9090/api/v1/targets' | "
            "grep -o 'weather-api:80'"
        )
        assert "weather-api:80" in output


class TestGrafanaIntegration:
    """Tests for Grafana integration."""

    def test_grafana_is_running(self) -> None:
        """Grafana deployment should be running."""
        result = run_kubectl([
            "get", "deployment", "grafana",
            "-o", "jsonpath={.status.readyReplicas}",
        ])
        assert result.returncode == 0
        assert result.stdout.strip() in ["1", "2", "3"], "Grafana not ready"

    def test_grafana_datasource_configured(self) -> None:
        """Grafana should have Prometheus datasource configured."""
        result = run_kubectl([
            "exec", "deploy/grafana", "--",
            "cat", "/etc/grafana/provisioning/datasources/datasources.yaml",
        ])
        assert result.returncode == 0
        assert "http://prometheus:9090" in result.stdout
        assert "editable: false" in result.stdout

    def test_grafana_datasource_not_editable(self) -> None:
        """Grafana datasource should not be editable."""
        result = run_kubectl([
            "exec", "deploy/grafana", "--",
            "cat", "/etc/grafana/provisioning/datasources/datasources.yaml",
        ])
        assert "editable: false" in result.stdout

    def test_grafana_can_reach_prometheus(self) -> None:
        """Grafana should be able to reach Prometheus."""
        result = run_kubectl([
            "exec", "deploy/grafana", "--",
            "wget", "-qO-", "http://prometheus:9090/api/v1/status/config",
        ])
        assert result.returncode == 0
        assert "success" in result.stdout

    def test_grafana_dashboard_loaded(self) -> None:
        """Grafana should have weather-api dashboard loaded."""
        result = run_kubectl([
            "exec", "deploy/grafana", "--",
            "ls", "/var/lib/grafana/dashboards/",
        ])
        assert result.returncode == 0
        assert "weather-api.json" in result.stdout

    def test_grafana_dashboard_not_editable(self) -> None:
        """Dashboard should be configured as non-editable."""
        result = run_kubectl([
            "exec", "deploy/grafana", "--",
            "cat", "/var/lib/grafana/dashboards/weather-api.json",
        ])
        assert result.returncode == 0
        # Check that editable is false in the dashboard JSON
        has_editable_false = '"editable": false' in result.stdout
        has_editable_false_compact = '"editable":false' in result.stdout
        assert has_editable_false or has_editable_false_compact


class TestServiceConnectivity:
    """Tests for Kubernetes service connectivity."""

    def test_prometheus_service_resolves(self) -> None:
        """Prometheus service should be resolvable."""
        output = run_in_cluster("nslookup prometheus 2>/dev/null | grep -i address")
        assert "Address" in output or "address" in output

    def test_grafana_service_resolves(self) -> None:
        """Grafana service should be resolvable."""
        output = run_in_cluster("nslookup grafana 2>/dev/null | grep -i address")
        assert "Address" in output or "address" in output

    def test_weather_api_service_resolves(self) -> None:
        """Weather-api service should be resolvable."""
        output = run_in_cluster("nslookup weather-api 2>/dev/null | grep -i address")
        assert "Address" in output or "address" in output

    def test_no_host_docker_internal_references(self) -> None:
        """No services should reference host.docker.internal."""
        # Check Grafana datasource config
        result = run_kubectl([
            "exec", "deploy/grafana", "--",
            "cat", "/etc/grafana/provisioning/datasources/datasources.yaml",
        ])
        assert "host.docker.internal" not in result.stdout

        # Check Prometheus config
        result = run_kubectl([
            "get", "configmap", "prometheus-config", "-o", "yaml",
        ])
        assert "host.docker.internal" not in result.stdout
