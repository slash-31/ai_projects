# Lab Task Documentation

**GKE Cluster Deployment Tracking & Reference**

---

## 📁 Documentation Structure

This directory contains comprehensive documentation for the GKE cluster deployment in the `florida-prod-gke-101025` project.

### Files Overview

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `GKE_DEPLOYMENT_STATUS.md` | Complete status of infrastructure and workloads | Weekly |
| `QUICK_REFERENCE.md` | One-liner commands for daily operations | As needed |
| `CHANGE_LOG.md` | Chronological record of all changes | After each change |
| `CLAUDE.md` | Instructions for Claude Code assistant | As needed |

---

## 🚀 Getting Started

### First Time Setup

1. **Authenticate with GCP:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/home/slash-31/junk/terraform-admin-jwt.json
   gcloud auth application-default login
   ```

2. **Get Cluster Access:**
   ```bash
   gcloud container clusters get-credentials us-central1-prod-gke-cluster \
     --region us-central1 --project florida-prod-gke-101025
   ```

3. **Verify Access:**
   ```bash
   kubectl get nodes
   kubectl get pods -A
   ```

### Daily Usage

**Quick status check:**
```bash
kubectl get pods -A -o wide
kubectl get svc -A
```

**View logs:**
```bash
kubectl logs -n adguard -l app=adguard-home --tail=50
kubectl logs -n twingate -l app=twingate-connector --tail=50
```

**For more commands, see:** `QUICK_REFERENCE.md`

---

## 📊 Current Deployment Summary

### Infrastructure
- **Cluster:** us-central1-prod-gke-cluster (6 nodes, 3 zones)
- **Network:** us-central1-prod-vpc (private cluster)
- **NAT Gateway:** us-central1-prod-nat-gateway (internet egress)
- **Firewall Rules:** 9 rules with logging enabled

### Workloads
- **AdGuard Home:** 2 replicas (DNS filtering + ad blocking)
- **Twingate:** 2 replicas (zero-trust network access)

### External IPs
- DNS (TCP): `35.202.44.179:53`
- DNS (UDP): `34.172.169.29:53`
- DoH: `136.113.247.244:443`
- Web UI (Internal): `172.27.32.11:3000`

### Internal Subnets
**Munich Site:**
- 10.0.128.0/24 (Core), 10.0.129.0/24 (IoT), 10.0.130.0/24 (Mgmt), 10.0.132.0/24 (Docker)

**BinaryFU Site:**
- 10.101.53.0/24 (JK - 4x /27 subnets), 10.101.12.0/24 (OOB-MGMT), 10.101.20.0/24 (Core-Servers)

**Other Sites:**
- 192.168.1.0/24 (WillowCreek), 192.168.12.0/24 (Davis)

**For full details, see:** `GKE_DEPLOYMENT_STATUS.md` or `QUICK_REFERENCE.md`

---

## 🔄 How to Update Documentation

### After Making Infrastructure Changes

1. **Update the status document:**
   - Edit `GKE_DEPLOYMENT_STATUS.md`
   - Update the "What's Currently Working" section
   - Add any new issues to "What Needs Attention"
   - Update the "Last Updated" date

2. **Record the change:**
   - Add entry to `CHANGE_LOG.md` (use the template at the bottom)
   - Include: what changed, why, commands used, impact assessment

3. **Update quick reference (if needed):**
   - Add new commands to `QUICK_REFERENCE.md`
   - Update IPs/endpoints if they changed

### When Something Breaks

1. **Document in status doc:**
   - Move item from "Working" to "Known Issues"
   - Add troubleshooting steps tried

2. **Add to change log:**
   - Create entry describing the issue
   - Document the resolution (or current status if unresolved)

### Weekly Review Checklist

Run these commands to verify status:

```bash
# Cluster health
kubectl get nodes
kubectl get pods -A

# Workload status
kubectl get deploy,pods,svc -n adguard
kubectl get deploy,pods -n twingate

# Twingate connection
kubectl logs -n twingate -l app=twingate-connector --tail=10 | grep "State:"

# Firewall logging
gcloud compute firewall-rules list --project=florida-prod-gke-101025 \
  --format="table(name,logConfig.enable)"

# NAT gateway
gcloud compute routers nats list --router=us-central1-prod-nat-router \
  --region=us-central1 --project=florida-prod-gke-101025
```

Update `GKE_DEPLOYMENT_STATUS.md` with current status and set "Next Review" date to +7 days.

---

## 🎯 Quick Navigation

### By Task

**I want to...**
- **Check if everything is working:** See `GKE_DEPLOYMENT_STATUS.md` → "What's Currently Working"
- **Run a quick command:** See `QUICK_REFERENCE.md` → Find your task
- **Troubleshoot an issue:** See `GKE_DEPLOYMENT_STATUS.md` → "Troubleshooting Guide"
- **See what changed recently:** See `CHANGE_LOG.md` → Most recent entries
- **Find a specific IP/endpoint:** See `QUICK_REFERENCE.md` → "Important IPs & Endpoints"
- **Update authorized IPs:** See `QUICK_REFERENCE.md` → "Update Firewall Allowed IPs"

### By Component

- **GKE Cluster:** `GKE_DEPLOYMENT_STATUS.md` → "GKE Cluster" section
- **AdGuard DNS:** `GKE_DEPLOYMENT_STATUS.md` → "AdGuard Home DNS Server" section
- **Twingate:** `GKE_DEPLOYMENT_STATUS.md` → "Twingate Zero-Trust Connector" section
- **Networking:** `GKE_DEPLOYMENT_STATUS.md` → "VPC Networking" + "Firewall Rules"
- **Logging:** `GKE_DEPLOYMENT_STATUS.md` → "Logging & Monitoring" section

---

## 🔗 Related Resources

### Infrastructure Code
- **Root module:** `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/root/`
- **Workloads module:** `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/workloads/`
- **Terraform modules:** `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/`
- **Project instructions:** `/home/slash-31/argolis_v2/CLAUDE.md`

### External Documentation
- [GKE Best Practices](https://cloud.google.com/kubernetes-engine/docs/best-practices)
- [AdGuard Home Wiki](https://github.com/AdguardTeam/AdGuardHome/wiki)
- [Twingate Documentation](https://docs.twingate.com/docs)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

### GCP Console Links
- [GKE Clusters](https://console.cloud.google.com/kubernetes/list?project=florida-prod-gke-101025)
- [Firewall Rules](https://console.cloud.google.com/net-security/firewall-manager/firewall-policies/list?project=florida-prod-gke-101025)
- [Secret Manager](https://console.cloud.google.com/security/secret-manager?project=florida-prod-gke-101025)
- [Logs Explorer](https://console.cloud.google.com/logs/query?project=florida-prod-gke-101025)

---

## 🆘 Emergency Contacts & Procedures

### If Cluster is Unreachable

1. Check cluster status:
   ```bash
   gcloud container clusters list --project=florida-prod-gke-101025
   ```

2. Re-authenticate:
   ```bash
   gcloud container clusters get-credentials us-central1-prod-gke-cluster \
     --region us-central1 --project=florida-prod-gke-101025
   ```

3. Check master endpoint in firewall (authorized networks)

### If DNS Not Working

1. Check AdGuard pods:
   ```bash
   kubectl get pods -n adguard
   kubectl logs -n adguard -l app=adguard-home --tail=100
   ```

2. Verify load balancers have external IPs:
   ```bash
   kubectl get svc -n adguard
   ```

3. Test DNS resolution:
   ```bash
   dig @35.202.44.179 google.com
   ```

### If Twingate Not Connecting

1. Check connector status:
   ```bash
   kubectl logs -n twingate -l app=twingate-connector --tail=50 | grep -E "(State:|error)"
   ```

2. Verify secrets:
   ```bash
   gcloud secrets versions access latest --secret=twingate-network-name \
     --project=florida-prod-gke-101025 | cat -A
   ```

3. Restart connectors:
   ```bash
   kubectl rollout restart deployment/twingate-connector -n twingate
   ```

**For full troubleshooting guide, see:** `GKE_DEPLOYMENT_STATUS.md` → "Troubleshooting Guide"

---

## 📝 Maintenance Schedule

### Daily
- Check pod status (`kubectl get pods -A`)
- Review recent logs for errors
- Verify Twingate connection state

### Weekly
- Run full status check (see "Weekly Review Checklist" above)
- Update `GKE_DEPLOYMENT_STATUS.md` with current state
- Review and clear old logs if needed

### Monthly
- Review firewall rules and access controls
- Check for GKE version updates
- Review cost optimization opportunities
- Backup Terraform state
- Rotate Twingate tokens (if needed)

### Quarterly
- Full security audit
- Review and update documentation
- Disaster recovery test
- Review future enhancements list

---

## 🎓 Learning Resources

### New to GKE?
1. Start with `GKE_DEPLOYMENT_STATUS.md` → "What's Currently Working"
2. Review `QUICK_REFERENCE.md` → Try running status checks
3. Read `CHANGE_LOG.md` → See what was done and why
4. Explore the Terraform code in `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/`

### Want to Make Changes?
1. Read `GKE_DEPLOYMENT_STATUS.md` → "Key Configuration Files"
2. Test changes in `terraform plan` first
3. Document in `CHANGE_LOG.md` before applying
4. Update `GKE_DEPLOYMENT_STATUS.md` after verification

### Kubernetes Commands
- Official cheat sheet: https://kubernetes.io/docs/reference/kubectl/cheatsheet/
- Quick reference: `QUICK_REFERENCE.md` → "Common Operations"

---

**Questions or issues?** Check the troubleshooting guide in `GKE_DEPLOYMENT_STATUS.md` or review recent changes in `CHANGE_LOG.md`.

**Last Documentation Update:** 2025-10-29
