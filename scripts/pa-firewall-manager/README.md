# Palo Alto Firewall Address Object Manager

Automated management of Palo Alto Networks firewall address objects using the XML API. This script reads IP addresses and metadata from a CSV file and creates organized, tagged address objects in your firewall.

## Features

- ✅ **Bulk Creation**: Process hundreds of address objects from a single CSV file
- ✅ **Intelligent Tagging**: Automatic tag generation based on metadata (environment, type, namespace, zone, service)
- ✅ **Dry Run Mode**: Preview changes before applying them
- ✅ **Error Handling**: Robust error handling with detailed logging
- ✅ **Reusable**: Designed for repeated use with different environments and clusters
- ✅ **Safe**: Connection testing and optional manual commit control

## Requirements

### System Requirements
- Python 3.7 or higher
- Network connectivity to your Palo Alto firewall

### Python Setup (Recommended: Use Virtual Environment)

**Option 1: Virtual Environment (Recommended)**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Deactivate when done
deactivate
```

**Option 2: System-wide Installation**
```bash
pip install -r requirements.txt
```

> **Note**: See [SETUP.md](SETUP.md) for detailed virtual environment setup guide.

### Firewall Requirements
- Palo Alto firewall with API access enabled
- Valid API key with sufficient permissions:
  - Configuration Read/Write
  - Commit permissions

## Quick Start

### 0. Setup Python Environment (First Time Only)

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
pip list
```

> **Tip**: The wrapper script `update-firewall-gke.sh` automatically detects and uses the venv if it exists.

### 1. Generate API Key

Generate an API key from your Palo Alto firewall:

```bash
# SSH to firewall or use web UI
# CLI method:
request api-key generate name="api-automation" lifetime=525600
```

Or via web UI:
1. Navigate to: Device → Setup → Management → Authentication Settings
2. Click "Generate" under API Key Management
3. Save the generated key securely

### 2. Prepare Your CSV File

Ensure your CSV file has the required columns (see CSV Structure section below):

```csv
IP_Address,Hostname,Service_Name,Type,Ports,Function,Zone,Namespace
172.27.32.11,adguard-web-lb,adguard-web,Internal LoadBalancer,80/TCP,AdGuard Web UI,us-central1,adguard
```

### 3. Run the Script

**Easy Way (using wrapper script):**
```bash
# Wrapper automatically uses venv if available
export PA_API_KEY="your-api-key"

# Dry run first
./update-firewall-gke.sh dry-run

# Then run for real
./update-firewall-gke.sh
```

**Manual Way (if you need more control):**
```bash
# Activate venv first
source venv/bin/activate

# Dry run
python pa_address_manager.py \
  --api-key "$PA_API_KEY" \
  --csv-file gke-cluster-private-ips.csv \
  --dry-run

# Create objects and commit
python pa_address_manager.py \
  --api-key "$PA_API_KEY" \
  --csv-file gke-cluster-private-ips.csv

# Deactivate venv
deactivate
```

## CSV File Structure

### Required Columns

Your CSV file **must** include these columns (order doesn't matter):

| Column | Description | Example |
|--------|-------------|---------|
| `IP_Address` | IP address (CIDR optional) | `172.27.32.11` or `172.27.32.0/24` |
| `Hostname` | Unique hostname/identifier | `adguard-web-lb` |
| `Service_Name` | Service identifier | `adguard-web` |
| `Type` | Resource type | `Infrastructure`, `Internal LoadBalancer`, `ClusterIP`, `Pod` |
| `Function` | Description of function | `AdGuard Web UI (HTTP)` |
| `Zone` | GCP zone or region | `us-central1` or `us-central1-a` |
| `Namespace` | Kubernetes namespace | `adguard`, `N/A` for non-k8s resources |

### Optional Columns

| Column | Description | Example |
|--------|-------------|---------|
| `Ports` | Port/protocol info | `80/TCP`, `53/UDP`, `All` |

### CSV Template

Create your CSV file with this structure:

```csv
IP_Address,Hostname,Service_Name,Type,Ports,Function,Zone,Namespace
172.27.32.11,adguard-web-lb,adguard-web,Internal LoadBalancer,80/TCP,AdGuard Web UI (HTTP),us-central1,adguard
172.27.32.12,gke-node-1,GKE Node,Infrastructure,All,GKE Worker Node,us-central1-a,N/A
172.27.46.5,adguard-pod-1,adguard-home-pod,Pod,All,AdGuard container,us-central1-a,adguard
```

### Exporting from GKE

To extract IP information from your GKE cluster:

**Get Node IPs:**
```bash
kubectl get nodes -o custom-columns=\
NAME:.metadata.name,\
IP:.status.addresses[0].address,\
ZONE:.metadata.labels.topology\\.kubernetes\\.io/zone
```

**Get Service IPs:**
```bash
kubectl get svc -A -o custom-columns=\
NAMESPACE:.metadata.namespace,\
NAME:.metadata.name,\
TYPE:.spec.type,\
CLUSTER-IP:.spec.clusterIP,\
EXTERNAL-IP:.status.loadBalancer.ingress[0].ip
```

**Get Pod IPs:**
```bash
kubectl get pods -A -o custom-columns=\
NAMESPACE:.metadata.namespace,\
NAME:.metadata.name,\
IP:.status.podIP,\
NODE:.spec.nodeName
```

## Tagging Structure

The script automatically generates tags based on your CSV data:

### Tag Categories

1. **Environment**: `env:prod`, `env:dev`, `env:staging`
   - Controlled by `--environment` flag
   - Default: `prod`

2. **Type**: `type:infrastructure`, `type:loadbalancer`, `type:clusterip`, `type:pod`
   - Derived from CSV `Type` column
   - Automatically lowercased and spaces removed

3. **Namespace**: `namespace:adguard`, `namespace:rustdesk`, `namespace:none`
   - Derived from CSV `Namespace` column
   - `N/A` values converted to `namespace:none`

4. **Zone**: `zone:us-central1-a`, `zone:us-central1-b`, `zone:us-central1`
   - Derived from CSV `Zone` column

5. **Service**: `service:adguard`, `service:rustdesk`, `service:n8n`
   - Derived from CSV `Service_Name` column (first component)
   - Example: `adguard-web-lb` → `service:adguard`

6. **Cluster**: `cluster:us-central1-prod`
   - Controlled by `--cluster` flag
   - Default: `us-central1-prod`

7. **Automation**: `auto-created`
   - Applied to all objects created by this script
   - Helps identify automated vs. manual objects

### Example Tags

For this CSV row:
```csv
172.27.32.11,adguard-web-lb,adguard-web,Internal LoadBalancer,80/TCP,AdGuard Web UI,us-central1,adguard
```

Generated tags:
- `env:prod`
- `type:internalloadbalancer`
- `namespace:adguard`
- `zone:us-central1`
- `service:adguard`
- `cluster:us-central1-prod`
- `auto-created`

## Usage Examples

### Basic Usage

```bash
# Create objects with default settings
python3 pa_address_manager.py \
  --api-key YOUR_API_KEY \
  --csv-file gke-cluster-private-ips.csv
```

### Dry Run (Test Mode)

```bash
# Preview what would be created without making changes
python3 pa_address_manager.py \
  --api-key YOUR_API_KEY \
  --csv-file gke-cluster-private-ips.csv \
  --dry-run
```

### Different Environment

```bash
# Tag objects as development environment
python3 pa_address_manager.py \
  --api-key YOUR_API_KEY \
  --csv-file dev-cluster-ips.csv \
  --environment dev \
  --cluster us-east1-dev
```

### Different Firewall

```bash
# Target a different firewall
python3 pa_address_manager.py \
  --api-key YOUR_API_KEY \
  --csv-file gke-ips.csv \
  --firewall other-firewall.example.com
```

### Create Without Committing

```bash
# Create objects but don't commit (allows manual review)
python3 pa_address_manager.py \
  --api-key YOUR_API_KEY \
  --csv-file gke-ips.csv \
  --no-commit
```

Then manually commit via CLI or Web UI:
```bash
# Manual commit via CLI
ssh admin@firewall
commit
```

### Verbose Logging

```bash
# Enable detailed debug output
python3 pa_address_manager.py \
  --api-key YOUR_API_KEY \
  --csv-file gke-ips.csv \
  --verbose
```

## Command-Line Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--api-key` | Yes | - | Palo Alto firewall API key |
| `--csv-file` | Yes | - | Path to CSV file |
| `--firewall` | No | `munich-pa-415.securitydude.us` | Firewall hostname/IP |
| `--environment` | No | `prod` | Environment tag (prod/dev/staging) |
| `--cluster` | No | `us-central1-prod` | GKE cluster name for tagging |
| `--dry-run` | No | `False` | Preview mode - no changes made |
| `--no-commit` | No | `False` | Create objects without committing |
| `--verify-ssl` | No | `False` | Verify SSL certificates |
| `--verbose` | No | `False` | Enable debug logging |

## Error Handling

### Common Errors

**"Failed to connect to firewall"**
- Check firewall hostname/IP is correct
- Verify API key is valid
- Ensure network connectivity
- Check firewall management interface is accessible

**"CSV missing required columns"**
- Verify CSV has all required column headers
- Check for typos in column names
- Ensure column names match exactly (case-sensitive)

**"API request failed"**
- API key may have expired
- Insufficient permissions on API key
- Firewall may be busy or unreachable

**"Failed to create address object"**
- Object name may already exist
- Object name may contain invalid characters
- IP address format may be invalid

### Validation

The script performs these validations:

1. ✅ CSV file exists and is readable
2. ✅ All required columns are present
3. ✅ Firewall connection is successful
4. ✅ API key is valid
5. ✅ IP addresses are properly formatted
6. ✅ Hostnames are sanitized for firewall naming rules

## Security Best Practices

### API Key Management

**DO NOT** hardcode API keys in scripts or commit them to git.

**Option 1: Environment Variable**
```bash
export PA_API_KEY="your-api-key-here"
python3 pa_address_manager.py --api-key "$PA_API_KEY" --csv-file data.csv
```

**Option 2: Read from Secure File**
```bash
python3 pa_address_manager.py --api-key "$(cat ~/.pa-api-key)" --csv-file data.csv
```

**Option 3: Use Secret Manager**
```bash
# GCP Secret Manager example
export PA_API_KEY=$(gcloud secrets versions access latest --secret="pa-api-key")
python3 pa_address_manager.py --api-key "$PA_API_KEY" --csv-file data.csv
```

### Firewall API Key Permissions

Create a dedicated API key with minimal required permissions:

1. Configuration: Read/Write
2. Commit: Yes
3. Validity: Set appropriate expiration
4. Admin role: Read-only admin (if possible)

### SSL Verification

By default, SSL verification is disabled (`--verify-ssl=False`) because many Palo Alto firewalls use self-signed certificates.

For production environments with proper certificates:
```bash
python3 pa_address_manager.py \
  --api-key YOUR_KEY \
  --csv-file data.csv \
  --verify-ssl
```

## Reusability Guidelines

### For Multiple Environments

Create environment-specific CSV files:

```
gke-prod-ips.csv
gke-dev-ips.csv
gke-staging-ips.csv
```

Run with appropriate flags:
```bash
# Production
python3 pa_address_manager.py --api-key $KEY --csv-file gke-prod-ips.csv --environment prod

# Development
python3 pa_address_manager.py --api-key $KEY --csv-file gke-dev-ips.csv --environment dev
```

### For Multiple Clusters

```bash
# US Central cluster
python3 pa_address_manager.py --csv-file us-central1.csv --cluster us-central1-prod

# US East cluster
python3 pa_address_manager.py --csv-file us-east1.csv --cluster us-east1-prod
```

### Automation with Scripts

Create a wrapper script for repeated use:

```bash
#!/bin/bash
# update-firewall-objects.sh

set -e

# Load API key from secure location
API_KEY=$(cat ~/.pa-api-key)

# Update prod cluster objects
python3 pa_address_manager.py \
  --api-key "$API_KEY" \
  --csv-file gke-cluster-private-ips.csv \
  --environment prod \
  --cluster us-central1-prod

echo "Firewall objects updated successfully"
```

### Scheduled Updates (Cron)

```bash
# Update firewall objects daily at 2 AM
0 2 * * * /home/user/scripts/update-firewall-objects.sh >> /var/log/pa-updates.log 2>&1
```

## Troubleshooting

### Enable Verbose Logging

```bash
python3 pa_address_manager.py --api-key $KEY --csv-file data.csv --verbose
```

### Test Connection Only

```bash
# Dry run with verbose logging
python3 pa_address_manager.py --api-key $KEY --csv-file data.csv --dry-run --verbose
```

### Verify Firewall Configuration

```bash
# SSH to firewall and check address objects
ssh admin@munich-pa-415.securitydude.us

# List all address objects with auto-created tag
show config running xpath "/config/devices/entry/vsys/entry/address" | match auto-created
```

### Manual Rollback

If you need to remove created objects:

```bash
# Delete objects with auto-created tag via CLI
delete config devices localhost.localdomain vsys vsys1 address [object-name]
commit
```

## Performance Considerations

- **Batch Size**: Script processes all CSV rows sequentially
- **API Rate Limits**: Palo Alto firewalls have API rate limits (typically 100-200 req/min)
- **Commit Time**: Commits can take 30-60 seconds depending on firewall config size
- **Large CSV Files**: For 1000+ objects, consider splitting into batches

For large deployments (500+ objects):
```bash
# Split CSV and run separately
split -l 200 large-file.csv batch-
python3 pa_address_manager.py --api-key $KEY --csv-file batch-aa --no-commit
python3 pa_address_manager.py --api-key $KEY --csv-file batch-ab --no-commit
# ... then commit manually
```

## Version History

- **v1.0.0** (2025-11-07)
  - Initial release
  - Support for CSV-based address object creation
  - Automatic tag generation
  - Dry run mode
  - Error handling and logging

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:
- Review this README and CSV structure documentation
- Check the inline script documentation
- Verify your CSV file format matches the template
- Test with `--dry-run` first

## Author

Joshua Koch
