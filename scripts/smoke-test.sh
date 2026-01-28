#!/bin/bash
# Smoke test script for post-deployment validation
# Usage: ./scripts/smoke-test.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED=0
PASSED=0

check() {
    local name="$1"
    local cmd="$2"

    printf "  %-50s " "$name"
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC}"
        ((FAILED++))
    fi
}

echo ""
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║                    SMOKE TEST SUITE                          ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi

# Check cluster connectivity
echo -e "${YELLOW}[1/6] Cluster Connectivity${NC}"
check "Kubernetes cluster reachable" "kubectl cluster-info"
check "Default namespace accessible" "kubectl get pods"
echo ""

# Check deployments
echo -e "${YELLOW}[2/6] Deployments${NC}"
check "weather-api deployment ready" "kubectl get deployment weather-api -o jsonpath='{.status.readyReplicas}' | grep -q '[1-9]'"
check "redis deployment ready" "kubectl get deployment redis -o jsonpath='{.status.readyReplicas}' | grep -q '[1-9]'"
check "prometheus deployment ready" "kubectl get deployment prometheus -o jsonpath='{.status.readyReplicas}' | grep -q '[1-9]'"
check "grafana deployment ready" "kubectl get deployment grafana -o jsonpath='{.status.readyReplicas}' | grep -q '[1-9]'"
echo ""

# Check services
echo -e "${YELLOW}[3/6] Services${NC}"
check "weather-api service exists" "kubectl get svc weather-api"
check "redis service exists" "kubectl get svc redis"
check "prometheus service exists" "kubectl get svc prometheus"
check "grafana service exists" "kubectl get svc grafana"
echo ""

# Check pod health
echo -e "${YELLOW}[4/6] Pod Health${NC}"
check "weather-api pods running" "kubectl get pods -l app=weather-api -o jsonpath='{.items[*].status.phase}' | grep -q Running"
check "weather-api no restarts" "[ \$(kubectl get pods -l app=weather-api -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}') -lt 5 ]"
check "All pods healthy" "[ \$(kubectl get pods --field-selector=status.phase!=Running,status.phase!=Succeeded 2>/dev/null | wc -l) -eq 0 ]"
echo ""

# Check endpoints
echo -e "${YELLOW}[5/6] Endpoint Health (via kubectl exec)${NC}"
check "Health endpoint responds" "kubectl run smoke-health --rm -i --restart=Never --image=curlimages/curl:latest -- curl -sf http://weather-api/health 2>/dev/null"
check "Metrics endpoint responds" "kubectl run smoke-metrics --rm -i --restart=Never --image=curlimages/curl:latest -- curl -sf http://weather-api/metrics 2>/dev/null | head -1"
check "Forecast endpoint responds" "kubectl run smoke-forecast --rm -i --restart=Never --image=curlimages/curl:latest -- curl -sf http://weather-api/forecast/London 2>/dev/null"
echo ""

# Check observability stack
echo -e "${YELLOW}[6/6] Observability Stack${NC}"
check "Prometheus scraping weather-api" "kubectl run smoke-prom --rm -i --restart=Never --image=curlimages/curl:latest -- curl -sf 'http://prometheus:9090/api/v1/query?query=up{job=\"weather-api\"}' 2>/dev/null | grep -q success"
check "Grafana datasource configured" "kubectl exec deploy/grafana -- wget -qO- --header=\"Authorization: Basic \$(echo -n 'admin:CHANGE_ME_BEFORE_PRODUCTION' | base64)\" http://localhost:3000/api/datasources 2>/dev/null | grep -q prometheus"
check "Grafana can query Prometheus" "kubectl exec deploy/grafana -- wget -qO- --header=\"Authorization: Basic \$(echo -n 'admin:CHANGE_ME_BEFORE_PRODUCTION' | base64)\" 'http://localhost:3000/api/datasources/proxy/1/api/v1/query?query=up' 2>/dev/null | grep -q success"
check "Redis connectivity" "kubectl exec deploy/redis -- redis-cli ping | grep -q PONG"
echo ""

# Summary
echo -e "${YELLOW}══════════════════════════════════════════════════════════════${NC}"
echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED ($PASSED/$((PASSED+FAILED)))${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED ($FAILED failed, $PASSED passed)${NC}"
    exit 1
fi
