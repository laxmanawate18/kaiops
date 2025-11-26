# KaiOPS GitHub-to-GKE Deployment Guide

Complete step-by-step guide to deploy KaiOPS from GitHub private repo to GCP GKE cluster.

## Prerequisites
- GCP Project created
- GKE cluster running (kaiops-gke)
- GitHub account with private repo access
- Git installed locally
- `gcloud` CLI installed and authenticated
- `kubectl` installed

---

## STEP 1: Setup GitHub Private Repository

### 1.1 Create Private Repository on GitHub

```bash
# Navigate to GitHub and create a new private repository
# Repository URL: https://github.com/YOUR_USERNAME/kaiops-sre-agent (private)
```

### 1.2 Initialize Git in Your Local Project

```bash
cd f:\Personal\AI-Project\kaiops-agent\sre-agent-main

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: KaiOPS SRE Agent deployment ready"

# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/kaiops-sre-agent.git

# Push to GitHub (main branch)
git branch -M main
git push -u origin main
```

### 1.3 Generate GitHub Personal Access Token (PAT)

```
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes:
   - repo (full control of private repositories)
   - workflow (update GitHub Action workflows)
4. Copy and save the token (you'll need it for GCP)
```

---

## STEP 2: Setup GCP Project Configuration

### 2.1 Set Environment Variables

```bash
# Set your GCP project details
export GCP_PROJECT_ID="your-gcp-project-id"
export GKE_CLUSTER_NAME="kaiops-gke"
export GKE_ZONE="us-central1-a"
export GKE_REGION="us-central1"
export DOCKER_REGISTRY="gcr.io/$GCP_PROJECT_ID"
```

### 2.2 Enable Required GCP APIs

```bash
gcloud services enable \
  container.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  compute.googleapis.com \
  servicenetworking.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com
```

### 2.3 Create GCP Service Account for Cloud Build

```bash
# Create service account
gcloud iam service-accounts create cloud-build-sa \
  --display-name="Cloud Build Service Account for KaiOPS"

# Get service account email
export SA_EMAIL="cloud-build-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Grant necessary roles
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member=serviceAccount:$SA_EMAIL \
  --role=roles/container.developer

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member=serviceAccount:$SA_EMAIL \
  --role=roles/storage.admin

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member=serviceAccount:$SA_EMAIL \
  --role=roles/cloudbuild.builds.editor

# Create and download service account key
gcloud iam service-accounts keys create ~/cloud-build-key.json \
  --iam-account=$SA_EMAIL
```

---

## STEP 3: Create GitHub Secrets for GCP Access

### 3.1 Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

#### 3.1.1 GCP Project Information
**Name:** `GCP_PROJECT_ID`
**Value:** `your-gcp-project-id`

**Name:** `GKE_CLUSTER_NAME`
**Value:** `kaiops-gke`

**Name:** `GKE_ZONE`
**Value:** `us-central1-a`

**Name:** `GKE_REGION`
**Value:** `us-central1`

#### 3.1.2 GCP Service Account Key
**Name:** `GCP_SA_KEY`
**Value:** (Content of `~/cloud-build-key.json`)

```bash
# On your local machine, display the key content and copy it
cat ~/cloud-build-key.json
```

---

## STEP 4: Setup Docker Registry Push Permissions

### 4.1 Configure Docker Authentication for GCR

```bash
# Configure gcloud auth for Docker
gcloud auth configure-docker gcr.io

# Create GCR service account for Docker push
gcloud iam service-accounts create gcr-push-sa \
  --display-name="GCR Push Service Account"

export GCR_SA_EMAIL="gcr-push-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Grant Storage Admin role for GCR
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member=serviceAccount:$GCR_SA_EMAIL \
  --role=roles/storage.admin

# Create key for GitHub Actions
gcloud iam service-accounts keys create ~/gcr-push-key.json \
  --iam-account=$GCR_SA_EMAIL

# Add to GitHub secrets
# Name: GCR_JSON_KEY
# Value: (Content of ~/gcr-push-key.json)
```

---

## STEP 5: Create GitHub Actions Workflow

### 5.1 Create Workflow File

Create `.github/workflows/deploy-to-gke.yml` in your repository

See `github-actions-workflow.yml` in the deployment scripts

### 5.2 Commit and Push Workflow

```bash
git add .github/workflows/deploy-to-gke.yml
git commit -m "Add GitHub Actions deployment workflow"
git push origin main
```

---

## STEP 6: Prepare GKE Cluster

### 6.1 Create Namespaces

```bash
# Get GKE credentials
gcloud container clusters get-credentials $GKE_CLUSTER_NAME --zone $GKE_ZONE

# Create namespaces
kubectl create namespace kaiops
kubectl create namespace redis
kubectl create namespace monitoring
```

### 6.2 Create Service Account in GKE

```bash
# Create service account for deployments
kubectl create serviceaccount kaiops-deployer -n kaiops

# Create role binding
kubectl create clusterrolebinding kaiops-deployer-binding \
  --clusterrole=cluster-admin \
  --serviceaccount=kaiops-deployer:kaiops-deployer
```

### 6.3 Get GKE Service Account Token

```bash
# Get the token for GKE auth
kubectl get secret $(kubectl get secret -n kaiops | grep kaiops-deployer | awk '{print $1}') \
  -n kaiops -o jsonpath='{.data.token}' | base64 -d

# Also get cluster CA certificate
kubectl config view --raw --flatten --minify > ~/.kube/config-kaiops
```

---

## STEP 7: Setup Cloud Build Trigger (Alternative to GitHub Actions)

### 7.1 Connect GitHub to Cloud Build

```bash
# Create a Cloud Build trigger connected to GitHub
gcloud builds connect \
  --repository-name=kaiops-sre-agent \
  --repository-owner=YOUR_GITHUB_USERNAME \
  --region=us-central1
```

### 7.2 Create Trigger Configuration

```bash
gcloud builds triggers create github \
  --name="kaiops-deploy-trigger" \
  --repo-name=kaiops-sre-agent \
  --repo-owner=YOUR_GITHUB_USERNAME \
  --branch-pattern="^main$" \
  --build-config=kubernetes/cloudbuild.yaml \
  --region=us-central1
```

---

## STEP 8: Setup Database Connections

### 8.1 MongoDB/Cosmos DB Connection

Create a secret with your database connection string:

```bash
# Create secret with MongoDB URI
kubectl create secret generic kaiops-secrets -n kaiops \
  --from-literal=MONGODB_URI="mongodb+srv://username:password@cluster0.mongodb.net/sre_agent_db?retryWrites=true&w=majority" \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 8.2 Update Kubernetes Manifests

Edit `kubernetes/kaiops-deployment.yaml` and replace:
- `YOUR_COSMOS_DB_CONNECTION_STRING` with your actual MongoDB URI
- `YOUR_GCP_PROJECT_ID` with your project ID

---

## STEP 9: Deploy Redis Cache

### 9.1 Deploy Redis StatefulSet

```bash
# Apply Redis deployment
kubectl apply -f kubernetes/redis-statefulset.yaml

# Verify Redis is running
kubectl get pods -n redis
kubectl logs -f deployment/redis -n redis
```

---

## STEP 10: Initial Manual Deployment (First Time)

### 10.1 Push Initial Code to GitHub

```bash
cd f:\Personal\AI-Project\kaiops-agent\sre-agent-main

# Make sure all changes are committed
git status
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 10.2 Monitor GitHub Actions/Cloud Build

- **GitHub Actions**: Go to your repo → Actions tab → Select workflow run
- **Cloud Build**: Go to GCP Console → Cloud Build → Build History

### 10.3 Deploy Initial Manifests

```bash
# Apply Kubernetes manifests
kubectl apply -f kubernetes/kaiops-deployment.yaml -n kaiops

# Check deployment status
kubectl rollout status deployment/kaiops-backend -n kaiops --timeout=5m
kubectl rollout status deployment/kaiops-frontend -n kaiops --timeout=5m

# Check pods
kubectl get pods -n kaiops -o wide
```

---

## STEP 11: Verify Deployment

### 11.1 Check Services

```bash
# Get service endpoints
kubectl get svc -n kaiops
kubectl get svc -n redis

# Port forward to test locally
kubectl port-forward -n kaiops svc/kaiops-backend 8000:8000 &
kubectl port-forward -n kaiops svc/kaiops-frontend 3000:80 &
```

### 11.2 Check Logs

```bash
# Backend logs
kubectl logs -f deployment/kaiops-backend -n kaiops

# Frontend logs
kubectl logs -f deployment/kaiops-frontend -n kaiops

# Redis logs
kubectl logs -f statefulset/redis -n redis
```

### 11.3 Test API

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000
```

---

## STEP 12: Setup Continuous Deployment

### 12.1 Enable Auto-deploy on Push

The workflow in `.github/workflows/deploy-to-gke.yml` automatically triggers on pushes to main branch.

```bash
# Any push to main will trigger:
# 1. Build Docker images
# 2. Push to GCR
# 3. Deploy to GKE
# 4. Run health checks
```

### 12.2 Monitor Deployments

```bash
# Watch deployment progress
kubectl rollout status deployment/kaiops-backend -n kaiops --watch

# View recent events
kubectl get events -n kaiops --sort-by='.lastTimestamp'

# Check Cloud Build logs
gcloud builds log $(gcloud builds list --limit=1 --format='value(id)')
```

---

## Troubleshooting

### Issue: Images not pushing to GCR
```bash
# Verify service account has storage.admin role
gcloud projects get-iam-policy $GCP_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/storage.admin"

# Re-authenticate Docker
gcloud auth configure-docker gcr.io
```

### Issue: Pod fails to pull image
```bash
# Check image exists in GCR
gcloud container images list --repository=gcr.io/$GCP_PROJECT_ID

# Check pod events
kubectl describe pod <pod-name> -n kaiops
```

### Issue: Deployment stuck in pending
```bash
# Check resource limits
kubectl top nodes
kubectl describe nodes

# Check pod logs
kubectl logs <pod-name> -n kaiops --previous
```

### Issue: Database connection fails
```bash
# Verify MongoDB URI secret
kubectl get secret kaiops-secrets -n kaiops -o yaml

# Check backend logs for connection errors
kubectl logs deployment/kaiops-backend -n kaiops | grep -i mongo
```

---

## Useful Commands

```bash
# Get deployment info
kubectl get all -n kaiops
kubectl describe deployment kaiops-backend -n kaiops

# Scale deployment
kubectl scale deployment kaiops-backend -n kaiops --replicas=3

# Trigger rolling update
kubectl set image deployment/kaiops-backend \
  kaiops-backend=gcr.io/$GCP_PROJECT_ID/kaiops-backend:latest -n kaiops

# View deployment history
kubectl rollout history deployment/kaiops-backend -n kaiops

# Rollback deployment
kubectl rollout undo deployment/kaiops-backend -n kaiops

# Delete deployment
kubectl delete deployment kaiops-backend -n kaiops
kubectl delete namespace kaiops
```

---

## Next Steps

1. ✅ Setup GitHub private repo
2. ✅ Create GCP service accounts
3. ✅ Add GitHub secrets
4. ✅ Create GitHub Actions workflow
5. ✅ Prepare GKE cluster
6. ✅ Deploy databases
7. ✅ Initial deployment
8. Continue with monitoring, logging, and scaling configurations
