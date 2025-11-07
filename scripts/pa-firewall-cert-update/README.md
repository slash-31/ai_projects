# Palo Alto Firewall Certificate Update Automation

Python script to automate wildcard certificate updates on Palo Alto firewalls using the REST API.

## Overview

This script automates the manual certificate update process documented in `docs/`, eliminating human error and reducing the time required to update certificates across multiple firewalls.

### What This Script Does

1. **Backs up** the current firewall configuration
2. **Queries** the firewall for existing certificates via REST API
3. **Identifies** which certificate is being replaced (interactive prompt)
4. **Searches** the configuration for all uses of the old certificate
5. **Uploads** the new certificate (public key + private key)
6. **Updates** the SSL/TLS service profile with the new certificate
7. **Updates** all portal and gateway configurations using the old certificate
8. **Commits** the changes with safety checks
9. **Logs** all actions for audit trail

## Prerequisites

### Firewall Configuration

**Enable REST API Access:**
1. Log into your Palo Alto firewall web interface
2. Navigate to **Device → Setup → Management**
3. Under **Management Interface Settings**, click **gear icon**
4. Check **Enable HTTP/HTTPS API**
5. Click **OK** and **Commit**

**Generate API Key:**
```bash
# Method 1: Using curl (replace with your firewall details)
curl -k -X GET 'https://<firewall-ip>/api/?type=keygen&user=<username>&password=<password>'

# Method 2: Via web browser
https://<firewall-ip>/api/?type=keygen&user=<username>&password=<password>
```

The response will contain your API key:
```xml
<response status="success">
  <result>
    <key>LUFRPT14MW5xOEo1R09KVlBZNnpnemh0VHRBOWl6TGM9bXcwM3JHUGVhRlNiY0dCR0srNESvT3dDdz09</key>
  </result>
</response>
```

**Save your API key securely** - you'll need it to run the script.

### Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `requests` - REST API communication
- `urllib3` - HTTP client (included with requests)
- `argparse` - Command-line argument parsing
- `logging` - Audit trail and logging

### Certificate Files

Prepare your new certificate files in the script directory:
- `<cert-name>.crt` or `<cert-name>.pem` - Public certificate
- `<cert-name>.key` - Private key
- `<cert-name>-chain.crt` - Certificate chain (intermediate CA)

**Example:**
```
Pride-Wildcard-January-2026.crt
Pride-Wildcard-January-2026.key
Pride-Wildcard-January-2026-chain.crt
```

## Installation

```bash
# Clone or download this script
cd pa-firewall-cert-update

# Install dependencies
pip install -r requirements.txt

# Make script executable (optional)
chmod +x pa_cert_update.py
```

## Usage

### Basic Usage

```bash
python pa_cert_update.py \
  --firewall <firewall-ip-or-hostname> \
  --api-key <your-api-key> \
  --cert-name "Pride-Wildcard-January-2026" \
  --cert-file Pride-Wildcard-January-2026.crt \
  --key-file Pride-Wildcard-January-2026.key \
  --chain-file Pride-Wildcard-January-2026-chain.crt
```

### Command-Line Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--firewall` | Yes | Firewall IP address or hostname |
| `--api-key` | Yes | REST API key (from firewall) |
| `--cert-name` | Yes | Name for the new certificate in firewall |
| `--cert-file` | Yes | Path to public certificate file (.crt or .pem) |
| `--key-file` | Yes | Path to private key file (.key) |
| `--chain-file` | No | Path to certificate chain file |
| `--passphrase` | No | Private key passphrase (if encrypted) |
| `--backup-dir` | No | Directory for config backups (default: ./backups) |
| `--dry-run` | No | Show what would be done without making changes |
| `--verbose` | No | Enable verbose logging output |

### Examples

**Update certificate on single firewall:**
```bash
python pa_cert_update.py \
  --firewall amdffw.prideindustries.com \
  --api-key "LUFRPT14MW5xOEo1R09KVlBZNnpn..." \
  --cert-name "Pride-Wildcard-June-2025" \
  --cert-file Pride-Wildcard-June-2025.crt \
  --key-file Pride-Wildcard-June-2025.key \
  --chain-file Pride-Wildcard-June-2025-chain.crt
```

**Dry run (preview changes without applying):**
```bash
python pa_cert_update.py \
  --firewall mcclfw1.prideindustries.com \
  --api-key "LUFRPT14MW5xOEo1R09KVlBZNnpn..." \
  --cert-name "Pride-Wildcard-June-2025" \
  --cert-file Pride-Wildcard-June-2025.crt \
  --key-file Pride-Wildcard-June-2025.key \
  --dry-run
```

**With encrypted private key:**
```bash
python pa_cert_update.py \
  --firewall amdffw.prideindustries.com \
  --api-key "LUFRPT14MW5xOEo1R09KVlBZNnpn..." \
  --cert-name "Pride-Wildcard-June-2025" \
  --cert-file Pride-Wildcard-June-2025.crt \
  --key-file Pride-Wildcard-June-2025.key \
  --passphrase "your-key-passphrase"
```

## Development Phases

### Phase 1: Configuration Backup & Certificate Discovery (Current)
- ✓ REST API authentication
- ✓ Configuration backup to local file
- ✓ Query and list existing certificates
- ✓ Interactive selection of certificate to replace
- ✓ Search configuration for certificate usage

### Phase 2: Certificate Upload & Profile Update
- Upload new certificate and private key
- Upload certificate chain
- Update SSL/TLS service profile

### Phase 3: Portal & Gateway Configuration Updates
- Identify all portals using old certificate
- Update portal configurations with new certificate
- Identify all gateways using old certificate
- Update gateway configurations with new certificate

### Phase 4: Commit & Validation
- Pre-commit validation checks
- Commit changes with admin-only scope
- Post-commit verification
- Error handling and rollback capability

### Phase 5: Logging & Audit Trail
- Comprehensive logging of all actions
- Audit trail for compliance
- Change summary report
- Email notification (optional)

## Output

The script generates:

1. **Configuration Backup**: `./backups/<firewall>-<timestamp>.xml`
2. **Certificate Usage Report**: Lists all locations using old certificate
3. **Change Summary**: Details all modifications made
4. **Audit Log**: `./logs/pa-cert-update-<timestamp>.log`

## Safety Features

- **Pre-flight checks**: Validates certificate files before upload
- **Configuration backup**: Always backs up before changes
- **Dry-run mode**: Preview changes without applying
- **Targeted commits**: Only commits admin's changes (not other admins' pending work)
- **Rollback capability**: Can restore from backup if needed
- **Audit logging**: Full trail of all API calls and changes

## Security Considerations

### API Key Security
- **Never commit API keys to version control**
- Store API key in environment variable or secure vault
- Use key with minimum required privileges
- Rotate API keys regularly

### Certificate File Security
- Keep private keys encrypted at rest
- Use secure file permissions (chmod 600)
- Delete private key files after upload
- Never commit private keys to version control

### Network Security
- Use HTTPS for all API calls
- Validate firewall SSL certificates (or use `-k` flag cautiously)
- Run script from secure network (management VLAN)

## Troubleshooting

### Common Issues

**API Authentication Failed**
```
Error: 403 Forbidden - Invalid API key
```
Solution: Regenerate API key from firewall and verify it's correct

**Certificate Upload Failed**
```
Error: Invalid certificate format
```
Solution: Verify certificate is in PEM format and not corrupted

**Commit Failed**
```
Error: Configuration validation failed
```
Solution: Check audit log for validation errors, restore from backup if needed

### Debug Mode

Enable verbose logging for troubleshooting:
```bash
python pa_cert_update.py --verbose [other arguments]
```

## Target Firewalls

This script is designed for Pride Industries Palo Alto firewalls:
- amdffw.prideindustries.com
- amdffw-standby.prideindustries.com
- mcclfw1.prideindustries.com
- mcclfw2.prideindustries.com

## Project Structure

```
pa-firewall-cert-update/
├── README.md                    # This file
├── CLAUDE.md                    # Claude Code guidance
├── pa_cert_update.py            # Main script (to be created)
├── requirements.txt             # Python dependencies
├── docs/                        # Documentation
│   └── Palo Alto Firewall_...md # Manual procedure guide
├── backups/                     # Configuration backups (created by script)
├── logs/                        # Audit logs (created by script)
└── certificates/                # Certificate files (user provides)
```

## Contributing

When modifying this script:
1. Test on lab/non-production firewall first
2. Use `--dry-run` mode extensively
3. Verify backup and rollback functionality
4. Update this README with any new features
5. Add comprehensive error handling
6. Log all API interactions

## References

- [Palo Alto REST API Documentation](https://docs.paloaltonetworks.com/pan-os/10-1/pan-os-panorama-api)
- Manual procedure guide: `docs/Palo Alto Firewall_ Backup & Wildcard Certificate Installation Guide.md`

## License

Internal use only - Pride Industries

## Support

For issues or questions:
- Review audit logs in `./logs/`
- Check firewall commit logs
- Restore from backup if needed: `./backups/`
- Contact network team for firewall access issues
