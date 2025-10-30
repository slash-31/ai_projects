# Lab Tasks

**Active Lab Projects and Investigations**

---

## 🔬 Current Lab Tasks

### 1. Rental Property Repair Tracker - Cloud Run Deployment

**Status:** 🟡 In Progress

**Objective:** Deploy full-stack repair tracker application to Google Cloud Run with Cloudflare protection for workorder.arkhms.com domain.

**Project Location:**
- Source Code: `/home/slash-31/ai_projects/rentalproprepairtracker/`
- Terraform Config: `/home/slash-31/argolis_v2/rental-repair-tracker-terraform/`

**Architecture Overview:**
```
User Request
    ↓
Cloudflare Proxy (DDoS, SSL/TLS, CDN)
    ↓
[IP Allowlist Check - Only Cloudflare IPs]
    ↓
Cloud Run Frontend (React/Vite + Nginx)
    ↓
Cloud Run Backend (Node.js/Express)
    ↓
├─ Cloud SQL (PostgreSQL 14, db-f1-micro)
└─ Cloud Storage (File uploads)
```

**Key Components:**
1. **Backend Service:**
   - Node.js + Express + TypeScript
   - Google OAuth 2.0 authentication
   - PostgreSQL with auto-initialized schema
   - File uploads to Cloud Storage
   - Email notifications via Gmail API
   - Cloudflare IP validation middleware

2. **Frontend Service:**
   - React + TypeScript + Vite
   - Tailwind CSS styling
   - Protected routes with AuthContext
   - Axios API client

3. **Infrastructure:**
   - Cloud SQL PostgreSQL (private, no public IP)
   - Cloud Storage bucket with lifecycle rules
   - Secret Manager for sensitive config
   - Cloudflare for edge security

**Deployment Tasks:**

- [ ] **Understand Application Architecture**
  - [ ] Review backend API routes and authentication flow
  - [ ] Understand database schema and relationships
  - [ ] Study frontend component structure and routing
  - [ ] Review Docker build process for both services
  - [ ] Understand Cloudflare IP protection mechanism
  - [ ] Read: `/home/slash-31/ai_projects/rentalproprepairtracker/CLAUDE.md`

- [ ] **Setup Cloudflare Configuration**
  - [ ] Add DNS CNAME record: `workorder` → Cloud Run URL
  - [ ] Enable proxy (orange cloud icon)
  - [ ] Configure SSL/TLS to "Full (strict)"
  - [ ] Enable "Always Use HTTPS"
  - [ ] Enable HSTS (HTTP Strict Transport Security)
  - [ ] Set minimum TLS version to 1.2
  - [ ] Enable Automatic HTTPS Rewrites

- [ ] **Create Google OAuth Credentials**
  - [ ] Go to GCP Console → APIs & Services → Credentials
  - [ ] Create OAuth 2.0 Client ID (Web application)
  - [ ] Add authorized redirect URIs:
    - `http://localhost:3001/auth/google/callback` (development)
    - `https://workorder.arkhms.com/auth/google/callback` (production)
  - [ ] Save Client ID and Client Secret

- [ ] **Build and Push Docker Images**
  ```bash
  cd /home/slash-31/ai_projects/rentalproprepairtracker
  export PROJECT_ID="your-gcp-project-id"

  # Backend
  docker build -t gcr.io/${PROJECT_ID}/repair-tracker-backend:latest ./backend
  docker push gcr.io/${PROJECT_ID}/repair-tracker-backend:latest

  # Frontend
  docker build -t gcr.io/${PROJECT_ID}/repair-tracker-frontend:latest ./frontend
  docker push gcr.io/${PROJECT_ID}/repair-tracker-frontend:latest
  ```

- [ ] **Configure Terraform Variables**
  ```bash
  cd ~/argolis_v2/rental-repair-tracker-terraform
  cp terraform.tfvars.example terraform.tfvars
  vim terraform.tfvars
  ```
  - [ ] Set `project_id`
  - [ ] Set `gcs_bucket_name` (must be globally unique)
  - [ ] Set `db_password` (strong password)
  - [ ] Set `google_client_id` (from OAuth setup)
  - [ ] Set `google_client_secret` (from OAuth setup)
  - [ ] Generate `session_secret`: `openssl rand -base64 32`
  - [ ] Generate `jwt_secret`: `openssl rand -base64 32`
  - [ ] Set `frontend_url = "workorder.arkhms.com"`
  - [ ] Set `enable_cloudflare_protection = true`
  - [ ] Set `backend_image` and `frontend_image` URLs

- [ ] **Deploy Infrastructure**
  ```bash
  cd ~/argolis_v2/rental-repair-tracker-terraform
  terraform init
  terraform plan    # Review what will be created
  terraform apply   # Deploy (~5-10 minutes)
  ```

- [ ] **Verify Deployment**
  ```bash
  # Get service URLs
  terraform output backend_service_url
  terraform output frontend_service_url

  # Test through Cloudflare (should work)
  curl -I https://workorder.arkhms.com

  # Test direct Cloud Run access (should be blocked)
  curl -I https://<cloud-run-url>.run.app  # Expected: 403 Forbidden

  # Check for Cloudflare headers
  curl -I https://workorder.arkhms.com | grep -i cf-
  ```

- [ ] **Monitor and Verify**
  - [ ] Check backend logs: `gcloud run logs read repair-tracker-backend --region=us-east1`
  - [ ] Verify database connection in logs
  - [ ] Test user login flow
  - [ ] Create a test repair request
  - [ ] Upload a test file
  - [ ] Check Cloudflare Analytics dashboard

**Key Learning Objectives:**

1. **Application Architecture Understanding:**
   - How does session-based authentication work with Passport.js?
   - What is the data flow from frontend → backend → database?
   - How are files uploaded to Cloud Storage?
   - How does role-based access control work (tenant vs manager)?

2. **Cloud Run Deployment:**
   - How do Cloud Run services scale to zero?
   - What's the difference between Cloud Run and App Engine?
   - How does Cloud SQL private IP connection work?
   - Why use Secret Manager instead of environment variables?

3. **Cloudflare Integration:**
   - How does the IP allowlist middleware work?
   - What happens when Cloudflare IP list is refreshed?
   - Why is Cloudflare protection needed?
   - What's the difference between edge and application-level security?

4. **Terraform Infrastructure:**
   - How are modules organized (database, storage, cloudrun)?
   - How are secrets passed between modules?
   - What's the dependency chain (database → storage → cloudrun)?
   - How to update just the Cloud Run service without rebuilding everything?

**Documentation References:**
- Architecture & Setup: `/home/slash-31/ai_projects/rentalproprepairtracker/CLAUDE.md`
- Cloudflare Guide: `~/argolis_v2/rental-repair-tracker-terraform/CLOUDFLARE_SETUP.md`
- Deployment Summary: `~/argolis_v2/rental-repair-tracker-terraform/DEPLOYMENT_SUMMARY.md`
- Terraform README: `~/argolis_v2/rental-repair-tracker-terraform/README.md`
- Database Schema: `/home/slash-31/ai_projects/rentalproprepairtracker/docs/DATABASE.md`

**Estimated Time:** 2-3 hours (first deployment)

**Cost:** ~$18-32/month
- Cloud Run: $10-20
- Cloud SQL: $7-10
- Cloud Storage: $1-2
- Secret Manager: $0.30

---

### 2. BindPlane Agent Deployment for GKE Log Collection

**Status:** 🟡 Planning

**Objective:** Deploy BindPlane agent to collect logs from the GKE cluster and nodes, then forward them to SecOps.

**Investigation Areas:**
- BindPlane agent deployment architecture for GKE
  - DaemonSet vs Sidecar deployment model
  - Resource requirements and scaling considerations
- Log collection scope:
  - GKE cluster logs (control plane, API server, scheduler)
  - Node logs (kubelet, container runtime, OS-level logs)
  - Pod/Container logs (stdout/stderr)
  - Audit logs
- SecOps integration:
  - Authentication/authorization (service accounts, workload identity)
  - Network connectivity requirements
  - Log format and parsing requirements
  - Rate limits and quotas

**Key Questions to Answer:**
- [ ] What's the recommended BindPlane deployment pattern for GKE?
- [ ] How to configure log collection from both cluster and node levels?
- [ ] What permissions/IAM roles are needed for SecOps forwarding?
- [ ] How to handle log filtering and aggregation before forwarding?
- [ ] What's the network path from GKE private cluster to SecOps?

**Resources:**
- GKE Cluster: `us-central1-prod-gke-cluster`
- Project: `florida-prod-gke-101025`
- Network: Private cluster with NAT gateway

---

### 2. AdGuard Logs to SecOps Integration

**Status:** 🟡 Planning

**Objective:** Determine best approach to send AdGuard logs to SecOps - evaluate direct forwarding vs Cloud Storage bucket intermediary.

**Investigation Areas:**

#### Option A: Direct Log Forwarding
- AdGuard native log export capabilities
- Direct integration with SecOps ingestion API
- Real-time vs batch processing

#### Option B: Cloud Storage Bucket Intermediary
- Mount Google Cloud Storage bucket to AdGuard pods
- Create folder structure per host: `gs://bucket-name/{hostname}/logs/`
- SecOps ingests from bucket periodically
- Considerations:
  - FUSE mounting vs Cloud Storage API writes
  - File rotation and retention policies
  - SecOps bucket ingestion capabilities
  - Latency trade-offs (real-time vs batch)
  - Cost implications (storage + egress)

**Key Questions to Answer:**
- [ ] What log formats does SecOps support for ingestion?
- [ ] Does SecOps have native GCS bucket ingestion capability?
- [ ] What's the latency requirement for log availability in SecOps?
- [ ] How to handle log rotation and cleanup from bucket?
- [ ] What are the authentication requirements for bucket access?
- [ ] Can AdGuard write logs to mounted Cloud Storage efficiently?
- [ ] Performance impact of FUSE mounting vs direct writes?

**Current AdGuard Setup:**
- Namespace: `adguard`
- Replicas: 2
- Services: DNS (TCP/UDP), DoH, Web UI
- External IPs: See `README.md` → External IPs section

**Recommended Approach:** *(To be determined after investigation)*

---

## 📋 Task Priority

1. **High Priority:**
   - **Rental Property Repair Tracker deployment** (Learning Cloud Run + Cloudflare)
   - AdGuard → SecOps integration (critical for DNS security monitoring)

2. **Medium Priority:**
   - BindPlane GKE log collection setup

---

## 🔄 Investigation Workflow

For each task:
1. **Research phase:** Document findings, architecture options, pros/cons
2. **Design phase:** Create implementation plan with diagrams
3. **Proof of concept:** Test in lab environment
4. **Production deployment:** Deploy with monitoring and rollback plan
5. **Documentation:** Update relevant docs with configuration and procedures

---

## 📊 Related Documentation

- **GKE Deployment:** `GKE_DEPLOYMENT_STATUS.md`
- **Quick Commands:** `QUICK_REFERENCE.md`
- **Change History:** `CHANGE_LOG.md`
- **Terraform Code:** `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/`
- **Repair Tracker Project:** `/home/slash-31/ai_projects/rentalproprepairtracker/`
- **Repair Tracker Terraform:** `/home/slash-31/argolis_v2/rental-repair-tracker-terraform/`

## 🎓 Learning Resources

### Cloud Run Deep Dive
- How Cloud Run differs from GKE
- Container lifecycle and scaling
- Cold start optimization
- Secret Manager integration
- Cloud SQL connection patterns

### Full-Stack Application Architecture
- React + TypeScript frontend patterns
- Node.js/Express API design
- PostgreSQL schema design
- OAuth 2.0 authentication flow
- File upload handling with Cloud Storage

### Terraform Best Practices
- Module organization and reusability
- Secret management patterns
- Output chaining between modules
- State management considerations

---

**Last Updated:** 2025-10-30
**Next Review:** 2025-11-06
