# GKE Cluster Quick Reference

**Quick access commands for daily operations.**

---

## 🚀 Quick Start

### Get Cluster Access
```bash
gcloud container clusters get-credentials us-central1-prod-gke-cluster \
  --region us-central1 --project florida-prod-gke-101025
```

### Set Environment Variables
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/home/slash-31/junk/terraform-admin-jwt.json
export PROJECT_ID=florida-prod-gke-101025
export CLUSTER_NAME=us-central1-prod-gke-cluster
export REGION=us-central1
```

---

## 📊 Status Checks (One-Liners)

### Overall Health
```bash
# All workload pods
kubectl get pods -A -o wide

# All services with IPs
kubectl get svc -A

# Cluster nodes
kubectl get nodes -o wide

# Recent events
kubectl get events -A --sort-by='.lastTimestamp' | tail -20
```

### AdGuard Status
```bash
# Quick status
kubectl get deploy,pods,svc -n adguard

# External IPs
kubectl get svc -n adguard -o custom-columns=NAME:.metadata.name,EXTERNAL-IP:.status.loadBalancer.ingress[0].ip,PORT:.spec.ports[0].port

# Recent logs
kubectl logs -n adguard -l app=adguard-home --tail=50

# Test DNS resolution
dig @35.202.44.179 google.com
```

### Twingate Status
```bash
# Quick status
kubectl get deploy,pods -n twingate

# Check connection state (look for "State: Connected")
kubectl logs -n twingate -l app=twingate-connector --tail=50 | grep -E "(State:|Connected|Offline|Authentication)"

# Connector IPs
kubectl get pods -n twingate -o wide
```

---

## 🔥 Common Operations

### Restart Deployments
```bash
# Restart AdGuard
kubectl rollout restart deployment/adguard-home -n adguard

# Restart Twingate
kubectl rollout restart deployment/twingate-connector -n twingate

# Watch rollout status
kubectl rollout status deployment/twingate-connector -n twingate
```

### View Logs
```bash
# Follow AdGuard logs
kubectl logs -n adguard -l app=adguard-home -f

# Follow Twingate logs
kubectl logs -n twingate -l app=twingate-connector -f

# Logs from specific pod
kubectl logs -n adguard adguard-home-XXXXXX --tail=100
```

### Update Secrets
```bash
# Update Twingate token (NO TRAILING NEWLINE!)
echo -n "new_token_value" | gcloud secrets versions add twingate-access-token \
  --project=florida-prod-gke-101025 --data-file=-

# Verify secret
gcloud secrets versions access latest --secret=twingate-access-token \
  --project=florida-prod-gke-101025 | cat -A

# Restart to pick up new secret
kubectl rollout restart deployment/twingate-connector -n twingate
```

---

## 🌐 Network & Firewall

### View Firewall Rules
```bash
# List all firewall rules with logging status
gcloud compute firewall-rules list --project=florida-prod-gke-101025 \
  --format="table(name,logConfig.enable,sourceRanges.list(),allowed[].map().firewall_rule().list())"

# Describe specific rule
gcloud compute firewall-rules describe us-central1-prod-adguard-dns-external \
  --project=florida-prod-gke-101025
```

### Update Firewall Allowed IPs
```bash
# Update DNS access
gcloud compute firewall-rules update us-central1-prod-adguard-dns-external \
  --project=florida-prod-gke-101025 \
  --source-ranges=IP1/32,IP2/32,IP3/32
```

### Check NAT Gateway
```bash
# NAT status
gcloud compute routers nats describe us-central1-prod-nat-gateway \
  --router=us-central1-prod-nat-router \
  --region=us-central1 \
  --project=florida-prod-gke-101025

# NAT logs
gcloud logging read "resource.type=nat_gateway" \
  --project=florida-prod-gke-101025 --limit=20
```

---

## 🏗️ Terraform Operations

### Root Module (Infrastructure)
```bash
cd /home/slash-31/argolis_v2/prod-gke-gemini/deployed/root
export GOOGLE_APPLICATION_CREDENTIALS=/home/slash-31/junk/terraform-admin-jwt.json
terraform plan
terraform apply
```

### Workloads Module (Applications)
```bash
cd /home/slash-31/argolis_v2/prod-gke-gemini/deployed/workloads
export GOOGLE_APPLICATION_CREDENTIALS=/home/slash-31/junk/terraform-admin-jwt.json
terraform plan
terraform apply
```

### Import Existing Resources
```bash
# Example: Import firewall rule
terraform import module.networking.google_compute_firewall.RESOURCE_NAME \
  projects/PROJECT_ID/global/firewalls/FIREWALL_NAME

# Example: Import NAT gateway
terraform import module.networking.google_compute_router_nat.nat_gateway \
  projects/PROJECT_ID/regions/REGION/routers/ROUTER_NAME/NAT_NAME
```

---

## 📝 View Logs (Cloud Console)

### Firewall Logs
```bash
gcloud logging read "resource.type=gce_firewall_rule AND \
  resource.labels.firewall_rule_id=us-central1-prod-adguard-dns-external" \
  --project=florida-prod-gke-101025 --limit=50
```

### Load Balancer Logs
```bash
gcloud logging read "resource.type=gce_network_tcp_lb_rule" \
  --project=florida-prod-gke-101025 --limit=50
```

### VPC Flow Logs
```bash
gcloud logging read "resource.type=gce_subnetwork AND \
  resource.labels.subnetwork_name=us-central1-prod-gke-subnet" \
  --project=florida-prod-gke-101025 --limit=20
```

---

## 🆘 Emergency Commands

### Pod Not Starting
```bash
# Describe pod to see events
kubectl describe pod POD_NAME -n NAMESPACE

# Check pod logs even if crashed
kubectl logs POD_NAME -n NAMESPACE --previous

# Delete and recreate pod
kubectl delete pod POD_NAME -n NAMESPACE
```

### Service Has No External IP
```bash
# Check service status
kubectl get svc SERVICE_NAME -n NAMESPACE -o yaml

# Check GKE-managed firewall rules
gcloud compute firewall-rules list --project=florida-prod-gke-101025 \
  --filter="name~k8s-fw"

# Describe service events
kubectl describe svc SERVICE_NAME -n NAMESPACE
```

### Cluster Unreachable
```bash
# Verify cluster exists
gcloud container clusters list --project=florida-prod-gke-101025

# Check cluster status
gcloud container clusters describe us-central1-prod-gke-cluster \
  --region=us-central1 --project=florida-prod-gke-101025

# Re-authenticate
gcloud container clusters get-credentials us-central1-prod-gke-cluster \
  --region us-central1 --project=florida-prod-gke-101025
```

---

## 📍 Important IPs & Endpoints

### External IPs
- **AdGuard DNS (TCP):** `35.202.44.179:53`
- **AdGuard DNS (UDP):** `34.172.169.29:53`
- **AdGuard DoH:** `136.113.247.244:443`
- **AdGuard Web (Internal):** `172.27.32.11:3000`

### Network CIDRs
- **Node CIDR:** `172.27.32.0/24`
- **Pod CIDR:** `172.27.40.0/21`
- **Service CIDR:** `172.27.50.0/24`

### Authorized Client IPs
1. `45.21.151.99/32` (Munich Network)
2. `68.70.226.96/32` (BinaryFU-DC1-Gate1)
3. `68.228.239.142/32` (BinaryFU-Mar1-Gate1)
4. `73.90.26.100/32` (WillowCreek-MX68CW)
5. `93.127.200.12/32` (Aarrhus-Hostinger)
6. `172.234.224.17` (interlaken-linux01)

---

## 🔗 Quick Links

- **GCP Console:** https://console.cloud.google.com/kubernetes/list?project=florida-prod-gke-101025
- **GKE Cluster:** https://console.cloud.google.com/kubernetes/clusters/details/us-central1/us-central1-prod-gke-cluster?project=florida-prod-gke-101025
- **Firewall Rules:** https://console.cloud.google.com/net-security/firewall-manager/firewall-policies/list?project=florida-prod-gke-101025
- **Secret Manager:** https://console.cloud.google.com/security/secret-manager?project=florida-prod-gke-101025
- **Logs Explorer:** https://console.cloud.google.com/logs/query?project=florida-prod-gke-101025

---

**Pro Tip:** Add these aliases to your `~/.bashrc`:
```bash
alias k="kubectl"
alias kgp="kubectl get pods -A -o wide"
alias kgs="kubectl get svc -A"
alias kga="kubectl get all -A"
alias klf="kubectl logs -f"
alias tf="terraform"
alias gke-auth="gcloud container clusters get-credentials us-central1-prod-gke-cluster --region us-central1 --project florida-prod-gke-101025"
alias tf-env="export GOOGLE_APPLICATION_CREDENTIALS=/home/slash-31/junk/terraform-admin-jwt.json"
```
