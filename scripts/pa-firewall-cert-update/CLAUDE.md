# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This project automates wildcard SSL certificate updates on Palo Alto firewalls using the PAN-OS REST API. It replaces the manual procedure with a Python script that handles configuration backup, certificate upload, SSL/TLS profile updates, and portal/gateway configuration changes.

## Directory Structure

```
pa-firewall-cert-update/
├── pa_cert_update.py           # Main Python automation script
├── requirements.txt            # Python dependencies
├── README.md                   # User documentation
├── CLAUDE.md                   # This file - development guidance
├── docs/                       # Reference documentation
│   └── Palo Alto Firewall_...md # Original manual procedure
├── backups/                    # Config backups (created at runtime)
├── logs/                       # Audit logs (created at runtime)
└── certificates/               # Certificate files (user provides)
```

## Technology Stack

- **Language**: Python 3.8+
- **HTTP Client**: `requests` library for REST API calls
- **XML Parsing**: `lxml` for configuration parsing
- **Logging**: Standard `logging` module with file and console handlers
- **CLI**: `argparse` for command-line interface

## Development Phases

### Phase 1: Configuration Backup & Certificate Discovery (CURRENT FOCUS)
**Objective**: Safely backup firewall and identify certificate to replace

Tasks:
1. Implement REST API authentication with API key
2. Create configuration backup function (`GET /api/?type=export&category=configuration`)
3. Query existing certificates (`GET /api/?type=config&action=get&xpath=/config/shared/certificate`)
4. Present interactive list for user to select certificate to replace
5. Search XML configuration for all references to old certificate name

**Key Files**:
- `pa_cert_update.py` - Main script entry point
- Core functions: `authenticate()`, `backup_config()`, `list_certificates()`, `search_cert_usage()`

**Testing**: Use `--dry-run` flag to validate without making changes

### Phase 2: Certificate Upload & Profile Update
**Objective**: Upload new certificate and update SSL/TLS service profile

Tasks:
1. Upload public certificate (`POST /api/?type=import&category=certificate`)
2. Upload private key (included in certificate import)
3. Upload certificate chain
4. Update SSL/TLS service profile with new certificate name

### Phase 3: Portal & Gateway Configuration Updates
**Objective**: Update all firewall components using old certificate

Tasks:
1. Query all portal configurations
2. Update portal SSL/TLS certificates
3. Query all gateway configurations
4. Update gateway SSL/TLS certificates

### Phase 4: Commit & Validation
**Objective**: Safely commit changes with rollback capability

Tasks:
1. Validate configuration before commit
2. Commit with admin-only scope (`POST /api/?type=commit&cmd=<commit><partial><admin><member>username</member></admin></partial></commit>`)
3. Monitor commit job status
4. Verify changes applied successfully

### Phase 5: Logging & Audit Trail
**Objective**: Comprehensive logging for compliance and troubleshooting

Tasks:
1. Log all API requests/responses
2. Generate change summary report
3. Create audit trail for compliance
4. Optional: Email notification of changes

## PAN-OS REST API Key Endpoints

### Authentication
```python
# API key is passed in every request as header or query parameter
headers = {'X-PAN-KEY': api_key}
# OR
params = {'key': api_key}
```

### Configuration Backup
```
GET /api/?type=export&category=configuration
Response: XML file (running-config.xml)
```

### List Certificates
```
GET /api/?type=config&action=get&xpath=/config/shared/certificate
Response: XML with all certificate entries
```

### Import Certificate
```
POST /api/?type=import&category=certificate
Form data:
  - certificate-name: <name>
  - format: pem
  - file: <certificate file>
  - key: <private key file>
  - passphrase: <optional>
```

### Update SSL/TLS Profile
```
POST /api/?type=config&action=set&xpath=/config/shared/ssl-tls-service-profile/entry[@name='<profile>']
XML body with new certificate reference
```

### Commit Configuration
```
POST /api/?type=commit&cmd=<commit><partial><admin><member>USERNAME</member></admin></partial></commit>
```

### Check Commit Status
```
GET /api/?type=op&cmd=<show><jobs><id>JOB_ID</id></jobs></show>
```

## Original Manual Procedure Reference

The `docs/` directory contains the original manual procedure for reference:

**Target Firewalls**:
- amdffw.prideindustries.com
- amdffw-standby.prideindustries.com
- mcclfw1.prideindustries.com
- mcclfw2.prideindustries.com

**Procedure Sections**:
1. **Backup Configuration** - Export running-config.xml
2. **Certificate Import** - Install new wildcard certificate and private key
3. **Certificate Chain Upload** - Import intermediate/chain certificates
4. **SSL/TLS Profile Update** - Apply new certificate to active profile
5. **Commit Changes** - Safely commit configuration changes

**Certificate Naming Convention**:
- Format: `Pride-Wildcard-{Month-Year}` (e.g., `Pride-Wildcard-June-2025`)
- Chain certificate: `Pride-Wildcard-Chain`

## File Format Notes

The markdown file includes:
- Screenshot images (embedded as Base64-encoded PNG data URIs)
- Step-by-step instructions with visual references
- Firewall-specific configuration paths

## Working with This Directory

### When to Reference This Guide
- **Certificate expiration** - Renewing wildcard SSL certificates
- **New firewall deployment** - Installing certificates on new devices
- **SSL/TLS profile updates** - Changing active certificates
- **Configuration backup** - Exporting firewall running configuration

### Important Operational Considerations

**Certificate Management**:
- Always backup running configuration before changes
- Use consistent naming with month/year for certificate tracking
- Certificate chain files do not include private keys
- PEM format requires separate key file; PKCS12 includes key

**Commit Strategy**:
- Commit only admin's own changes ("Commit Changes Made By (1) Admin")
- Avoid "Commit All Changes" to prevent committing others' pending work
- Monitor commit process for errors

**Security Best Practices**:
- Store backup configurations in secure, encrypted locations
- Keep private keys in secure storage (encrypted if possible)
- Never commit private keys to version control
- Verify certificate validity dates before installation

### Related Infrastructure

This procedure applies to Pride Industries firewall infrastructure. Certificate updates may need coordination with:
- Network team (firewall access)
- Security team (certificate procurement)
- Certificate Authority (renewals)

## File Handling

**Markdown File with Embedded Images**:
The guide contains Base64-encoded PNG images. When viewing or editing:
- Use markdown previewer that supports data URIs
- File size is large (~375KB) due to embedded screenshots
- Do not attempt to extract images to separate files (breaks guide)

## Common Tasks

### Updating the Guide
When firewall procedures change:
1. Update relevant section in markdown file
2. If screenshots change, replace Base64 image data
3. Update certificate naming convention if modified
4. Test procedure on lab firewall before documentation

### Certificate Renewal Process
1. Obtain new wildcard certificate from CA
2. Follow Step 1: Backup current configuration
3. Follow Steps 2-4: Import certificate and chain
4. Follow Step 5: Update SSL/TLS profile
5. Follow Step 6: Commit changes
6. Verify HTTPS access to firewall management interface
7. Document certificate installation in change log

## Development Best Practices

### Code Organization
- **Main script**: `pa_cert_update.py` - Keep under 500 lines
- **Functions**: Single responsibility principle
- **Error handling**: Comprehensive try/except with specific exceptions
- **Logging**: Log all API calls (sanitize sensitive data)

### Security Considerations
1. **Never log API keys** - Sanitize before logging
2. **Never commit certificates** - Add `*.crt`, `*.key`, `*.pem` to `.gitignore`
3. **Validate inputs** - Check file existence, format before API calls
4. **Use HTTPS** - Verify SSL certificates (allow override with warning)
5. **Secure file permissions** - Set restrictive permissions on backup/log files

### Error Handling Patterns
```python
try:
    response = session.get(url, params=params, verify=verify_ssl)
    response.raise_for_status()
except requests.exceptions.ConnectionError:
    logger.error("Cannot connect to firewall - check IP/hostname")
    sys.exit(1)
except requests.exceptions.HTTPError as e:
    logger.error(f"HTTP error: {e.response.status_code}")
    sys.exit(1)
```

### Testing Strategy
1. **Dry-run mode**: Always implement `--dry-run` first
2. **Lab firewall**: Test on non-production first
3. **Incremental**: Build and test one phase at a time
4. **Backup validation**: Always verify backup before proceeding

### Common Pitfalls
- **Certificate name mismatches**: PAN-OS is case-sensitive
- **XPath queries**: Ensure correct XML namespace
- **Commit scope**: Use `<partial>` commits to avoid committing others' changes
- **Job monitoring**: Commit is async - must poll job status

## Common Development Tasks

### Running Phase 1 Tests
```bash
# Dry run with verbose output
python pa_cert_update.py \
  --firewall 192.168.1.1 \
  --api-key "YOUR_KEY" \
  --cert-name "Test-Cert" \
  --cert-file test.crt \
  --key-file test.key \
  --dry-run --verbose
```

### Debugging API Calls
Enable requests debugging:
```python
import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
```

### Manual API Testing
```bash
# Test API key
curl -k "https://FIREWALL/api/?type=keygen&user=USER&password=PASS"

# Export configuration
curl -k -H "X-PAN-KEY: YOUR_KEY" \
  "https://FIREWALL/api/?type=export&category=configuration" \
  -o backup.xml

# List certificates
curl -k -H "X-PAN-KEY: YOUR_KEY" \
  "https://FIREWALL/api/?type=config&action=get&xpath=/config/shared/certificate"
```
