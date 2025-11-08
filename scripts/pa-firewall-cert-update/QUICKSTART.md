# Quick Start Guide - Phase 1

Phase 1 is complete! This guide walks through testing the backup and certificate discovery functionality.

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python3 pa_cert_update.py --show-api-instructions
```

## Get Your API Key

First, obtain your API key from the firewall:

```bash
# View instructions
python3 pa_cert_update.py --show-api-instructions

# Or use curl directly (replace with your firewall details)
curl -k -X GET 'https://YOUR-FIREWALL/api/?type=keygen&user=admin&password=YOUR_PASSWORD'
```

Extract the key from the XML response and save it securely.

## Phase 1 Testing

### Test Connection
```bash
# Test API connection (dry run)
python3 pa_cert_update.py \
  --firewall amdffw.prideindustries.com \
  --api-key "YOUR_API_KEY_HERE" \
  --cert-name "Pride-Wildcard-Test" \
  --cert-file ./certificates/test.crt \
  --key-file ./certificates/test.key \
  --dry-run --verbose
```

### What Phase 1 Does

1. **Tests Connection**: Validates API key and retrieves firewall info
2. **Full Backup**:
   - Exports configuration XML (`<firewall>-config-<timestamp>.xml`)
   - Exports device state archive (`<firewall>-device-state-<timestamp>.tgz`)
3. **Lists Certificates**: Queries all certificates on firewall
4. **Interactive Selection**: Prompts you to select certificate to replace
5. **Usage Analysis**: Searches configuration for all certificate references

### Expected Output

```
================================================================================
Palo Alto Firewall Certificate Update - Phase 1
================================================================================
Log file: ./logs/pa-cert-update-20251107_120000.log
Firewall: amdffw.prideindustries.com
New certificate name: Pride-Wildcard-Test
Certificate file: ./certificates/test.crt
Key file: ./certificates/test.key
DRY RUN MODE - No changes will be made

Testing API connection and authentication...
✓ Connection successful!
  Hostname: amdffw
  Model: PA-3220
  PAN-OS Version: 10.1.5

================================================================================
FULL FIREWALL BACKUP
================================================================================
Backing up firewall configuration...
✓ Configuration backed up successfully
  File: ./backups/amdffw.prideindustries.com-config-20251107_120000.xml
  Size: 1,234,567 bytes

Backing up device state (this may take a few minutes)...
✓ Device state backed up successfully
  File: ./backups/amdffw.prideindustries.com-device-state-20251107_120000.tgz
  Size: 45,678,901 bytes (43.6 MB)

--------------------------------------------------------------------------------
BACKUP SUMMARY
--------------------------------------------------------------------------------
✓ Configuration: ./backups/amdffw.prideindustries.com-config-20251107_120000.xml
✓ Device State: ./backups/amdffw.prideindustries.com-device-state-20251107_120000.tgz
================================================================================

Retrieving certificate list from firewall...
✓ Found 5 certificate(s)

================================================================================
CERTIFICATES ON FIREWALL
================================================================================

1. Pride-Wildcard-December-2025
   Common Name: *.prideindustries.com
   Issuer: DigiCert
   Expiry: 2025-12-31

2. Pride-Wildcard-June-2025
   Common Name: *.prideindustries.com
   Issuer: DigiCert
   Expiry: 2025-06-30

[... more certificates ...]

================================================================================

Select certificate to replace (1-5, or 'q' to quit): 2

✓ Selected: Pride-Wildcard-June-2025

Searching configuration for certificate: Pride-Wildcard-June-2025
✓ Found 4 reference(s) to certificate 'Pride-Wildcard-June-2025':
  SSL/TLS Profiles: pride-ssl-profile
  GlobalProtect Portals: pride-gp-portal
  GlobalProtect Gateways: pride-gp-gateway-1, pride-gp-gateway-2

================================================================================
PHASE 1 SUMMARY
================================================================================

Phase 1 complete! Summary:
  ✓ Configuration backed up: ./backups/amdffw.prideindustries.com-config-20251107_120000.xml
  ✓ Device state backed up: ./backups/amdffw.prideindustries.com-device-state-20251107_120000.tgz
  ✓ Certificate to replace: Pride-Wildcard-June-2025
  ✓ New certificate name: Pride-Wildcard-Test
  ✓ Certificate usage analysis complete

[DRY RUN] Phase 2 would upload new certificate and update configurations

================================================================================
NEXT STEPS
================================================================================
Phase 2 will:
  1. Upload new certificate: Pride-Wildcard-Test
  2. Upload private key from: ./certificates/test.key
  3. Update SSL/TLS profiles
  4. Update GlobalProtect portals and gateways
  5. Commit changes
```

## File Locations

After running, you'll find:

```
pa-firewall-cert-update/
├── backups/
│   ├── amdffw.prideindustries.com-config-20251107_120000.xml  (Configuration)
│   └── amdffw.prideindustries.com-device-state-20251107_120000.tgz  (Device State)
└── logs/
    └── pa-cert-update-20251107_120000.log
```

**Backup Files:**
- **Configuration XML**: Full running configuration for rollback and analysis
- **Device State TGZ**: Comprehensive snapshot including logs and system state (40-100 MB typical)

## Common Issues

### Connection Refused
```
ERROR: Cannot connect to firewall amdffw.prideindustries.com
```
**Solution**: Verify firewall hostname/IP is correct and reachable

### Authentication Failed
```
ERROR: Authentication failed - check API key
```
**Solution**: Regenerate API key using `--show-api-instructions`

### Certificate File Not Found
```
ERROR: Certificate file not found: ./certificates/test.crt
```
**Solution**: Place certificate files in `./certificates/` directory

## Security Notes

- **Never commit API keys** to version control
- **Store backups securely** - they contain full firewall config
- **Use dry-run first** to validate before making changes
- **Review logs** in `./logs/` for detailed audit trail

## Next: Phase 2 Implementation

Phase 2 will add:
- Certificate upload via API
- Private key import
- SSL/TLS profile updates
- Portal/gateway configuration updates

Stay tuned for Phase 2!
