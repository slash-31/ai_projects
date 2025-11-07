# Tag Reference Guide

This document explains the tagging strategy used by the Palo Alto Address Object Manager.

## Automatic Tag Creation

The script now **automatically creates all required tags** before creating address objects. This happens in three phases:

1. **Phase 1**: Scan CSV and collect all unique tags
2. **Phase 2**: Create all tags in the firewall (if they don't exist)
3. **Phase 3**: Create address objects with those tags

## Tag Categories

### Universal Tags (Apply to ALL resources)

These tags identify **all objects from your GKE cluster**:

| Tag | Description | Use Case |
|-----|-------------|----------|
| `auto-created` | Identifies all script-created objects | Find all objects created by this script |
| `cluster:us-central1-prod` | Identifies specific cluster | Find all objects from this cluster |

**To view ALL GKE cluster resources in firewall:**
- Filter by: `cluster:us-central1-prod` OR `auto-created`

### Environment Tags

| Tag | Description |
|-----|-------------|
| `env:prod` | Production environment |
| `env:dev` | Development environment |
| `env:staging` | Staging environment |

### Resource Type Tags

| Tag | Description | Examples |
|-----|-------------|----------|
| `type:infrastructure` | Physical/virtual infrastructure | Nodes, VMs, VPN gateways |
| `type:internalloadbalancer` | Internal load balancers | GCP Internal LBs |
| `type:externalloadbalancer` | External load balancers | Public-facing LBs |
| `type:clusterip` | Kubernetes ClusterIP services | Internal K8s services |
| `type:pod` | Kubernetes pods | Running containers |
| `type:nodeport` | Kubernetes NodePort services | Node-exposed services |

### Namespace Tags

| Tag | Description |
|-----|-------------|
| `namespace:adguard` | AdGuard DNS namespace |
| `namespace:rustdesk` | RustDesk remote desktop namespace |
| `namespace:n8n` | n8n workflow automation namespace |
| `namespace:twingate` | Twingate zero-trust namespace |
| `namespace:none` | Non-Kubernetes resources |

### Zone Tags

| Tag | Description |
|-----|-------------|
| `zone:us-central1` | Regional resources |
| `zone:us-central1-a` | Zone A resources |
| `zone:us-central1-b` | Zone B resources |
| `zone:us-central1-c` | Zone C resources |

### Service Tags

| Tag | Description |
|-----|-------------|
| `service:adguard` | AdGuard DNS services |
| `service:rustdesk` | RustDesk remote desktop services |
| `service:n8n` | n8n workflow services |
| `service:twingate` | Twingate connector services |
| `service:meraki` | Meraki network devices |
| `service:gke` | GKE infrastructure |

## Common Use Cases

### Find All GKE Cluster Resources
**Filter**: `cluster:us-central1-prod`

This single tag identifies every resource from your GKE cluster across all namespaces, zones, and types.

### Find All AdGuard Resources
**Filters**: `namespace:adguard` OR `service:adguard`

### Find All Production Resources
**Filter**: `env:prod`

### Find All Pods
**Filter**: `type:pod`

### Find Resources in Specific Zone
**Filter**: `zone:us-central1-a`

### Find All Script-Created Objects
**Filter**: `auto-created`

Useful for cleanup or auditing automated changes.

### Find Specific Service Across All Types
**Filters**: `service:adguard`

This will show:
- LoadBalancers
- ClusterIPs
- Pods
- Any other AdGuard resources

## Tag Combinations

You can combine tags for precise filtering:

### AdGuard Production Pods
- `env:prod` AND `service:adguard` AND `type:pod`

### All Zone A Infrastructure
- `zone:us-central1-a` AND `type:infrastructure`

### All Internal Load Balancers
- `type:internalloadbalancer`

### Twingate Resources in Production
- `service:twingate` AND `env:prod`

## Managing Tags in Firewall

### View All Tags
Navigate to: **Device → Objects → Tags**

### Filter Address Objects by Tag
Navigate to: **Device → Objects → Addresses**
- Click the filter icon
- Select tags to filter

### View Tag Usage
In the Tags page, each tag shows how many objects use it.

## Tag Naming Conventions

All tags follow these rules:
- **Lowercase**: All tags are lowercase
- **No spaces**: Spaces are converted to hyphens
- **Colon separator**: Category:value format (e.g., `type:pod`)
- **Hyphen for multi-word**: `internal-loadbalancer` not `internal_loadbalancer`

## Cleanup Examples

### Remove All Script-Created Objects
1. Navigate to **Device → Objects → Addresses**
2. Filter by tag: `auto-created`
3. Select all
4. Delete
5. Commit

### Remove Specific Cluster Objects
1. Filter by tag: `cluster:us-central1-prod`
2. Select all
3. Delete
4. Commit

## Tag Colors (Optional)

You can assign colors to tags in the firewall UI for visual organization:
- **Red**: Production resources
- **Yellow**: Development resources
- **Green**: Healthy/active services
- **Blue**: Infrastructure
- **Purple**: Security-related (like Twingate)

## Automation Notes

- Tags are **automatically created** by the script
- If a tag already exists, it's **skipped** (not duplicated)
- Tag creation happens **before** address object creation
- All tags are created at the **vsys level** (not Panorama)

## Troubleshooting

### "Tag does not exist" Error
This shouldn't happen with v2.0.0+ as tags are auto-created. If you see this:
1. Check script output for Phase 2 (tag creation)
2. Verify tags were created: Device → Objects → Tags
3. Re-run script - it will skip existing tags

### Tag Shows Zero Objects
- The tag exists but no objects use it yet
- Check if address object creation succeeded
- Verify tag name matches exactly (case-sensitive)

## Version History

- **v2.0.0**: Added automatic tag creation
- **v1.0.0**: Tags had to be manually created first
