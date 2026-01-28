#!/usr/bin/env bash
set -euo pipefail

# Setup Kubernetes secrets from templates
# Usage: ./scripts/setup-secrets.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECRETS_DIR="$PROJECT_ROOT/k8s/secrets"

echo "Setting up Kubernetes secrets..."

# Grafana admin secret
GRAFANA_TEMPLATE="$SECRETS_DIR/grafana-admin.yaml.template"
GRAFANA_SECRET="$SECRETS_DIR/grafana-admin.yaml"

if [[ -f "$GRAFANA_SECRET" ]]; then
    echo "  grafana-admin.yaml already exists, skipping"
else
    if [[ -z "${GRAFANA_ADMIN_PASSWORD:-}" ]]; then
        echo "  Enter Grafana admin password (or set GRAFANA_ADMIN_PASSWORD env var):"
        read -rs GRAFANA_ADMIN_PASSWORD
    fi

    if [[ -z "$GRAFANA_ADMIN_PASSWORD" ]]; then
        echo "  Error: Password cannot be empty"
        exit 1
    fi

    envsubst < "$GRAFANA_TEMPLATE" > "$GRAFANA_SECRET"
    echo "  Created grafana-admin.yaml"
fi

echo "Done! Secret files created in $SECRETS_DIR"
echo ""
echo "Apply secrets to Kubernetes:"
echo "  kubectl apply -f $SECRETS_DIR/"
