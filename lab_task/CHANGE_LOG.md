# GKE Cluster Change Log

**Track all changes, deployments, and configuration updates.**

---

## 2025-10-29 - Security Hardening Phase 2: Pod Security & Persistent Storage

### Summary
Implemented 4 security hardening recommendations: Network policies, SSH firewall restriction, persistent storage for AdGuard, and Pod Security Standards across all namespaces.

### Changes Made

#### ✅ SSH Firewall Restriction
- **Rule**: `us-central1-prod-ssh-access`
- **Changed from**: `0.0.0.0/0` (entire internet)
- **Changed to**: 6 specific authorized IPs
- **Impact**: High - Prevents unauthorized SSH access to cluster nodes

#### ✅ Persistent Storage for AdGuard
- **Created**: `adguard-config-pvc` (5Gi, RWO, standard-rwo)
- **Created**: `adguard-data-pvc` (10Gi, RWO, standard-rwo)
- **Result**: AdGuard configuration now persists across pod restarts
- **Constraint**: RWO requires single replica (changed from 2 to 1)
- **File**: `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/workloads/terraform.tfvars:23`

#### ✅ Pod Security Standards
- **Applied**: Baseline policy to all namespaces (adguard, twingate, cribl, bindplane)
- **Security contexts**: Added to all pod/container specs
- **Capabilities**: NET_BIND_SERVICE for AdGuard (port 53, 443)
- **Seccomp**: RuntimeDefault profile enabled
- **Files**:
  - `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/helm/main.tf:33-35,208-290`
  - `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/twingate/main.tf:70-72`

#### ✅ Network Policies
- **Created**: `adguard-access-policy` (ingress restrictions)
- **Created**: `twingate-egress-only` (egress only, no ingress)
- **Status**: Active and enforced

#### ⚠️ AdGuard Configuration Update
- **Port change**: Container/service ports changed from 3000 to 80
- **Health probes**: Updated to check port 80
- **Note**: AdGuard serves on port 3000 during initial setup, switches to 80 after configuration
- **Action required**: Complete AdGuard initial setup via web UI

### Testing & Verification

✅ SSH firewall rule: 6 IPs only
✅ PVCs created and bound
✅ Pod Security labels applied to all namespaces
✅ Network policies active
✅ Twingate connectors: ONLINE (2/2)
✅ AdGuard pod: Running (awaiting initial setup)

### Known Issues

1. **AdGuard Initial Setup Required**
   - Pod running but needs web UI configuration
   - Access via: http://172.27.32.11:3000 (internal LB via Twingate)
   - After setup, will automatically switch to port 80

### Impact Assessment

**Security**:
- ✅ High: SSH access restricted to authorized IPs only
- ✅ Medium: Network policies control pod-level traffic
- ✅ Medium: Pod Security Standards enforced

**Operational**:
- ✅ AdGuard config now persists (no data loss on restart)
- ⚠️ Single replica only (RWO constraint)
- ⚠️ AdGuard needs initial setup to be fully operational

**Cost**:
- Additional: ~$18-19/month (PVCs + internal LB)

### Documentation Updated
- `/home/slash-31/argolis_v2/CLAUDE.md` - Added AdGuard LoadBalancer IP preservation requirements
- `/home/slash-31/ai_projects/lab_task/IMPLEMENTATION_SUMMARY.md` - Complete implementation details

### Critical Notes

**⚠️ LoadBalancer IP Preservation**:
Current AdGuard LoadBalancer IPs MUST be preserved in any future changes:
- DNS TCP: `35.202.44.179`
- DNS UDP: `34.172.169.29`
- DoH: `136.113.247.244`
- Web (Internal): `172.27.32.11`

These IPs are used by external DNS clients. Changing them will break DNS resolution.

---

## 2025-10-29 - Comprehensive Logging & Security Hardening

### Summary
Enabled comprehensive logging across all infrastructure components and hardened AdGuard access controls.

### Changes Made

#### ✅ Logging Enabled

1. **GKE-Managed Firewall Rules**
   - Enabled logging on 3 load balancer firewall rules:
     - `k8s-fw-ab483f3ccdabf492a8511ec512335a3e` (DNS TCP)
     - `k8s-fw-ace0f0c9ed0ea4b0997936aad65c3fc1` (DoH HTTPS)
     - `k8s-fw-ad42963d39b514310babdbc2fea64f14` (DNS UDP)
     - `k8s-fw-aa509261d96be4b5d88d4f253d5902a0` (Web UI)
   - Command used:
     ```bash
     gcloud compute firewall-rules update RULE_NAME \
       --project=florida-prod-gke-101025 \
       --enable-logging --logging-metadata=include-all
     ```

2. **VPC Flow Logs** (Already enabled)
   - Confirmed enabled on `us-central1-prod-gke-subnet`
   - Settings: 5-second intervals, 50% sampling, full metadata

3. **Cloud NAT Logging** (Updated filter)
   - Changed from `ERRORS_ONLY` to `ALL`
   - File: `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/networking/main.tf:207`

4. **Load Balancer Logging** (Already enabled)
   - All 4 AdGuard services have 100% sample rate

#### ✅ AdGuard Web UI - Internal LoadBalancer

**Changed:** AdGuard web service from `NodePort` to `LoadBalancer (Internal)`

**File:** `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/helm/main.tf:350-391`

**Configuration:**
- **Type:** LoadBalancer (Internal)
- **Internal IP:** `172.27.32.11`
- **Port:** 3000/TCP
- **Allowed Sources:**
  - `172.27.40.0/21` (Pod CIDR - includes Twingate)
  - `172.27.32.0/24` (Node CIDR)
  - `172.27.50.0/24` (Service CIDR)
- **Logging:** Enabled (100% sample rate)
- **Session Affinity:** ClientIP

**Rationale:**
- Secure internal-only access
- Accessible from Twingate connectors
- Removes need for public exposure of web UI
- Consistent with zero-trust architecture

#### ✅ New Firewall Rule - AdGuard Web External

**Created:** `us-central1-prod-adguard-web-external`

**File:** `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/networking/main.tf:156-176`

**Configuration:**
- **Protocol:** TCP
- **Port:** 3000
- **Allowed Source:** `45.21.151.99/32` (Munich Network)
- **Logging:** Enabled (INCLUDE_ALL_METADATA)

**Purpose:** Allow direct access to AdGuard web UI from Munich network

#### ✅ Updated AdGuard Allowed IPs

**Changed:** Reduced AdGuard access from all private RFC1918 ranges + 1 IP to 6 specific IPs

**Files Updated:**
- `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/workloads/terraform.tfvars:27-35`
- `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/root/variables.tf:74-87`

**Old Configuration:**
```hcl
adguard_allowed_cidrs = [
  "45.21.151.99/32",
  "10.0.0.0/8",
  "172.16.0.0/12",
  "192.168.0.0/16"
]
```

**New Configuration:**
```hcl
adguard_allowed_cidrs = [
  "45.21.151.99/32",   # Munich Network
  "68.70.225.213/32",  # Network 2
  "68.103.59.243/32",  # Network 3
  "47.147.24.137/32",  # Network 4
  "208.115.150.123/32", # Network 5
  "20.118.171.229/32"  # Network 6
]
```

**Rationale:** More restrictive security posture - only allow known client IPs

#### ✅ Fixed DNS Firewall Rule

**Issue:** `us-central1-prod-adguard-dns-external` allowed `0.0.0.0/0` (entire internet)

**Fix:** Updated to only allow 6 authorized IPs
```bash
gcloud compute firewall-rules update us-central1-prod-adguard-dns-external \
  --project=florida-prod-gke-101025 \
  --source-ranges=45.21.151.99/32,68.70.225.213/32,68.103.59.243/32,47.147.24.137/32,208.115.150.123/32,20.118.171.229/32
```

#### ✅ Updated Terraform Outputs

**File:** `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/helm/outputs.tf`

**Removed:**
- `adguard_dns_tls_ip`
- `adguard_dnscrypt_tcp_ip`
- `adguard_https_tcp_ip`

**Added:**
- `adguard_doh_lb_ip` (DNS-over-HTTPS LB IP)
- `adguard_web_lb_ip` (Internal web UI LB IP)

**Reason:** Removed outputs for services that no longer exist after simplification

#### ✅ Imported Existing Resources

**Imported into Terraform state:**
1. `module.networking.google_compute_firewall.adguard_doh_external`
2. `module.networking.google_compute_router.nat_router`
3. `module.networking.google_compute_router_nat.nat_gateway`
4. `module.helm.kubernetes_service.adguard_doh[0]`

**Reason:** These resources were created manually via gcloud in previous session; now managed by Terraform

### Testing & Verification

✅ All firewall rules have logging enabled (9 rules)
✅ VPC Flow Logs operational
✅ Cloud NAT logging enabled (ALL filter)
✅ Load balancer logging enabled on all 4 services
✅ AdGuard web UI accessible via internal LB (`172.27.32.11:3000`)
✅ Internal connectivity test successful from pods
✅ All 6 authorized IPs can access DNS services
✅ Twingate connectors remain ONLINE
✅ AdGuard pods running (2/2)

### Commands Used

```bash
# Enable logging on GKE firewall rules
gcloud compute firewall-rules update k8s-fw-ab483f3ccdabf492a8511ec512335a3e \
  --project=florida-prod-gke-101025 --enable-logging --logging-metadata=include-all

# Update DNS firewall allowed IPs
gcloud compute firewall-rules update us-central1-prod-adguard-dns-external \
  --project=florida-prod-gke-101025 \
  --source-ranges=45.21.151.99/32,68.70.225.213/32,68.103.59.243/32,47.147.24.137/32,208.115.150.123/32,20.118.171.229/32

# Apply Terraform changes
cd /home/slash-31/argolis_v2/prod-gke-gemini/deployed/root
terraform apply

cd /home/slash-31/argolis_v2/prod-gke-gemini/deployed/workloads
terraform apply
```

### Impact Assessment

**Security:**
- ✅ Improved: Restricted AdGuard access to only 6 known IPs
- ✅ Improved: Web UI now internal-only (access via Twingate)
- ✅ Improved: All infrastructure logging enabled for audit trail

**Operational:**
- ✅ No downtime during changes
- ✅ AdGuard services remained available
- ✅ Twingate connectors stayed online
- ⚠️ DNS firewall rule briefly allowed 0.0.0.0/0 (fixed within 5 minutes)

**Cost:**
- Additional internal load balancer: ~$0.025/hour (~$18/month)
- Increased logging volume: estimate +$10-20/month

### Related Documentation
- Main status doc: `/home/slash-31/ai_projects/lab_task/GKE_DEPLOYMENT_STATUS.md`
- Quick reference: `/home/slash-31/ai_projects/lab_task/QUICK_REFERENCE.md`

---

## 2025-10-27 - Initial GKE Cluster & Workload Deployment

### Summary
Initial deployment of GKE cluster with AdGuard Home DNS server and Twingate zero-trust connector.

### Infrastructure Created

#### ✅ GKE Cluster
- **Name:** `us-central1-prod-gke-cluster`
- **Type:** Regional (3 zones)
- **Node Pool:** `us-central1-prod-default-pool`
  - Machine type: `e2-standard-4`
  - Nodes: 2 per zone (6 total)
- **Network:** Private cluster with authorized networks
- **Master Endpoint:** Private with public access restricted to authorized IPs

#### ✅ VPC Networking
- **VPC:** `us-central1-prod-vpc`
- **Subnet:** `us-central1-prod-gke-subnet`
  - Primary CIDR: `172.27.32.0/24`
  - Secondary (pods): `172.27.40.0/21`
  - Secondary (services): `172.27.50.0/24`
- **VPC Flow Logs:** Enabled (5-sec intervals, 50% sampling)

#### ✅ Firewall Rules
Created 5 custom firewall rules:
1. `us-central1-prod-gke-internal` - Internal cluster communication
2. `us-central1-prod-adguard-dns-external` - DNS queries (53/TCP+UDP)
3. `us-central1-prod-adguard-doh-external` - DNS-over-HTTPS (443/TCP+UDP)
4. `us-central1-prod-ssh-access` - SSH access (22/TCP)
5. Logging enabled on all custom rules

#### ✅ Cloud NAT Gateway
- **Router:** `us-central1-prod-nat-router`
- **Gateway:** `us-central1-prod-nat-gateway`
- **Purpose:** Internet egress for private nodes and pods
- **Configuration:** AUTO_ONLY IP allocation, ALL_SUBNETWORKS
- **Logging:** Enabled (ERRORS_ONLY initially)

### Workloads Deployed

#### ✅ AdGuard Home (Namespace: adguard)
- **Replicas:** 2
- **Image:** `adguard/adguardhome:latest`
- **Services:**
  - `adguard-dns-tcp` (LoadBalancer - External)
  - `adguard-dns-udp` (LoadBalancer - External)
  - `adguard-doh` (LoadBalancer - External) - Added on 2025-10-29
  - `adguard-web` (NodePort initially, changed to Internal LB on 2025-10-29)
- **Exposed Ports:**
  - 53/TCP+UDP (DNS)
  - 443/TCP+UDP (DNS-over-HTTPS)
  - 3000/TCP (Web UI)

**Initial Services (Later Simplified):**
- Initially deployed 10 load balancers (DoT, DoQ, DNSCrypt)
- Simplified to 3 external + 1 internal on 2025-10-29

#### ✅ Twingate Connector (Namespace: twingate)
- **Replicas:** 2
- **Image:** `twingate/connector:latest`
- **Network:** `securitydude.twingate.com`
- **Secret Management:** Google Secret Manager integration
- **Secrets:**
  - `twingate-access-token`
  - `twingate-refresh-token`
  - `twingate-network-name`

### Issues Resolved

#### Issue 1: Twingate Network Name Format
**Problem:** Connectors tried to reach `https://securitydude.twingate.com.twingate.com` (domain doubled)

**Root Cause:** Secret Manager stored full domain `securitydude.twingate.com`, but connector appends `.twingate.com`

**Fix:**
```bash
echo -n "securitydude" | gcloud secrets versions add twingate-network-name \
  --project=florida-prod-gke-101025 --data-file=-
kubectl rollout restart deployment/twingate-connector -n twingate
```

**Result:** Connectors authenticated successfully

#### Issue 2: No Internet Connectivity from Pods
**Problem:** Twingate connectors showing "EOF reached" errors, couldn't authenticate

**Root Cause:** Private GKE cluster had no Cloud NAT gateway

**Fix:**
```bash
gcloud compute routers create us-central1-prod-nat-router \
  --project=florida-prod-gke-101025 --region=us-central1 \
  --network=us-central1-prod-vpc

gcloud compute routers nats create us-central1-prod-nat-gateway \
  --router=us-central1-prod-nat-router \
  --project=florida-prod-gke-101025 --region=us-central1 \
  --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges \
  --enable-logging --log-filter=ERRORS_ONLY
```

**Result:** Connectors immediately went ONLINE

### Terraform Structure Created

```
/home/slash-31/argolis_v2/prod-gke-gemini/deployed/
├── root/                    # Infrastructure layer
│   ├── main.tf
│   ├── variables.tf
│   ├── terraform.tfvars
│   └── outputs.tf
├── workloads/               # Application layer
│   ├── main.tf
│   ├── variables.tf
│   ├── terraform.tfvars
│   └── outputs.tf
└── modules/
    ├── networking/          # VPC, firewall, NAT
    ├── gke/                 # GKE cluster
    ├── helm/                # K8s workloads (AdGuard, etc.)
    ├── twingate/            # Twingate connector
    └── ncc/                 # Network Connectivity Center
```

### Commands Used

**Initial Deployment:**
```bash
cd /home/slash-31/argolis_v2/prod-gke-gemini/deployed/root
export GOOGLE_APPLICATION_CREDENTIALS=/home/slash-31/junk/terraform-admin-jwt.json
terraform init
terraform plan
terraform apply

cd /home/slash-31/argolis_v2/prod-gke-gemini/deployed/workloads
terraform init
terraform plan
terraform apply
```

**Get Cluster Credentials:**
```bash
gcloud container clusters get-credentials us-central1-prod-gke-cluster \
  --region us-central1 --project florida-prod-gke-101025
```

### Testing & Verification

✅ GKE cluster operational (6 nodes)
✅ AdGuard pods running (2/2)
✅ Twingate connectors ONLINE (2/2)
✅ DNS resolution working (`dig @35.202.44.179 google.com`)
✅ Internal communication operational
✅ Internet egress via NAT gateway

### Impact Assessment

**Security:**
- Private GKE cluster (no public node IPs)
- Authorized networks for kubectl access
- Zero-trust access via Twingate
- Firewall rules restrict access to known IPs

**Operational:**
- Fully functional DNS filtering service
- Secure remote access via Twingate
- High availability (2 replicas per service)

**Cost:**
- GKE cluster management: ~$73/month
- 6 x e2-standard-4 nodes: ~$340/month
- 3 external IPs: ~$90/month
- Load balancers: ~$60/month
- **Total:** ~$560/month

---

## Change Template

```markdown
## YYYY-MM-DD - Change Title

### Summary
Brief description of what was changed and why.

### Changes Made

#### ✅ Component/Feature Name

**Changed:** What was modified
**File:** Path to file(s) modified
**Configuration:** Key settings

**Old:**
```
old configuration
```

**New:**
```
new configuration
```

**Rationale:** Why this change was made

### Commands Used
```bash
# Commands executed
```

### Testing & Verification
✅ Test 1
✅ Test 2
❌ Test 3 (failed - reason)

### Impact Assessment
**Security:** Impact on security posture
**Operational:** Impact on operations
**Cost:** Impact on monthly costs

### Related Documentation
- Links to related docs or issues
```

---

**Next Review Date:** 2025-11-05
