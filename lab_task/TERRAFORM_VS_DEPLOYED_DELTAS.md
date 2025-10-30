# Terraform Configuration vs Deployed State Analysis
**Date**: 2025-10-29
**Cluster**: us-central1-prod-gke-cluster
**Analysis Method**: Code review + kubectl inspection + Terraform state comparison

---

## Executive Summary

**Status**: ⚠️ CRITICAL DRIFT DETECTED

The deployed infrastructure is **more advanced** than what the Terraform configuration can currently manage due to **corrupted/truncated configuration files**. The cluster is operational with security hardening applied, but Terraform cannot manage it in its current state.

### Key Findings:
1. ✅ **Deployed cluster has improvements** not in original code (security contexts, PVCs, network policies)
2. 🚨 **Terraform code has syntax errors** preventing management
3. 🚨 **Configuration files truncated** during recent editing session
4. ⚠️ **Configuration drift**: `enable_network_policies = false` but 2 policies active

---

## Critical Issues Preventing Terraform Operations

### Issue 1: Syntax Error in workloads/main.tf
**File**: `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/workloads/main.tf`
**Line**: 105 (module "twingate" block)
**Error**: Unclosed configuration block

```
Error: Unclosed configuration block
  on main.tf line 105, in module "twingate":
 105: module "twingate" {
There is no closing brace for this block before the end of the file.
```

**Line 130 Truncation**:
```hcl
twingate_cpu_request    = var.twingate_cpu_reque  # ← Incomplete!
```

**Impact**:
- `terraform plan/apply` fails immediately
- Cannot manage infrastructure via Terraform
- State file may become inconsistent

**Root Cause**: File appears truncated during recent editing session (should end around line 135-140 with proper closing braces)

---

### Issue 2: helm/main.tf File Truncation
**File**: `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/helm/main.tf`
**Expected**: ~939 lines
**Actual**: 349 lines (63% missing!)

**Missing Resources**:
Based on outputs.tf, these resources should exist but are missing from main.tf:
- `kubernetes_service.adguard_doh` (DoH LoadBalancer)
- `kubernetes_service.adguard_web` (Web UI LoadBalancer)
- `kubernetes_ingress_v1.adguard_https` (HTTPS ingress)

**However, kubectl shows these ARE deployed**:
```bash
$ kubectl get svc -n adguard
NAME              TYPE           EXTERNAL-IP
adguard-doh       LoadBalancer   136.113.247.244  ✅ EXISTS
adguard-web       LoadBalancer   172.27.32.11     ✅ EXISTS
```

**Conclusion**: Resources were deployed in previous successful apply, but code defining them was lost during truncation.

---

## Configuration vs Deployed State Comparison

### AdGuard Deployment

| Aspect | Terraform Config (tfvars) | Deployed State | Match? |
|--------|---------------------------|----------------|--------|
| **Replicas** | `adguard_replicas = 1` | 1 replica | ✅ YES |
| **Image** | `adguard/adguardhome:latest` | `adguard/adguardhome:latest` | ✅ YES |
| **Persistent Storage** | ❓ (code truncated) | 2 PVCs (5Gi + 10Gi) | ❓ UNKNOWN |
| **Security Context** | ❓ (code truncated) | Pod: runAsNonRoot=false, fsGroup=1000, seccomp | ✅ DEPLOYED |
| **Container Ports** | ❓ (code truncated) | 53, 53, 80, 443, 443 | ✅ DEPLOYED |
| **Pod Security** | ❓ (code truncated) | Namespace has baseline PSS | ✅ DEPLOYED |

### Persistent Volume Claims

| Resource | Size | Access Mode | Storage Class | Status |
|----------|------|-------------|---------------|--------|
| adguard-config-pvc | 5Gi | ReadWriteOnce | standard-rwo | ✅ Bound |
| adguard-data-pvc | 10Gi | ReadWriteOnce | standard-rwo | ✅ Bound |

**Status**: PVCs exist and are bound, but we cannot confirm if Terraform code defines them due to truncation.

### AdGuard Services

| Service | Type | External IP | Port | Deployed |
|---------|------|-------------|------|----------|
| adguard-dns-tcp | LoadBalancer | **35.202.44.179** | 53/TCP | ✅ |
| adguard-dns-udp | LoadBalancer | **34.172.169.29** | 53/UDP | ✅ |
| adguard-doh | LoadBalancer | **136.113.247.244** | 443/TCP+UDP | ✅ |
| adguard-web | LoadBalancer (Internal) | **172.27.32.11** | 80/TCP | ✅ |

**Status**: All 4 services deployed with stable IPs (MUST PRESERVE THESE IPs)

### Network Policies

| Policy | Namespace | Status | Config Value |
|--------|-----------|--------|--------------|
| adguard-access-policy | adguard | ✅ ACTIVE | `enable_network_policies = false` ⚠️ |
| twingate-egress-only | twingate | ✅ ACTIVE | `enable_network_policies = false` ⚠️ |

**⚠️ CONFIGURATION DRIFT DETECTED**:
- **terraform.tfvars**: `enable_network_policies = false` (line 82)
- **Deployed State**: 2 network policies are ACTIVE

**Analysis**:
- Network policies were deployed during security hardening session
- tfvars was reverted/changed to `false` after deployment
- Policies remain active in cluster (Kubernetes doesn't auto-delete)
- If Terraform runs with `false`, it will DELETE the active policies!

**Impact**: Running `terraform apply` with current config will remove network policies and reduce security posture.

### Twingate Deployment

| Aspect | Config | Deployed | Match? |
|--------|--------|----------|--------|
| **Replicas** | 2 | 2 | ✅ YES |
| **Image** | `twingate/connector:latest` | Latest | ✅ YES |
| **Secret Manager** | `use_secret_manager = true` | Used | ✅ YES |
| **Network Policy** | `enable_network_policies = false` | ACTIVE | ❌ DRIFT |
| **Pod Security** | baseline | baseline | ✅ YES |
| **Status** | N/A | 2/2 ONLINE | ✅ HEALTHY |

---

## Detailed Delta Analysis

### 1. Security Hardening Applied to Cluster (Not in Original Code)

**Deployed but may not be in current Terraform code** (due to truncation):

#### Pod Security Standards
```yaml
# Applied to all namespaces:
labels:
  pod-security.kubernetes.io/enforce: baseline
  pod-security.kubernetes.io/audit: baseline
  pod-security.kubernetes.io/warn: baseline
```

**Namespaces affected**: adguard, twingate, cribl, bindplane

#### Security Contexts
```yaml
# AdGuard Pod Security Context
securityContext:
  runAsNonRoot: false  # Required for ports 53/443
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault

# AdGuard Container Security Context
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: false
  capabilities:
    drop: [ALL]
    add: [NET_BIND_SERVICE]
```

**Status**: ✅ Deployed and active, ❓ Unknown if in truncated code

#### Network Policies
1. **adguard-access-policy** (Namespace: adguard)
   - Policy Types: Ingress, Egress
   - Pod Selector: app=adguard-home
   - ✅ ACTIVE

2. **twingate-egress-only** (Namespace: twingate)
   - Policy Types: Egress, Ingress
   - Pod Selector: app=twingate-connector
   - ✅ ACTIVE

**Configuration Conflict**:
```hcl
# terraform.tfvars line 82:
enable_network_policies = false  # ← Would DELETE these if applied!
```

### 2. Persistent Storage Added to AdGuard

**Deployed**:
- adguard-config-pvc: 5Gi (Bound)
- adguard-data-pvc: 10Gi (Bound)
- Volumes mounted to AdGuard pods
- Replicas reduced from 2 → 1 (RWO constraint)

**Terraform Configuration**:
- ❓ UNKNOWN if PVC resources exist in code (truncated section)
- tfvars shows: `adguard_replicas = 1` ✅ Matches

### 3. AdGuard Port Configuration Changes

**Deployed Ports**:
```json
{
  "ports": [53, 53, 80, 443, 443]
}
```

**Services**:
- Port 80: Web UI (changed from 3000 → 80)
- Port 443: DNS-over-HTTPS
- Port 53: DNS (TCP + UDP)

**Health Probes** (from earlier session):
- Liveness: http://localhost:80/
- Readiness: http://localhost:80/
- ✅ Successfully updated

**Terraform Configuration**: ❓ UNKNOWN (code truncated)

### 4. SSH Firewall Restriction

**Deployed** (via gcloud, not Terraform):
```bash
us-central1-prod-ssh-access:
  Source Ranges: [6 specific IPs only]
  # Was: 0.0.0.0/0
```

**Terraform State**: ❓ UNKNOWN - managed outside workloads layer (in root/)

---

## Code Quality Issues (From Agent Review)

### Critical
1. ❌ workloads/main.tf: Unclosed brace, truncated line 130
2. ❌ helm/main.tf: Missing 590 lines (349/939 lines present)
3. ❌ Outputs reference non-existent resources

### High Priority
4. ⚠️ Using `:latest` image tags (non-deterministic)
5. ⚠️ No PodDisruptionBudgets defined
6. ⚠️ Twingate network policy allows all ingress (contradicts comment)

### Medium Priority
7. ⚠️ Duplicate Twingate namespace in helm module
8. ⚠️ Inconsistent date formats in headers
9. ⚠️ Missing resource request/limit validation

---

## Infrastructure Drift Summary

### What Terraform THINKS is Deployed
❓ **UNKNOWN** - Cannot read state due to syntax errors

### What is ACTUALLY Deployed
✅ **OPERATIONAL** with security hardening:
- 1x AdGuard pod with persistent storage
- 2x Twingate connectors
- 4x LoadBalancer services with stable IPs
- 2x Network policies (active)
- Pod Security Standards (baseline) on all namespaces
- Security contexts on all pods

### Configuration Mismatches

| Item | Config Says | Reality Is | Risk Level |
|------|-------------|------------|------------|
| Network Policies | Disabled (`false`) | Active (2 policies) | 🔴 HIGH - Will delete on apply |
| AdGuard Replicas | 1 | 1 | ✅ Match |
| Persistent Storage | ❓ Unknown | Deployed | ⚠️ Could delete if missing |
| Image Tags | `:latest` | `:latest` | ⚠️ Non-deterministic |

---

## Risks of Running Terraform Apply

### With Current Broken Configuration
🔴 **BLOCKING**: Terraform will fail validation with syntax errors. Cannot proceed.

### After Fixing Syntax (but with truncated helm/main.tf)
🔴 **HIGH RISK**:
- Resources in state but not in code will be DELETED
- Potential data loss if PVC definitions missing
- Services may be recreated with NEW IPs (breaks DNS!)

### After Fixing Syntax + Restoring Files
🟡 **MEDIUM RISK**:
- Network policies will be DELETED if `enable_network_policies = false`
- Need to set `enable_network_policies = true` first

### After All Fixes
🟢 **LOW RISK**: Safe to apply with proper configuration

---

## Immediate Action Required

### Priority 1: Fix Syntax Errors (BLOCKING)
```bash
cd /home/slash-31/argolis_v2/prod-gke-gemini/deployed/workloads

# Check git status
git status

# Option A: Restore from git if changes not needed
git checkout HEAD -- main.tf

# Option B: Manually fix line 130 and add closing brace
# Add:
st
}  # Close twingate module
```

### Priority 2: Restore helm/main.tf
```bash
cd /home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/helm

# Check what's in git
git log --oneline main.tf | head -5

# Restore from before truncation
git checkout HEAD^ -- main.tf
# OR from specific commit:
git checkout <commit-hash> -- main.tf

# Verify restoration
wc -l main.tf  # Should be ~939 lines
```

### Priority 3: Align Configuration with Deployed State
```bash
cd /home/slash-31/argolis_v2/prod-gke-gemini/deployed/workloads

# Edit terraform.tfvars line 82:
enable_network_policies = true  # Change false → true

# Verify
grep enable_network_policies terraform.tfvars
```

### Priority 4: Validate Configuration
```bash
terraform fmt -recursive
terraform validate
terraform plan  # Review for unexpected changes
```

---

## What Should Terraform Show (After Fixes)

### Expected Plan Output
```
No changes. Your infrastructure matches the configuration.
```

### Or Minimal Changes
```
Plan: 0 to add, 1 to change, 0 to destroy.

Changes:
  ~ module.helm.kubernetes_namespace.twingate
    ~ labels: (minor label updates)
```

### ⚠️ Warning Signs of Problems
If plan shows any of these, **DO NOT APPLY**:
```
Plan: X to add, Y to change, Z to destroy

Changes:
  - kubernetes_service.adguard_dns_tcp (destroy)
  - kubernetes_persistent_volume_claim.adguard_config (destroy)
  - kubernetes_network_policy.adguard_access_policy (destroy)
```

These indicate drift not properly resolved.

---

## Recommended Recovery Steps

### Step 1: Assess Git History
```bash
cd /home/slash-31/argolis_v2/prod-gke-gemini/deployed

# Check recent commits
git log --oneline --all --graph | head -20

# Check what files changed
git status
git diff HEAD

# Check for uncommitted but good versions
git stash list
```

### Step 2: Restore Files
```bash
# If good version in git:
git checkout HEAD -- workloads/main.tf
git checkout HEAD -- modules/helm/main.tf

# If need to go back further:
git log --oneline modules/helm/main.tf
git checkout <commit-before-truncation> -- modules/helm/main.tf
```

### Step 3: Verify Restoration
```bash
# Check file line counts
wc -l workloads/main.tf        # Should be ~135-140 lines
wc -l modules/helm/main.tf     # Should be ~939 lines
wc -l modules/twingate/main.tf # Should be ~404 lines

# Check for syntax errors
terraform fmt -check -recursive
terraform validate
```

### Step 4: Align Configuration
```bash
# Update terraform.tfvars to match deployed state
vi workloads/terraform.tfvars

# Changes needed:
# - enable_network_policies = true (line 82)
# - Verify adguard_replicas = 1 (line 23)
```

### Step 5: Safe Terraform Plan
```bash
cd workloads
export GOOGLE_APPLICATION_CREDENTIALS=/home/slash-31/junk/terraform-admin-jwt.json

terraform plan -out=tfplan

# Review plan carefully:
# - Should show "No changes" or minimal changes
# - Should NOT destroy any resources
# - Should NOT recreate LoadBalancers (IPs must stay same)
```

### Step 6: Apply Only If Safe
```bash
# Only if plan looks good:
terraform apply tfplan

# Monitor for issues:
kubectl get pods -A -w
```

---

## Files Requiring Immediate Attention

### 🔴 Critical (Blocking)
1. `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/workloads/main.tf`
   - Issue: Truncated line 130, missing closing brace
   - Action: Restore from git or manual fix

2. `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/modules/helm/main.tf`
   - Issue: 63% of file missing (349/939 lines)
   - Action: Restore from git (find commit before truncation)

### 🟡 High Priority (Configuration Drift)
3. `/home/slash-31/argolis_v2/prod-gke-gemini/deployed/workloads/terraform.tfvars`
   - Issue: `enable_network_policies = false` but policies active
   - Action: Change to `true` on line 82

### 🟢 Low Priority (Best Practice)
4. All files: Replace `:latest` tags with specific versions
5. Add PodDisruptionBudget resources
6. Add resource request/limit validations

---

## Validation Checklist

After restoring files, verify:

- [ ] `terraform fmt -check -recursive` passes
- [ ] `terraform validate` passes
- [ ] `terraform plan` shows no unexpected changes
- [ ] workloads/main.tf ends with proper closing braces
- [ ] modules/helm/main.tf is ~939 lines
- [ ] `enable_network_policies = true` in tfvars
- [ ] No resource deletions in plan
- [ ] LoadBalancer IPs preserved in plan
- [ ] PVC resources present in helm/main.tf
- [ ] Security contexts present in configurations
- [ ] Git status shows expected changes only

---

## Current State Summary

**Infrastructure**: ✅ Operational and secure
**Terraform Configuration**: ❌ Broken (syntax errors, truncated files)
**Configuration Alignment**: ⚠️ Drift detected (network policies)
**Can Deploy New Changes**: ❌ No (must fix config first)
**Risk of Data Loss**: 🔴 HIGH (if applied with current broken config)

**Recommended Next Action**: Restore configuration files from git before any terraform operations.

---

## References

- Code Quality Review: Agent analysis completed
- Deployed State: Captured in /tmp/adguard-deployed.yaml and /tmp/twingate-deployed.yaml
- Implementation Summary: /home/slash-31/ai_projects/lab_task/IMPLEMENTATION_SUMMARY.md
- Change Log: /home/slash-31/ai_projects/lab_task/CHANGE_LOG.md

---

**Generated**: 2025-10-29
**Status**: Configuration restoration required before further operations
