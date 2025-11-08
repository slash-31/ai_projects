# Certificate Files Directory

Place your SSL certificate files here before running the script.

## Required Files

For each certificate update, you'll need:

1. **Public Certificate** (`.crt` or `.pem`)
   - Contains the public certificate
   - Format: PEM-encoded

2. **Private Key** (`.key`)
   - Contains the private key
   - May be encrypted with passphrase
   - Format: PEM-encoded

3. **Certificate Chain** (`.crt` or `-chain.crt`) - OPTIONAL
   - Contains intermediate CA certificates
   - Required for proper SSL/TLS trust chain
   - Format: PEM-encoded

## File Naming Convention

Use descriptive names with date:
```
Pride-Wildcard-January-2026.crt
Pride-Wildcard-January-2026.key
Pride-Wildcard-January-2026-chain.crt
```

## File Format Example

**Certificate File** (`Pride-Wildcard-January-2026.crt`):
```
-----BEGIN CERTIFICATE-----
MIIFXzCCBEegAwIBAgIQBnGvN8...
[certificate data]
...3vF5kZqW/4=
-----END CERTIFICATE-----
```

**Private Key File** (`Pride-Wildcard-January-2026.key`):
```
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQ...
[private key data]
...kWyN5qZw==
-----END PRIVATE KEY-----
```

**Chain File** (`Pride-Wildcard-January-2026-chain.crt`):
```
-----BEGIN CERTIFICATE-----
[Intermediate CA certificate]
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
[Root CA certificate]
-----END CERTIFICATE-----
```

## Security Notes

⚠️ **IMPORTANT**:
- **Never commit certificate files to version control**
- Store private keys encrypted when possible
- Use secure file permissions: `chmod 600 *.key`
- Delete files after successful upload
- Keep backup copies in secure, encrypted storage

## Verification

Before running the script, verify your files:

```bash
# Check certificate validity
openssl x509 -in Pride-Wildcard-January-2026.crt -text -noout

# Check private key
openssl rsa -in Pride-Wildcard-January-2026.key -check

# Verify certificate and key match
openssl x509 -noout -modulus -in Pride-Wildcard-January-2026.crt | openssl md5
openssl rsa -noout -modulus -in Pride-Wildcard-January-2026.key | openssl md5
# ^ These two commands should produce identical MD5 hashes

# Check chain file
openssl crl2pkcs7 -nocrl -certfile Pride-Wildcard-January-2026-chain.crt | \
  openssl pkcs7 -print_certs -text -noout
```

## Encrypted Private Keys

If your private key is encrypted with a passphrase:

```bash
# Test with passphrase
openssl rsa -in Pride-Wildcard-January-2026.key -check

# Use --passphrase argument when running script
python3 ../pa_cert_update.py \
  --firewall fw.example.com \
  --api-key YOUR_KEY \
  --cert-name "Pride-Wildcard-January-2026" \
  --cert-file Pride-Wildcard-January-2026.crt \
  --key-file Pride-Wildcard-January-2026.key \
  --passphrase "your-passphrase-here"
```

## Getting Certificates

Certificates typically come from:
- Certificate Authority (CA) - DigiCert, Let's Encrypt, etc.
- Internal PKI team
- Network/security team

Request format: **PEM** (not DER, PKCS12, or other formats)

## File Protection

This directory is protected by `.gitignore`:
- All `.crt`, `.pem`, `.key`, `.p12`, `.pfx` files are excluded from git
- Certificate files will never be committed to version control
- Safe to place certificates here temporarily for script execution
