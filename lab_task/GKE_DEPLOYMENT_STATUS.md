# GKE Cluster Deployment Status

**Project:** florida-prod-gke-101025
**Cluster:** us-central1-prod-gke-cluster
**Region:** us-central1
**Last Updated:** 2025-10-29

---

## 🟢 What's Currently Working

### Infrastructure Layer (Root Module)

#### ✅ GKE Cluster
- **Status:** Operational (6 nodes across 3 zones)
- **Configuration:** Regional, private cluster with authorized networks
- **Node Pool:** `us-central1-prod-default-pool`
- **Machine Type:** e2-standard-4
- **Nodes:** 2 per zone (6 total)
- **Master Endpoint:** Private with authorized networks enabled
- **Location:** `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/root/`

**Access Cluster:**
```bash
gcloud container clusters get-credentials us-central1-prod-gke-cluster \
  --region us-central1 --project florida-prod-gke-101025
```

#### ✅ VPC Networking
- **VPC:** `us-central1-prod-vpc`
- **Subnet:** `us-central1-prod-gke-subnet`
  - Primary CIDR: `172.27.32.0/24` (nodes)
  - Secondary CIDR (pods): `172.27.40.0/21`
  - Secondary CIDR (services): `172.27.50.0/24`
- **VPC Flow Logs:** ENABLED
  - Aggregation: 5 seconds
  - Sampling: 50%
  - Metadata: INCLUDE_ALL_METADATA
- **Private Google Access:** Enabled
- **Location:** `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/networking/main.tf`

#### ✅ Cloud NAT Gateway
- **Router:** `us-central1-prod-nat-router`
- **NAT Gateway:** `us-central1-prod-nat-gateway`
- **Configuration:** AUTO_ONLY IP allocation
- **Scope:** ALL_SUBNETWORKS_ALL_IP_RANGES
- **Logging:** ENABLED (filter: ALL)
- **Purpose:** Internet egress for private GKE nodes and pods

**Verify NAT:**
```bash
gcloud compute routers nats list --router=us-central1-prod-nat-router \
  --region=us-central1 --project=florida-prod-gke-101025
```

#### ✅ Firewall Rules (All with Logging Enabled)

| Rule Name | Purpose | Source | Ports | Logging |
|-----------|---------|--------|-------|---------|
| `us-central1-prod-gke-internal` | Internal cluster traffic | 172.27.32.0/24, 172.27.40.0/21, 172.27.50.0/24 | ALL | ✅ |
| `us-central1-prod-adguard-dns-external` | DNS queries | 6 authorized IPs | 53/TCP, 53/UDP | ✅ |
| `us-central1-prod-adguard-doh-external` | DNS-over-HTTPS | 6 authorized IPs | 443/TCP, 443/UDP | ✅ |
| `us-central1-prod-adguard-web-external` | AdGuard web UI | 45.21.151.99/32 | 3000/TCP | ✅ |
| `us-central1-prod-ssh-access` | SSH (not recommended - too open) | 0.0.0.0/0 | 22/TCP | ✅ |
| `k8s-fw-*` (4 GKE-managed rules) | Load balancer health checks | Various | Various | ✅ |

**Authorized IPs for AdGuard:**
1. `45.21.151.99/32` (Munich Network)
2. `68.70.225.213/32` (Network 2)
3. `68.103.59.243/32` (Network 3)
4. `47.147.24.137/32` (Network 4)
5. `208.115.150.123/32` (Network 5)
6. `20.118.171.229/32` (Network 6)

**View Firewall Rules:**
```bash
gcloud compute firewall-rules list --project=florida-prod-gke-101025 \
  --format="table(name,logConfig.enable,sourceRanges.list(),allowed[].map().firewall_rule().list())"
```

---

### Application Layer (Workloads Module)

#### ✅ AdGuard Home DNS Server
- **Status:** 2 replicas running
- **Namespace:** `adguard`
- **Image:** `adguard/adguardhome:latest`
- **Service Account:** `adguard-sa`
- **Pods:** `172.27.43.19`, `172.27.41.9` (pod IPs)
- **Location:** `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/helm/main.tf`

**Services & External IPs:**
| Service | Type | IP Address | Ports | Purpose |
|---------|------|------------|-------|---------|
| `adguard-dns-tcp` | LoadBalancer (External) | `35.202.44.179` | 53/TCP | DNS queries |
| `adguard-dns-udp` | LoadBalancer (External) | `34.172.169.29` | 53/UDP | DNS queries |
| `adguard-doh` | LoadBalancer (External) | `136.113.247.244` | 443/TCP+UDP | DNS-over-HTTPS |
| `adguard-web` | LoadBalancer (Internal) | `172.27.32.11` | 3000/TCP | Web UI (internal only) |

**DNS Configuration Example:**
```bash
# Test DNS resolution
dig @35.202.44.179 google.com

# Test DNS-over-HTTPS
curl -H 'accept: application/dns-json' \
  'https://136.113.247.244/dns-query?name=google.com&type=A'
```

**Access Web UI:**
- **From 45.21.151.99:** `http://<external-ip>:3000`
- **Via Twingate:** `http://172.27.32.11:3000`

**Check AdGuard Status:**
```bash
kubectl get pods -n adguard -o wide
kubectl get svc -n adguard
kubectl logs -n adguard -l app=adguard-home --tail=50
```

#### ✅ Twingate Zero-Trust Connector
- **Status:** 2 replicas running (ONLINE)
- **Namespace:** `twingate`
- **Image:** `twingate/connector:latest`
- **Service Account:** `twingate-connector-sa`
- **Pods:** `172.27.43.20`, `172.27.45.15` (pod IPs)
- **Network:** `securitydude.twingate.com`
- **Credentials:** Stored in Google Secret Manager
- **Location:** `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/twingate/main.tf`

**Secret Manager Integration:**
- `twingate-access-token` (version 2)
- `twingate-refresh-token` (version 2)
- `twingate-network-name` (version 5) - value: `securitydude`

**Check Twingate Status:**
```bash
kubectl get pods -n twingate -o wide
kubectl logs -n twingate -l app=twingate-connector --tail=50
# Look for: "State: Connected" in logs
```

**Update Twingate Secrets:**
```bash
# No trailing newline!
echo -n "new_token_value" | gcloud secrets versions add SECRET_NAME \
  --project=florida-prod-gke-101025 --data-file=-

# Restart connectors to pick up new tokens
kubectl rollout restart deployment/twingate-connector -n twingate
```

#### ✅ Other Namespaces
- **cribl:** Created but no workload deployed (`deploy_cribl = false`)
- **bindplane:** Created but no workload deployed (`deploy_bindplane = false`)

---

### Logging & Monitoring

#### ✅ Comprehensive Logging Enabled

**Infrastructure Logging:**
- VPC Flow Logs: ✅ (5-second intervals, 50% sampling)
- Cloud NAT Logs: ✅ (ALL filter)
- Firewall Logs: ✅ (9 rules - all custom + GKE-managed)
- Load Balancer Logs: ✅ (100% sample rate on all 4 AdGuard LBs)

**View Logs:**
```bash
# VPC Flow Logs
gcloud logging read "resource.type=gce_subnetwork AND resource.labels.subnetwork_name=us-central1-prod-gke-subnet" \
  --project=florida-prod-gke-101025 --limit=10

# Firewall Logs
gcloud logging read "resource.type=gce_firewall_rule" \
  --project=florida-prod-gke-101025 --limit=20

# Load Balancer Logs
gcloud logging read "resource.type=gce_network_tcp_lb_rule" \
  --project=florida-prod-gke-101025 --limit=20

# NAT Gateway Logs
gcloud logging read "resource.type=nat_gateway" \
  --project=florida-prod-gke-101025 --limit=10
```

---

## 🟡 What Needs Attention

### Security Improvements

#### ⚠️ SSH Firewall Rule Too Permissive
- **Current:** `us-central1-prod-ssh-access` allows 0.0.0.0/0
- **Risk:** SSH accessible from entire internet
- **Recommendation:** Restrict to authorized IPs only

**Fix:**
```bash
gcloud compute firewall-rules update us-central1-prod-ssh-access \
  --project=florida-prod-gke-101025 \
  --source-ranges=45.21.151.99/32,68.70.225.213/32,68.103.59.243/32,47.147.24.137/32,208.115.150.123/32,20.118.171.229/32
```

#### ⚠️ AdGuard Web UI External Access
- **Current:** Firewall allows 45.21.151.99/32 directly to port 3000
- **Issue:** Internal LB at 172.27.32.11 is only accessible from within VPC
- **Recommendation:** Access AdGuard Web UI ONLY via Twingate tunnel (zero-trust)
- **Optional:** Remove external firewall rule if Twingate-only access is sufficient

#### ⚠️ Network Policies Disabled
- **Current:** `enable_network_policies = false` in workloads tfvars
- **Risk:** No pod-to-pod network segmentation
- **Recommendation:** Enable GKE Network Policy addon and implement policies

**Enable Network Policies:**
```bash
gcloud container clusters update us-central1-prod-gke-cluster \
  --enable-network-policy \
  --region=us-central1 \
  --project=florida-prod-gke-101025
```

Then set `enable_network_policies = true` in `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/workloads/terraform.tfvars`

### Configuration Management

#### ⚠️ AdGuard Data Persistence
- **Current:** Using `emptyDir{}` volumes
- **Issue:** Data lost on pod restart (configuration, logs, query history)
- **Recommendation:** Migrate to Persistent Volume Claims (PVCs)

**Location:** `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/helm/main.tf` lines 225-233

---

## 🔴 Known Issues & Blockers

### Resolved Issues

#### ✅ Twingate Connector Authentication Failure (RESOLVED)
- **Error:** Connectors stuck in "Authentication" state, trying to reach `https://securitydude.twingate.com.twingate.com`
- **Root Cause:** Secret Manager stored full domain instead of subdomain
- **Fix:** Updated `twingate-network-name` secret to just `securitydude` (no `.twingate.com`)
- **Resolution Date:** 2025-10-29
- **Status:** Connectors now ONLINE

#### ✅ No Internet Connectivity from Pods (RESOLVED)
- **Error:** Twingate connectors showing "EOF reached" when trying to authenticate
- **Root Cause:** Private GKE cluster had no Cloud NAT gateway
- **Fix:** Created Cloud Router and NAT gateway via Terraform
- **Resolution Date:** 2025-10-29
- **Status:** All pods have internet egress

#### ✅ Terraform OAuth Authentication Errors (WORKAROUND)
- **Error:** `oauth2: "invalid_grant" "reauth related error (invalid_rapt)"`
- **Workaround:** Used `gcloud` commands directly instead of Terraform for some operations
- **Status:** Terraform state now consistent; all resources imported
- **Note:** May need to refresh application credentials periodically

---

## 🔵 Future Additions & Improvements

### Planned Features

#### 📋 High Priority

1. **Persistent Storage for AdGuard**
   - Replace emptyDir with GCE Persistent Disks
   - Implement automated backups to GCS bucket
   - Add restore procedure documentation

2. **TLS/SSL Certificates**
   - Generate Let's Encrypt certificates via cert-manager
   - Configure DNS-over-TLS (DoT) on port 853
   - Enable HTTPS for AdGuard web UI

3. **Monitoring & Alerting**
   - Deploy Prometheus + Grafana stack
   - Create dashboards for:
     - DNS query volume and latency
     - Twingate connection status
     - GKE node health and resource usage
   - Set up Google Cloud Monitoring alerts

4. **Network Policy Implementation**
   - Enable GKE Network Policy addon
   - Restrict AdGuard egress (DNS/NTP only)
   - Lock down Twingate connector communication

#### 📋 Medium Priority

5. **BindPlane Observability Pipeline**
   - Deploy BindPlane in the cluster
   - Configure log collection from AdGuard pods
   - Configure log collection from Twingate connector pods
   - Set up log ingestion pipeline to Google SecOps (Chronicle)
   - Enable structured logging with proper metadata tagging

6. **High Availability Improvements**
   - Increase AdGuard replicas to 3 (one per zone)
   - Implement pod anti-affinity rules
   - Configure pod disruption budgets (PDBs)

6. **Backup & Disaster Recovery**
   - Automate Terraform state backups
   - Document cluster rebuild procedure
   - Create etcd backup strategy

7. **CI/CD Pipeline**
   - Set up GitHub Actions or Cloud Build
   - Automated Terraform validation on PR
   - Blue/green deployments for workloads

8. **Cost Optimization**
   - Review load balancer usage (4 external IPs = $4/day)
   - Consider consolidating services
   - Implement autoscaling for node pools

#### 📋 Low Priority / Ideas

9. **Additional Workloads**
   - Cribl Stream for log processing
   - BindPlane OTEL for observability
   - Private Docker registry (Artifact Registry)

10. **Documentation**
    - Create network diagrams (Lucidchart/Draw.io)
    - Write incident response playbook
    - Document common troubleshooting steps

11. **Security Hardening**
    - Implement Pod Security Standards (PSS)
    - Enable Binary Authorization
    - Configure Workload Identity for pods

---

## 📂 Key Configuration Files

### Terraform Root Module (Infrastructure)
```
/home/slash-31/argolis_v2/prod-gke-gemini/deployed/root/
├── main.tf                  # Main orchestration
├── variables.tf             # Variable definitions (master_authorized_networks, etc.)
├── terraform.tfvars         # Actual values (EDIT THIS)
├── outputs.tf               # Cluster endpoint, network info
└── versions.tf              # Provider versions
```

### Terraform Workloads Module (Applications)
```
/home/slash-31/argolis_v2/prod-gke-gemini/deployed/workloads/
├── main.tf                  # Workload orchestration
├── variables.tf             # Variable definitions
├── terraform.tfvars         # Actual values (deploy flags, IPs)
└── outputs.tf               # Service IPs, endpoints
```

### Terraform Modules
```
/home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/
├── networking/              # VPC, subnets, firewall, NAT
├── gke/                     # GKE cluster configuration
├── helm/                    # AdGuard, Cribl, BindPlane deployments
├── twingate/                # Twingate connector with Secret Manager
└── ncc/                     # Network Connectivity Center
```

---

## 🔧 Common Commands

### Terraform Operations

**Root Module (Infrastructure):**
```bash
cd /home/slash-31/argolis_v2/prod-gke-gemini/deployed/root
export GOOGLE_APPLICATION_CREDENTIALS=/home/slash-31/junk/terraform-admin-jwt.json
terraform init
terraform plan
terraform apply
```

**Workloads Module (Applications):**
```bash
cd /home/slash-31/argolis_v2/prod-gke-gemini/deployed/workloads
export GOOGLE_APPLICATION_CREDENTIALS=/home/slash-31/junk/terraform-admin-jwt.json
terraform init
terraform plan
terraform apply
```

### Kubernetes Operations

**Check All Workloads:**
```bash
# Pods across all namespaces
kubectl get pods --all-namespaces -o wide

# Services with external IPs
kubectl get svc --all-namespaces

# Deployment status
for ns in adguard twingate cribl bindplane; do
  echo "=== $ns namespace ==="
  kubectl get deploy,pods,svc -n $ns
done
```

**View Logs:**
```bash
# AdGuard logs
kubectl logs -n adguard -l app=adguard-home --tail=100

# Twingate logs
kubectl logs -n twingate -l app=twingate-connector --tail=100

# Follow logs in real-time
kubectl logs -n adguard -l app=adguard-home --tail=50 -f
```

**Execute Commands in Pods:**
```bash
# Get shell in AdGuard pod
kubectl exec -it -n adguard <pod-name> -- /bin/sh

# Run one-off command
kubectl exec -n adguard <pod-name> -- ls -la /opt/adguardhome/
```

**Restart Deployments:**
```bash
kubectl rollout restart deployment/adguard-home -n adguard
kubectl rollout restart deployment/twingate-connector -n twingate
```

### GCP Operations

**View Firewall Rules:**
```bash
gcloud compute firewall-rules list --project=florida-prod-gke-101025
```

**Enable Firewall Logging:**
```bash
gcloud compute firewall-rules update RULE_NAME \
  --project=florida-prod-gke-101025 \
  --enable-logging \
  --logging-metadata=include-all
```

**Check NAT Gateway:**
```bash
gcloud compute routers nats describe us-central1-prod-nat-gateway \
  --router=us-central1-prod-nat-router \
  --region=us-central1 \
  --project=florida-prod-gke-101025
```

**View Secret Manager Secrets:**
```bash
# List secrets
gcloud secrets list --project=florida-prod-gke-101025

# View secret value (latest version)
gcloud secrets versions access latest \
  --secret=twingate-network-name \
  --project=florida-prod-gke-101025
```

---

## 📊 Resource Summary

### GCP Resources Created

| Resource Type | Count | Names |
|---------------|-------|-------|
| GKE Clusters | 1 | us-central1-prod-gke-cluster |
| Node Pools | 1 | us-central1-prod-default-pool (6 nodes) |
| VPCs | 1 | us-central1-prod-vpc |
| Subnets | 1 | us-central1-prod-gke-subnet |
| Cloud Routers | 1 | us-central1-prod-nat-router |
| Cloud NAT Gateways | 1 | us-central1-prod-nat-gateway |
| Firewall Rules | 9+ | 5 custom + 4+ GKE-managed |
| Load Balancers | 4 | 3 external + 1 internal |
| External IPs | 4 | 3 for AdGuard services + 1 for NAT |

### Kubernetes Resources Created

| Resource Type | Count | Namespaces |
|---------------|-------|------------|
| Namespaces | 4 | adguard, twingate, cribl, bindplane |
| Deployments | 2 | adguard-home (2 replicas), twingate-connector (2 replicas) |
| Pods | 4 | 2 AdGuard + 2 Twingate |
| Services | 4 | 3 external LBs + 1 internal LB |
| Service Accounts | 2 | adguard-sa, twingate-connector-sa |
| Secrets | 1 | twingate-connector-tokens |

### Estimated Monthly Costs

**GKE Cluster:**
- 6 x e2-standard-4 nodes: ~$340/month
- GKE cluster management fee: $73/month (regional cluster)

**Networking:**
- 4 external IP addresses: ~$120/month
- Load balancer forwarding rules: ~$60/month
- Egress traffic: Variable (estimate $50-100/month)

**Total Estimated Cost:** ~$650-700/month

---

## 🆘 Troubleshooting Guide

### Twingate Connectors Not Connecting

**Symptoms:**
- Pods show "Running" but logs indicate "State: Authentication" or "State: Offline"
- Errors about network unreachable or EOF reached

**Common Causes & Fixes:**

1. **Network name format incorrect:**
   ```bash
   # Check secret value
   gcloud secrets versions access latest --secret=twingate-network-name \
     --project=florida-prod-gke-101025 | cat -A

   # Should be: securitydude (no protocol, no .twingate.com, no trailing newline)
   # Fix if needed:
   echo -n "securitydude" | gcloud secrets versions add twingate-network-name \
     --project=florida-prod-gke-101025 --data-file=-
   ```

2. **Expired tokens:**
   - Regenerate tokens in Twingate admin console
   - Update secrets in Secret Manager
   - Restart deployment

3. **No internet connectivity:**
   - Check Cloud NAT gateway exists and is operational
   - Verify NAT logs for errors

### AdGuard Not Resolving DNS

**Symptoms:**
- DNS queries time out or get SERVFAIL
- `dig @35.202.44.179 google.com` fails

**Common Causes & Fixes:**

1. **Pods not ready:**
   ```bash
   kubectl get pods -n adguard
   # Should show 2/2 Running

   # If not, check logs:
   kubectl logs -n adguard -l app=adguard-home --tail=100
   ```

2. **Service has no external IP:**
   ```bash
   kubectl get svc -n adguard
   # Wait for EXTERNAL-IP to populate (can take 2-3 minutes)
   ```

3. **Firewall blocking queries:**
   ```bash
   # Verify your IP is in allowed list
   gcloud compute firewall-rules describe us-central1-prod-adguard-dns-external \
     --project=florida-prod-gke-101025 --format="get(sourceRanges)"
   ```

### Terraform Apply Failures

**Symptoms:**
- `Error: 409: resource already exists`
- `Error: oauth2: invalid_grant`

**Common Fixes:**

1. **Resource already exists:**
   ```bash
   # Import existing resource into Terraform state
   terraform import module.MODULE_NAME.RESOURCE_NAME RESOURCE_ID

   # Example:
   terraform import module.networking.google_compute_firewall.adguard_doh_external \
     projects/florida-prod-gke-101025/global/firewalls/us-central1-prod-adguard-doh-external
   ```

2. **OAuth errors:**
   - Re-authenticate: `gcloud auth application-default login`
   - Verify credentials: `echo $GOOGLE_APPLICATION_CREDENTIALS`
   - Use gcloud commands as workaround

### Pods Can't Access Internet

**Symptoms:**
- Pods can't pull images from Docker Hub
- Twingate connectors can't authenticate
- AdGuard can't resolve upstream DNS

**Fix:**
```bash
# Verify Cloud NAT exists
gcloud compute routers nats list --router=us-central1-prod-nat-router \
  --region=us-central1 --project=florida-prod-gke-101025

# Check NAT logs for errors
gcloud logging read "resource.type=nat_gateway" \
  --project=florida-prod-gke-101025 --limit=50
```

---

## 📚 Additional Resources

### Documentation
- **GKE Best Practices:** https://cloud.google.com/kubernetes-engine/docs/best-practices
- **Terraform GCP Provider:** https://registry.terraform.io/providers/hashicorp/google/latest/docs
- **AdGuard Home Docs:** https://github.com/AdguardTeam/AdGuardHome/wiki
- **Twingate Docs:** https://docs.twingate.com/docs

### Repository Structure
- **Main Repo:** `/home/slash-31/argolis_v2/`
- **GKE Deployment:** `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/`
- **Project Instructions:** `/home/slash-31/argolis_v2/CLAUDE.md`

---

**Last Audit Date:** 2025-10-29
**Next Review:** 2025-11-05
