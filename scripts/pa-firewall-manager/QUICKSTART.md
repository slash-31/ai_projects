# Quick Start Guide

Get started with the Palo Alto Address Object Manager in 5 minutes.

## Step 0: Setup Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note**: You only need to do this once. The wrapper script will automatically use the venv.

## Step 2: Set Your API Key

Choose one method:

**Option A: Environment Variable**
```bash
export PA_API_KEY="your-api-key-here"
```

**Option B: Secure File**
```bash
echo "your-api-key-here" > ~/.pa-api-key
chmod 600 ~/.pa-api-key
export PA_API_KEY=$(cat ~/.pa-api-key)
```

**Option C: GCP Secret Manager**
```bash
export PA_API_KEY=$(gcloud secrets versions access latest --secret="pa-api-key")
```

## Step 3: Test with Dry Run

**Recommended - Use wrapper script** (automatically uses venv):
```bash
./update-firewall-gke.sh dry-run
```

**Or manually** (activate venv first):
```bash
source venv/bin/activate
python pa_address_manager.py \
  --api-key "$PA_API_KEY" \
  --csv-file gke-cluster-private-ips.csv \
  --dry-run
deactivate
```

## Step 4: Create Objects

**Recommended - Use wrapper script**:
```bash
./update-firewall-gke.sh
```

**Or manually**:
```bash
source venv/bin/activate
python pa_address_manager.py \
  --api-key "$PA_API_KEY" \
  --csv-file gke-cluster-private-ips.csv
deactivate
```

## Expected Output

```
======================================================================
Palo Alto Firewall Address Object Manager v1.0.0
======================================================================

2025-11-07 10:00:00 - INFO - Initialized connection to firewall: munich-pa-415.securitydude.us
2025-11-07 10:00:01 - INFO - ✓ Successfully connected to firewall

2025-11-07 10:00:02 - INFO - Processing CSV file: gke-cluster-private-ips.csv
2025-11-07 10:00:02 - INFO - Row 2: meraki-vmx-small (172.27.0.2)
2025-11-07 10:00:02 - INFO -   Description: Meraki vMX VPN Gateway - 172.27.0.2
2025-11-07 10:00:02 - INFO -   Tags: env:prod, type:infrastructure, namespace:none, zone:us-central1-a, service:meraki, cluster:us-central1-prod, auto-created
2025-11-07 10:00:03 - INFO - ✓ Created address object: meraki-vmx-small (172.27.0.2/32)
...

2025-11-07 10:00:30 - INFO - Committing changes to firewall...
2025-11-07 10:00:45 - INFO - ✓ Successfully committed changes

======================================================================
Summary
======================================================================
Created:  26
Failed:   0
Skipped:  0

All changes have been committed to the firewall
======================================================================
```

## Troubleshooting

**"Failed to connect to firewall"**
- Verify firewall hostname is reachable: `ping munich-pa-415.securitydude.us`
- Check API key is correct
- Ensure management interface allows your IP

**"CSV missing required columns"**
- Check CSV has all required headers: `head -1 gke-cluster-private-ips.csv`
- See CSV_STRUCTURE.md for required columns

**"Permission denied"**
- Make scripts executable: `chmod +x pa_address_manager.py update-firewall-gke.sh`

## Next Steps

- Read **README.md** for detailed documentation
- Review **CSV_STRUCTURE.md** for CSV file format guidance
- Check tags in firewall: Device → Objects → Tags
- View created objects: Device → Objects → Addresses (filter by tag "auto-created")

## Useful Commands

**List all auto-created objects:**
```bash
# Via firewall CLI
show config running xpath "/config/devices/entry/vsys/entry/address" | match auto-created
```

**Update objects regularly (cron):**
```bash
# Add to crontab
0 2 * * * /home/slash-31/ai_projects/scripts/update-firewall-gke.sh >> /var/log/pa-updates.log 2>&1
```

**Different environment:**
```bash
python3 pa_address_manager.py \
  --api-key "$PA_API_KEY" \
  --csv-file dev-cluster.csv \
  --environment dev \
  --cluster us-east1-dev
```
