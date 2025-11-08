# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a personal AI-assisted projects repository containing multiple independent projects and lab experiments. The repository serves as a central workspace for various technical projects, infrastructure deployments, and learning activities.

## Repository Structure

This is a **multi-project repository** with the following main directories:

### 1. `rentalproprepairtracker/`
Full-stack rental property repair tracking application with Google Cloud Platform deployment.

**Tech Stack**: Node.js/Express backend, React/TypeScript frontend, PostgreSQL, Google Cloud Run
**Documentation**: See `rentalproprepairtracker/CLAUDE.md` for complete architecture, development commands, and deployment procedures.

**Quick Commands**:
```bash
cd rentalproprepairtracker
npm run dev              # Run both frontend + backend
npm run build           # Build for production
npm run install:all     # Install all dependencies
```

### 2. `lab_task/`
GKE cluster deployment documentation and operational procedures for production Kubernetes infrastructure.

**Purpose**: Track and document the `florida-prod-gke-101025` GKE cluster running AdGuard DNS and Twingate.
**Documentation**: See `lab_task/CLAUDE.md` and `lab_task/README.md` for cluster operations, troubleshooting, and maintenance procedures.

**Key Files**:
- `GKE_DEPLOYMENT_STATUS.md` - Complete infrastructure status
- `QUICK_REFERENCE.md` - Common kubectl and gcloud commands
- `CHANGE_LOG.md` - Chronological change history
- `LAB_TASKS.md` - Active lab experiments and learning objectives

### 3. `find_new_laptop/`
Research and comparison notes for laptop/device procurement.

**Contains**: Comparative analysis documents and device specifications.

### 4. `scripts/`
Utility scripts directory (currently empty).

## Working in This Repository

### Project Selection
When the user mentions work on a specific project:
- **"rental repair tracker"** or **"workorder"** → Work in `rentalproprepairtracker/`
- **"GKE"**, **"AdGuard"**, **"Twingate"**, or **"lab tasks"** → Work in `lab_task/`
- **"laptop"** or **"device research"** → Work in `find_new_laptop/`

### Key Architectural Patterns

**Rental Repair Tracker**:
- Monorepo with npm workspaces (`backend/` and `frontend/`)
- Cloud Run deployment with Terraform infrastructure-as-code
- Cloud SQL PostgreSQL with Unix socket connection in production
- Session-based authentication with Google OAuth 2.0
- Cloudflare edge protection for production domain

**GKE Lab Infrastructure**:
- Private GKE cluster with NAT gateway for egress
- Terraform modules in separate repository: `/home/slash-31/argolis_v2/prod-gke-gemini/`
- Kubernetes workloads: AdGuard (DNS filtering), Twingate (zero-trust access)
- Documentation-driven operations (all changes logged)

### Git Workflow

This repository uses straightforward git commits:
```bash
git status
git add <files>
git commit -m "descriptive message"
git push
```

**Commit Message Style** (based on git history):
- Use lowercase, descriptive messages
- Start with action: "docs:", "add", "update", "fix"
- Examples: "docs: add network infrastructure documentation", "updates"

### Network Infrastructure Context

The repository documents infrastructure across multiple sites:

**Munich Site**:
- 10.0.128.0/24 (Core Network)
- 10.0.129.0/24 (IoT Network)
- 10.0.130.0/24 (Management Network)
- 10.0.132.0/24 (Docker Network)

**BinaryFU Site**:
- 10.101.53.0/24 (JK Network - divided into 4x /27 subnets)
- 10.101.12.0/24 (OOB Management)
- 10.101.20.0/24 (Core Servers)

**Other Sites**:
- 192.168.1.0/24 (WillowCreek)
- 192.168.12.0/24 (Davis)

These networks are referenced in firewall rules, GKE cluster configuration, and Twingate access policies.

## Related External Repositories

**Terraform Infrastructure Code**:
- `/home/slash-31/argolis_v2/prod-gke-gemini/` - GKE cluster infrastructure
- `/home/slash-31/argolis_v2/rental-repair-tracker-terraform/` - Repair tracker Cloud Run deployment

These are separate git repositories managing infrastructure-as-code for the projects documented in this repository.

## Documentation Standards

### When Creating New Projects
1. Create a dedicated directory for the project
2. Add a `CLAUDE.md` file with:
   - Project overview and purpose
   - Architecture and tech stack
   - Development commands (install, dev, build, test)
   - Deployment procedures
   - Common patterns and gotchas
3. Update this root `CLAUDE.md` to reference the new project

### When Working with Lab Tasks
- Document all infrastructure changes in `lab_task/CHANGE_LOG.md`
- Update `lab_task/GKE_DEPLOYMENT_STATUS.md` with current status
- Add useful commands to `lab_task/QUICK_REFERENCE.md`
- Check `lab_task/LAB_TASKS.md` for active experiments and learning objectives

### Documentation Philosophy
- **Status over history**: Maintain current state documents (`*_STATUS.md`)
- **Change logging**: Track all changes chronologically (`CHANGE_LOG.md`)
- **Quick reference**: One-liner commands for daily operations (`QUICK_REFERENCE.md`)
- **Learning focus**: Document not just "how" but "why" for educational value

## Common Scenarios

### Scenario: Working on Rental Repair Tracker
```bash
cd rentalproprepairtracker
# See rentalproprepairtracker/CLAUDE.md for all commands
npm run dev              # Local development
npm run build           # Build for production
```

Reference: `rentalproprepairtracker/CLAUDE.md` for complete architecture, API routes, database schema, and deployment procedures.

### Scenario: GKE Cluster Operations
```bash
# Authenticate
export GOOGLE_APPLICATION_CREDENTIALS=/home/slash-31/junk/terraform-admin-jwt.json
gcloud container clusters get-credentials us-central1-prod-gke-cluster \
  --region us-central1 --project florida-prod-gke-101025

# Check status
kubectl get pods -A
kubectl get svc -A
```

Reference: `lab_task/QUICK_REFERENCE.md` for common operations.

### Scenario: Infrastructure Changes
1. Make the change (Terraform, kubectl, gcloud)
2. Document in `lab_task/CHANGE_LOG.md`
3. Update `lab_task/GKE_DEPLOYMENT_STATUS.md`
4. Test and verify
5. Commit changes to this repository

### Scenario: New Lab Experiment
1. Review `lab_task/LAB_TASKS.md` for active tasks
2. Create new section with:
   - Objective
   - Investigation areas
   - Key questions
   - Resources needed
3. Document findings as you progress
4. Update status when complete or blocked

## Project-Specific Notes

### Rental Repair Tracker
- **Monorepo**: Uses npm workspaces, always run commands from root or with `--workspace=backend|frontend`
- **Database**: Auto-initializes schema on backend startup (no formal migration system)
- **Cloud Run**: Backend must listen on port 8080, use Unix socket for Cloud SQL
- **Secrets**: Stored in GCP Secret Manager, not in environment variables
- **Cloudflare**: Production domain uses IP allowlist middleware to only accept Cloudflare IPs

### GKE Lab Cluster
- **Private Cluster**: No direct internet access, uses NAT gateway for egress
- **Terraform State**: Remote state stored in GCS bucket
- **Workload Identity**: GKE pods use Google service accounts via Workload Identity
- **Firewall Rules**: All rules have logging enabled for security auditing
- **AdGuard**: 2 replicas with external LoadBalancer IPs for DNS services
- **Twingate**: 2 replicas for high availability zero-trust access

## Important File Locations

**Application Code**:
- Rental Repair Tracker: `/home/slash-31/ai_projects/rentalproprepairtracker/`

**Infrastructure Code (External)**:
- GKE Terraform: `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/`
- Repair Tracker Terraform: `/home/slash-31/argolis_v2/rental-repair-tracker-terraform/`

**Credentials**:
- Terraform Admin SA: `/home/slash-31/junk/terraform-admin-jwt.json`

**Documentation**:
- GKE Operations: `lab_task/` directory
- Project-specific: Each project's `CLAUDE.md` file
