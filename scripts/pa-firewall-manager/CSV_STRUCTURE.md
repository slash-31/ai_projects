# CSV File Structure Documentation

This document provides detailed guidance on structuring your CSV file for use with the Palo Alto Address Object Manager script.

## Table of Contents
- [Required Columns](#required-columns)
- [Optional Columns](#optional-columns)
- [CSV Templates](#csv-templates)
- [Data Extraction Examples](#data-extraction-examples)
- [Validation Rules](#validation-rules)
- [Best Practices](#best-practices)

---

## Required Columns

These columns **must** be present in your CSV file (order doesn't matter):

### IP_Address
- **Description**: The IP address for the address object
- **Format**: IPv4 address, optionally with CIDR notation
- **Examples**:
  - `172.27.32.11` (automatically becomes `/32`)
  - `172.27.32.0/24` (subnet)
  - `10.0.0.1` (single host)
- **Validation**: Must be a valid IP address format
- **Notes**: Script automatically adds `/32` if CIDR is omitted

### Hostname
- **Description**: Unique identifier/hostname for the resource
- **Format**: Alphanumeric with hyphens, underscores, dots
- **Examples**:
  - `adguard-web-lb`
  - `gke-us-central1-prod-node-1`
  - `meraki-vmx-small`
- **Validation**: Must be unique, will be sanitized for firewall (dots → underscores)
- **Notes**: Used as the address object name in the firewall

### Service_Name
- **Description**: The service/application identifier
- **Format**: Lowercase with hyphens
- **Examples**:
  - `adguard-web`
  - `rustdesk-hbbr`
  - `twingate-connector`
  - `n8n-service`
- **Validation**: Should follow naming convention
- **Notes**: First component used for `service:` tag (e.g., `adguard-web` → `service:adguard`)

### Type
- **Description**: Resource type/category
- **Format**: Descriptive string
- **Valid Values**:
  - `Infrastructure` (for nodes, VMs, physical devices)
  - `Internal LoadBalancer` (for GCP/cloud load balancers)
  - `External LoadBalancer` (for public-facing load balancers)
  - `ClusterIP` (for Kubernetes ClusterIP services)
  - `Pod` (for Kubernetes pods)
  - `NodePort` (for Kubernetes NodePort services)
  - `VM` (for virtual machines)
  - `Container` (for containers)
- **Validation**: Free text, but should be consistent
- **Notes**: Converted to lowercase and used for `type:` tag

### Function
- **Description**: Human-readable description of the resource's purpose
- **Format**: Free text description
- **Examples**:
  - `AdGuard Web UI (HTTP)`
  - `GKE Worker Node`
  - `DNS over TCP (Internal)`
  - `Twingate connector container #1`
  - `Meraki vMX VPN Gateway`
- **Validation**: None, but should be descriptive
- **Notes**: Used in the address object description field

### Zone
- **Description**: Geographic zone/region/location
- **Format**: Cloud provider zone or custom location identifier
- **Examples**:
  - `us-central1` (GCP region)
  - `us-central1-a` (GCP zone)
  - `us-east-1a` (AWS zone)
  - `eastus` (Azure region)
  - `datacenter-1` (custom)
- **Validation**: Should follow cloud provider naming or be consistent
- **Notes**: Used for `zone:` tag

### Namespace
- **Description**: Kubernetes namespace or logical grouping
- **Format**: Lowercase alphanumeric with hyphens
- **Examples**:
  - `adguard`
  - `rustdesk`
  - `twingate`
  - `default`
  - `kube-system`
  - `N/A` (for non-Kubernetes resources)
- **Validation**: Use `N/A` for non-namespaced resources
- **Notes**: `N/A` values converted to `namespace:none` tag

---

## Optional Columns

These columns are not required but provide additional context:

### Ports
- **Description**: Port numbers and protocols used
- **Format**: Port/Protocol notation
- **Examples**:
  - `80/TCP`
  - `53/UDP`
  - `443/TCP`
  - `21115-21118/TCP+UDP`
  - `All`
- **Validation**: None
- **Notes**: Informational only, not used by script

### Notes
- **Description**: Additional notes or comments
- **Format**: Free text
- **Examples**:
  - `Primary DNS server`
  - `Migrating to new zone`
  - `Temporary - remove after Q4`
- **Validation**: None
- **Notes**: Can be added for your reference

---

## CSV Templates

### Template 1: Basic GKE Resources

```csv
IP_Address,Hostname,Service_Name,Type,Ports,Function,Zone,Namespace
172.27.32.11,adguard-web-lb,adguard-web,Internal LoadBalancer,80/TCP,AdGuard Web UI (HTTP),us-central1,adguard
172.27.32.12,gke-worker-node-1,gke-node,Infrastructure,All,GKE Worker Node,us-central1-a,N/A
172.27.46.5,adguard-pod-1,adguard-home,Pod,All,AdGuard DNS container,us-central1-a,adguard
172.27.50.94,n8n-service,n8n-web,ClusterIP,443/TCP,n8n workflow automation,us-central1,n8n
```

### Template 2: Mixed Infrastructure

```csv
IP_Address,Hostname,Service_Name,Type,Ports,Function,Zone,Namespace
10.0.128.10,core-router-1,router,Infrastructure,All,Core network router,munich-dc,N/A
10.0.128.20,firewall-primary,firewall,Infrastructure,All,Palo Alto firewall,munich-dc,N/A
192.168.1.1,wifi-controller,unifi,Infrastructure,8443/TCP,UniFi Network Controller,willowcreek,N/A
172.27.32.11,lb-adguard,adguard-lb,Internal LoadBalancer,53/UDP,DNS load balancer,us-central1,adguard
```

### Template 3: Multi-Site Deployment

```csv
IP_Address,Hostname,Service_Name,Type,Ports,Function,Zone,Namespace
10.0.128.100,munich-vpn-gw,vpn-gateway,Infrastructure,IPSec,Munich VPN endpoint,munich-dc,N/A
10.101.53.10,binaryfu-vpn-gw,vpn-gateway,Infrastructure,IPSec,BinaryFU VPN endpoint,binaryfu-dc,N/A
192.168.1.1,willowcreek-vpn-gw,vpn-gateway,Infrastructure,IPSec,WillowCreek VPN endpoint,willowcreek-dc,N/A
172.27.32.100,gcp-vpn-gw,vpn-gateway,Infrastructure,IPSec,GCP VPN endpoint,us-central1,N/A
```

---

## Data Extraction Examples

### From GKE Cluster

#### 1. Extract Node Information

```bash
# Get all nodes with IPs and zones
kubectl get nodes -o custom-columns=\
IP:.status.addresses[?(@.type==\"InternalIP\")].address,\
HOSTNAME:.metadata.name,\
ZONE:.metadata.labels.topology\\.kubernetes\\.io/zone \
--no-headers | \
awk '{print $1 "," $2 ",gke-node,Infrastructure,All,GKE Worker Node," $3 ",N/A"}'
```

**Output format**:
```
172.27.32.12,gke-us-central1-prod-node-1,gke-node,Infrastructure,All,GKE Worker Node,us-central1-a,N/A
```

#### 2. Extract Service LoadBalancer IPs

```bash
# Get LoadBalancer services
kubectl get svc -A -o json | jq -r '
  .items[] |
  select(.spec.type == "LoadBalancer") |
  [
    .status.loadBalancer.ingress[0].ip // .spec.clusterIP,
    .metadata.name + "-lb",
    .metadata.name,
    .spec.type,
    (.spec.ports[0].port|tostring) + "/" + .spec.ports[0].protocol,
    "LoadBalancer for " + .metadata.name,
    "us-central1",
    .metadata.namespace
  ] | @csv
' | tr -d '"'
```

#### 3. Extract ClusterIP Services

```bash
# Get ClusterIP services
kubectl get svc -A -o json | jq -r '
  .items[] |
  select(.spec.type == "ClusterIP") |
  [
    .spec.clusterIP,
    .metadata.name + "-clusterip",
    .metadata.name,
    "ClusterIP",
    (.spec.ports[0].port|tostring) + "/" + .spec.ports[0].protocol,
    .metadata.name + " cluster IP",
    "us-central1",
    .metadata.namespace
  ] | @csv
' | tr -d '"'
```

#### 4. Extract Pod IPs

```bash
# Get pod IPs for specific namespace
kubectl get pods -n adguard -o json | jq -r '
  .items[] |
  select(.status.phase == "Running") |
  [
    .status.podIP,
    .metadata.name,
    .metadata.labels.app // .metadata.name,
    "Pod",
    "All",
    (.metadata.labels.app // .metadata.name) + " container",
    .spec.nodeName | split("-") | .[-2],
    .metadata.namespace
  ] | @csv
' | tr -d '"'
```

### From Google Cloud

#### Get Compute Instance IPs

```bash
gcloud compute instances list --format="csv(
  networkInterfaces[0].networkIP,
  name,
  name,
  'VM',
  'All',
  'Compute Engine VM',
  zone.basename(),
  'N/A'
)"
```

#### Get Cloud SQL Instances

```bash
gcloud sql instances list --format="csv(
  ipAddresses[0].ipAddress,
  name,
  name,
  'Cloud SQL',
  databaseVersion,
  'Cloud SQL database',
  region,
  'N/A'
)"
```

### From AWS

#### Get EC2 Instance Private IPs

```bash
aws ec2 describe-instances --query '
  Reservations[].Instances[].{
    IP: PrivateIpAddress,
    Hostname: Tags[?Key==`Name`]|[0].Value,
    ServiceName: Tags[?Key==`Name`]|[0].Value,
    Type: "EC2",
    Ports: "All",
    Function: "EC2 Instance",
    Zone: Placement.AvailabilityZone,
    Namespace: "N/A"
  }
' --output text
```

---

## Validation Rules

### IP Address Validation
- ✅ Valid: `172.27.32.11`, `10.0.0.1/24`, `192.168.1.0/24`
- ❌ Invalid: `256.1.1.1`, `10.0.0`, `not-an-ip`

### Hostname Validation
- ✅ Valid: `adguard-web-lb`, `node_01`, `server.example`
- ❌ Invalid: Empty string, only whitespace
- **Note**: Dots (`.`) automatically converted to underscores (`_`)

### Type Recommendations
Use consistent types across your CSV:
- Infrastructure resources: `Infrastructure`
- Kubernetes services: `ClusterIP`, `LoadBalancer`, `NodePort`
- Kubernetes pods: `Pod`
- VMs: `VM`
- Containers: `Container`

### Namespace Format
- Must be lowercase
- Use hyphens for word separation
- Use `N/A` for non-Kubernetes/non-namespaced resources
- Examples: `adguard`, `kube-system`, `istio-system`, `N/A`

---

## Best Practices

### 1. Consistent Naming Conventions

**Good**:
```csv
gke-prod-node-1,gke-prod-node,Infrastructure,...
gke-prod-node-2,gke-prod-node,Infrastructure,...
gke-prod-node-3,gke-prod-node,Infrastructure,...
```

**Avoid**:
```csv
node1,gke-node,Infrastructure,...
GKE-Node-2,node,Infrastructure,...
prod_node_3,kubernetes-node,Infrastructure,...
```

### 2. Descriptive Functions

**Good**:
```csv
...,AdGuard Web UI (HTTP port 80)
...,Primary DNS server for internal network
...,Twingate zero-trust connector #1 (us-central1-b)
```

**Avoid**:
```csv
...,Web server
...,DNS
...,Connector
```

### 3. Zone Consistency

If using GCP zones, be consistent:
```csv
us-central1-a
us-central1-b
us-central1-c
us-central1  (for regional resources)
```

### 4. Header Order

While order doesn't matter, a logical order helps readability:
```csv
IP_Address,Hostname,Service_Name,Type,Ports,Function,Zone,Namespace
```

### 5. Document Your Custom Columns

If adding custom columns beyond the required ones:
```csv
IP_Address,Hostname,Service_Name,Type,Function,Zone,Namespace,Owner,CostCenter,Expiration
172.27.32.11,adguard-lb,adguard,LoadBalancer,DNS LB,us-central1,adguard,ops-team,CC-1234,2025-12-31
```

### 6. Use Standard Namespace Values

For non-Kubernetes resources, always use `N/A`:
```csv
172.27.0.2,meraki-vmx,meraki,Infrastructure,Meraki vMX VPN,us-central1-a,N/A
```

### 7. Include Port Information

Even though optional, port information helps with documentation:
```csv
...,53/UDP,DNS over UDP,...
...,443/TCP,HTTPS,...
...,21115-21118/TCP+UDP,RustDesk signaling,...
```

---

## Restructuring Existing CSVs

### If Your CSV Has Different Columns

**Option 1: Rename Columns**

If your CSV has similar data but different names:

Current CSV:
```csv
ip,name,description,location,app
172.27.32.11,lb-dns,DNS load balancer,zone-a,adguard
```

Rename headers to match required format:
```csv
IP_Address,Hostname,Function,Zone,Service_Name
172.27.32.11,lb-dns,DNS load balancer,zone-a,adguard
```

Add missing columns with defaults:
```csv
IP_Address,Hostname,Service_Name,Type,Function,Zone,Namespace
172.27.32.11,lb-dns,adguard,LoadBalancer,DNS load balancer,zone-a,adguard
```

**Option 2: Transform with Script**

Create a transformation script:
```bash
#!/bin/bash
# transform-csv.sh

# Add header
echo "IP_Address,Hostname,Service_Name,Type,Ports,Function,Zone,Namespace"

# Transform data (skip header)
tail -n +2 old-format.csv | while IFS=',' read ip name desc location app; do
  echo "$ip,$name,$app,LoadBalancer,All,$desc,$location,$app"
done
```

**Option 3: Use awk/sed**

```bash
# Transform existing CSV
awk -F',' 'NR==1 {print "IP_Address,Hostname,Service_Name,Type,Ports,Function,Zone,Namespace"; next}
  {print $1","$2","$5","\"LoadBalancer\",\"All\","$3","$4","$5}' \
  old-format.csv > new-format.csv
```

### If You Have Extra Columns

Extra columns are ignored by the script, so they're safe to keep:

```csv
IP_Address,Hostname,Service_Name,Type,Function,Zone,Namespace,Owner,Notes
172.27.32.11,lb-dns,adguard,LoadBalancer,DNS LB,us-central1,adguard,ops-team,Primary DNS
```

The script will use required columns and ignore `Owner` and `Notes`.

---

## Testing Your CSV

### Quick Validation

```bash
# Check if required columns exist
head -1 your-file.csv | tr ',' '\n' | sort

# Should include:
# Function
# Hostname
# IP_Address
# Namespace
# Service_Name
# Type
# Zone
```

### Test with Dry Run

Always test with `--dry-run` first:

```bash
python3 pa_address_manager.py \
  --api-key YOUR_KEY \
  --csv-file your-file.csv \
  --dry-run \
  --verbose
```

This will show:
- ✅ Which columns were found
- ✅ What tags will be generated
- ✅ What address objects will be created
- ❌ Any validation errors

---

## Complete Example CSV

Here's a complete example with various resource types:

```csv
IP_Address,Hostname,Service_Name,Type,Ports,Function,Zone,Namespace
172.27.0.2,meraki-vmx-small,meraki-vpx,Infrastructure,IPSec,Meraki vMX VPN Gateway,us-central1-a,N/A
172.27.32.12,gke-node-1,gke-node,Infrastructure,All,GKE Worker Node (hosts AdGuard),us-central1-a,N/A
172.27.32.11,adguard-web-lb,adguard-web,Internal LoadBalancer,80/TCP,AdGuard Web UI (HTTP),us-central1,adguard
172.27.32.53,adguard-dns-tcp-lb,adguard-dns-tcp,Internal LoadBalancer,53/TCP,DNS over TCP (Internal),us-central1,adguard
172.27.50.129,adguard-dns-tcp-cluster,adguard-dns-tcp,ClusterIP,53/TCP,Internal cluster DNS TCP,us-central1,adguard
172.27.46.5,adguard-pod-1,adguard-home,Pod,All,AdGuard DNS container #1,us-central1-a,adguard
172.27.50.94,n8n-cluster,n8n-service,ClusterIP,443/TCP,n8n workflow automation,us-central1,n8n
172.27.43.7,n8n-pod-1,n8n-app,Pod,All,n8n workflow container,us-central1-c,n8n
```

---

## Questions or Issues?

If your CSV structure doesn't match the template:
1. Review the [Required Columns](#required-columns) section
2. Check [Data Extraction Examples](#data-extraction-examples) for your platform
3. Use [Restructuring Guide](#restructuring-existing-csvs) to transform your data
4. Test with `--dry-run --verbose` to see validation errors

The script is designed to be flexible - as long as required columns exist, additional columns won't cause issues.
