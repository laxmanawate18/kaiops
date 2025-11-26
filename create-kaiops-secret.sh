#!/bin/bash
# Script to create kaiops-secrets in Kubernetes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Creating KaiOPS secrets in Kubernetes...${NC}"

# Get credentials from .env file
source sre-agent-backend/.env

# Create namespace if it doesn't exist
kubectl create namespace kaiops --dry-run=client -o yaml | kubectl apply -f -

# Delete existing secret if it exists
kubectl delete secret kaiops-secrets -n kaiops 2>/dev/null

# Create the secret with all required environment variables
kubectl create secret generic kaiops-secrets -n kaiops \
  --from-literal=MONGODB_URI="$MONGODB_URI" \
  --from-literal=MONGODB_DATABASE="$MONGODB_DATABASE" \
  --from-literal=GITHUB_TOKEN="$GITHUB_TOKEN" \
  --from-literal=AZURE_CLIENT_ID="$AZURE_CLIENT_ID" \
  --from-literal=AZURE_TENANT_ID="$AZURE_TENANT_ID" \
  --from-literal=AZURE_CLIENT_SECRET="$AZURE_CLIENT_SECRET" \
  --from-literal=AZURE_SUBSCRIPTION_ID="$AZURE_SUBSCRIPTION_ID" \
  --from-literal=LOG_ANALYTICS_WORKSPACE_ID="$LOG_ANALYTICS_WORKSPACE_ID" \
  --from-literal=AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  --from-literal=AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  --from-literal=AWS_REGION="$AWS_REGION" \
  --from-literal=AWS_ACCOUNT_ID="$AWS_ACCOUNT_ID" \
  --from-literal=AWS_CLUSTER_NAME="$AWS_CLUSTER_NAME" \
  --from-literal=AWS_CLOUDWATCH_LOG_GROUP="$AWS_CLOUDWATCH_LOG_GROUP" \
  --from-literal=GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  --from-literal=GOOGLE_PROJECT_ID="$GOOGLE_PROJECT_ID" \
  --from-literal=GOOGLE_CREDENTIALS_PATH="/etc/secrets/gcp-credentials.json" \
  --from-literal=GEMINI_MODEL="$GEMINI_MODEL" \
  --from-literal=MODEL_TEMPERATURE="$MODEL_TEMPERATURE" \
  --from-literal=GRAFANA_URL="$GRAFANA_URL" \
  --from-literal=GRAFANA_SERVICE_ACCOUNT_TOKEN="$GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --from-literal=GRAFANA_ORG_ID="$GRAFANA_ORG_ID" \
  --from-literal=ARGOCD_URL="$ARGOCD_URL" \
  --from-literal=ARGOCD_AUTH_TOKEN="$ARGOCD_AUTH_TOKEN" \
  --from-literal=REDIS_URL="redis://redis-service.redis.svc.cluster.local:6379/0" \
  --from-literal=CACHE_TTL_METADATA="$CACHE_TTL_METADATA" \
  --from-literal=CACHE_TTL_APPLICATIONS="$CACHE_TTL_APPLICATIONS" \
  --from-literal=CACHE_TTL_USERS="$CACHE_TTL_USERS" \
  --from-literal=CACHE_TTL_FEEDBACK="$CACHE_TTL_FEEDBACK"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Secret created successfully${NC}"
    
    # Verify the secret was created
    echo -e "${YELLOW}Verifying secret...${NC}"
    kubectl get secret kaiops-secrets -n kaiops
    
    echo -e "${GREEN}✓ KaiOPS secret setup complete!${NC}"
else
    echo -e "${RED}✗ Failed to create secret${NC}"
    exit 1
fi
