#!/usr/bin/env python3
"""
Palo Alto Firewall Certificate Update Automation

This script automates the process of updating SSL certificates on Palo Alto firewalls
using the PAN-OS XML API. It handles configuration backup, certificate upload, and
updates to SSL/TLS profiles, portals, and gateways.

Usage:
    python pa_cert_update.py --firewall FIREWALL --api-key KEY --cert-name NAME \\
                              --cert-file FILE --key-file FILE [options]

Phase 1 Implementation (Current):
    - Full firewall backup (configuration + device state)
    - Certificate listing and selection
    - Configuration search for certificate usage
"""

import argparse
import sys
import os
import logging
import traceback
import urllib3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

try:
    import requests
    from lxml import etree
except ImportError as e:
    print(f"ERROR: Missing required package: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
API_ENDPOINT = "/api/"
DEFAULT_BACKUP_DIR = "./backups"
DEFAULT_LOG_DIR = "./logs"

# Configure logging
logger = logging.getLogger(__name__)


class PAFirewallClient:
    """Client for interacting with Palo Alto Firewall XML API."""

    def __init__(self, firewall: str, api_key: str, verify_ssl: bool = False):
        """
        Initialize firewall client.

        Args:
            firewall: Firewall hostname or IP address
            api_key: PAN-OS API key
            verify_ssl: Whether to verify SSL certificates (default: False)
        """
        self.firewall = firewall
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.base_url = f"https://{firewall}{API_ENDPOINT}"
        self.session = requests.Session()

        # Sanitize API key for logging (show only first/last 4 chars)
        self.api_key_display = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"

        logger.info(f"Initialized client for firewall: {firewall}")
        logger.debug(f"API key: {self.api_key_display}")

    def _api_call(self, params: Dict, method: str = 'GET', files: Dict = None) -> requests.Response:
        """
        Make API call to firewall.

        Args:
            params: Query parameters for API call
            method: HTTP method (GET or POST)
            files: Files to upload (for POST requests)

        Returns:
            Response object

        Raises:
            requests.exceptions.RequestException: On connection or HTTP errors
        """
        # Add API key to params
        params['key'] = self.api_key

        # Log API call (sanitize sensitive data)
        log_params = params.copy()
        log_params['key'] = self.api_key_display
        logger.debug(f"API call: {method} {self.base_url} params={log_params}")

        try:
            if method == 'GET':
                response = self.session.get(
                    self.base_url,
                    params=params,
                    verify=self.verify_ssl,
                    timeout=30
                )
            elif method == 'POST':
                response = self.session.post(
                    self.base_url,
                    params=params,
                    files=files,
                    verify=self.verify_ssl,
                    timeout=30
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            logger.debug(f"API response: {response.status_code}")

            return response

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to firewall {self.firewall}")
            logger.error(f"Error: {e}")
            raise
        except requests.exceptions.Timeout:
            logger.error(f"Timeout connecting to firewall {self.firewall}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error from firewall: {e.response.status_code}")
            logger.error(f"Response: {e.response.text[:200]}")
            raise

    def test_connection(self) -> bool:
        """
        Test API connection and authentication.

        Returns:
            True if connection successful, False otherwise
        """
        logger.info("Testing API connection and authentication...")

        try:
            params = {
                'type': 'op',
                'cmd': '<show><system><info></info></system></show>'
            }
            response = self._api_call(params)

            # Parse XML response
            root = etree.fromstring(response.content)
            status = root.get('status')

            if status == 'success':
                # Extract hostname and version
                hostname = root.findtext('.//hostname', default='unknown')
                sw_version = root.findtext('.//sw-version', default='unknown')
                model = root.findtext('.//model', default='unknown')

                logger.info(f"✓ Connection successful!")
                logger.info(f"  Hostname: {hostname}")
                logger.info(f"  Model: {model}")
                logger.info(f"  PAN-OS Version: {sw_version}")
                return True
            else:
                logger.error("✗ Authentication failed - check API key")
                return False

        except Exception as e:
            logger.error(f"✗ Connection test failed: {e}")
            return False

    def backup_configuration(self, backup_dir: str, timestamp: str = None) -> Optional[str]:
        """
        Backup firewall configuration to XML file.

        Args:
            backup_dir: Directory to save backup file
            timestamp: Optional timestamp string (generated if not provided)

        Returns:
            Path to backup file, or None on failure
        """
        logger.info("Backing up firewall configuration...")

        # Create backup directory if it doesn't exist
        Path(backup_dir).mkdir(parents=True, exist_ok=True)

        # Generate timestamp if not provided
        if not timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        backup_file = Path(backup_dir) / f"{self.firewall}-config-{timestamp}.xml"

        try:
            params = {
                'type': 'export',
                'category': 'configuration'
            }
            response = self._api_call(params)

            # Save configuration to file
            with open(backup_file, 'wb') as f:
                f.write(response.content)

            # Get file size for logging
            file_size = backup_file.stat().st_size
            logger.info(f"✓ Configuration backed up successfully")
            logger.info(f"  File: {backup_file}")
            logger.info(f"  Size: {file_size:,} bytes")

            return str(backup_file)

        except Exception as e:
            logger.error(f"✗ Configuration backup failed: {e}")
            return None

    def backup_device_state(self, backup_dir: str, timestamp: str = None) -> Optional[str]:
        """
        Backup complete device state (more comprehensive than config only).
        Device state includes running config, logs, and system state information.

        Args:
            backup_dir: Directory to save backup file
            timestamp: Optional timestamp string (generated if not provided)

        Returns:
            Path to backup file, or None on failure
        """
        logger.info("Backing up device state (this may take a few minutes)...")

        # Create backup directory if it doesn't exist
        Path(backup_dir).mkdir(parents=True, exist_ok=True)

        # Generate timestamp if not provided
        if not timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        backup_file = Path(backup_dir) / f"{self.firewall}-device-state-{timestamp}.tgz"

        try:
            params = {
                'type': 'export',
                'category': 'device-state'
            }
            # Device state export can take longer - increase timeout
            response = self.session.get(
                self.base_url,
                params={**params, 'key': self.api_key},
                verify=self.verify_ssl,
                timeout=300  # 5 minutes
            )
            response.raise_for_status()

            # Save device state to file
            with open(backup_file, 'wb') as f:
                f.write(response.content)

            # Get file size for logging
            file_size = backup_file.stat().st_size
            logger.info(f"✓ Device state backed up successfully")
            logger.info(f"  File: {backup_file}")
            logger.info(f"  Size: {file_size:,} bytes ({file_size / (1024*1024):.1f} MB)")

            return str(backup_file)

        except requests.exceptions.Timeout:
            logger.error(f"✗ Device state backup timed out (firewall may be busy)")
            return None
        except Exception as e:
            logger.error(f"✗ Device state backup failed: {e}")
            return None

    def full_backup(self, backup_dir: str) -> Dict[str, Optional[str]]:
        """
        Perform comprehensive backup of both configuration and device state.

        Args:
            backup_dir: Directory to save backup files

        Returns:
            Dictionary with paths to backup files {'config': path, 'device_state': path}
        """
        logger.info("\n" + "="*80)
        logger.info("FULL FIREWALL BACKUP")
        logger.info("="*80)

        # Use same timestamp for both backups
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        backups = {
            'config': None,
            'device_state': None
        }

        # Backup configuration
        config_backup = self.backup_configuration(backup_dir, timestamp)
        if config_backup:
            backups['config'] = config_backup
        else:
            logger.warning("Configuration backup failed - proceeding with caution")

        # Backup device state
        logger.info("")  # Blank line for readability
        device_state_backup = self.backup_device_state(backup_dir, timestamp)
        if device_state_backup:
            backups['device_state'] = device_state_backup
        else:
            logger.warning("Device state backup failed - config backup still available")

        # Summary
        logger.info("\n" + "-"*80)
        logger.info("BACKUP SUMMARY")
        logger.info("-"*80)
        if backups['config']:
            logger.info(f"✓ Configuration: {backups['config']}")
        else:
            logger.error(f"✗ Configuration: FAILED")

        if backups['device_state']:
            logger.info(f"✓ Device State: {backups['device_state']}")
        else:
            logger.warning(f"⚠ Device State: FAILED (non-critical)")

        logger.info("="*80 + "\n")

        return backups

    def list_certificates(self) -> List[Dict[str, str]]:
        """
        Retrieve list of certificates from firewall.

        Returns:
            List of dictionaries containing certificate info
        """
        logger.info("Retrieving certificate list from firewall...")

        try:
            params = {
                'type': 'config',
                'action': 'get',
                'xpath': '/config/shared/certificate'
            }
            response = self._api_call(params)

            # Parse XML response
            root = etree.fromstring(response.content)
            status = root.get('status')

            if status != 'success':
                logger.error("Failed to retrieve certificates")
                return []

            # Extract certificate entries
            certificates = []
            cert_entries = root.xpath('.//entry')

            for entry in cert_entries:
                cert_name = entry.get('name')

                # Extract additional info if available
                common_name = entry.findtext('.//common-name', default='N/A')
                issuer = entry.findtext('.//issuer', default='N/A')
                not_valid_after = entry.findtext('.//not-valid-after', default='N/A')

                certificates.append({
                    'name': cert_name,
                    'common_name': common_name,
                    'issuer': issuer,
                    'expiry': not_valid_after
                })

            logger.info(f"✓ Found {len(certificates)} certificate(s)")
            return certificates

        except Exception as e:
            logger.error(f"✗ Failed to retrieve certificates: {e}")
            return []

    def search_certificate_usage(self, config_file: str, cert_name: str) -> Dict[str, List[str]]:
        """
        Search configuration for all references to a certificate.

        Args:
            config_file: Path to configuration XML file
            cert_name: Name of certificate to search for

        Returns:
            Dictionary with usage locations
        """
        logger.info("\n" + "="*80)
        logger.info("CERTIFICATE USAGE ANALYSIS")
        logger.info("="*80)
        logger.info(f"Searching for: {cert_name}")
        logger.info(f"Config file: {config_file}")
        logger.info("")

        usage = {
            'ssl_tls_profiles': [],
            'portals': [],
            'gateways': [],
            'other': []
        }

        try:
            # Parse configuration XML
            tree = etree.parse(config_file)
            root = tree.getroot()

            # Search for SSL/TLS service profiles
            ssl_profiles = root.xpath(f"//ssl-tls-service-profile/entry[certificate='{cert_name}']/@name")
            usage['ssl_tls_profiles'] = list(ssl_profiles)

            # Search for GlobalProtect portals
            portals = root.xpath(f"//global-protect/global-protect-portal/entry[ssl-tls-service-profile='{cert_name}' or .//certificate='{cert_name}']/@name")
            usage['portals'] = list(portals)

            # Search for GlobalProtect gateways
            gateways = root.xpath(f"//global-protect/global-protect-gateway/entry[ssl-tls-service-profile='{cert_name}' or .//certificate='{cert_name}']/@name")
            usage['gateways'] = list(gateways)

            # Search for management interface usage
            mgmt_refs = root.xpath(f"//management/entry[.//certificate='{cert_name}']/@name")
            if mgmt_refs:
                usage['other'].extend([f"Management Interface: {ref}" for ref in mgmt_refs])

            # Search for other references (generic search)
            # This catches any other XML elements containing the cert name
            other_refs = root.xpath(f"//*[text()='{cert_name}' and not(ancestor::certificate)]")
            for ref in other_refs:
                xpath = tree.getpath(ref)
                # Filter out already found items
                if not any(pattern in xpath for pattern in ['ssl-tls-service-profile', 'global-protect-portal', 'global-protect-gateway', 'management']):
                    # Simplify XPath for readability
                    simplified_xpath = xpath.split('/')[-3:] if len(xpath.split('/')) > 3 else xpath
                    usage['other'].append('/'.join(simplified_xpath))

            # Calculate totals
            total_refs = sum(len(v) for v in usage.values())

            # Display results in formatted table
            logger.info("-"*80)
            logger.info("SEARCH RESULTS")
            logger.info("-"*80)

            if usage['ssl_tls_profiles']:
                logger.info("\n📋 SSL/TLS Service Profiles:")
                for i, profile in enumerate(usage['ssl_tls_profiles'], 1):
                    logger.info(f"   {i}. {profile}")
            else:
                logger.info("\n📋 SSL/TLS Service Profiles: (none found)")

            if usage['portals']:
                logger.info("\n🔐 GlobalProtect Portals:")
                for i, portal in enumerate(usage['portals'], 1):
                    logger.info(f"   {i}. {portal}")
            else:
                logger.info("\n🔐 GlobalProtect Portals: (none found)")

            if usage['gateways']:
                logger.info("\n🚪 GlobalProtect Gateways:")
                for i, gateway in enumerate(usage['gateways'], 1):
                    logger.info(f"   {i}. {gateway}")
            else:
                logger.info("\n🚪 GlobalProtect Gateways: (none found)")

            if usage['other']:
                logger.info(f"\n🔍 Other References ({len(usage['other'])}):")
                for i, ref in enumerate(usage['other'][:10], 1):  # Show first 10
                    logger.info(f"   {i}. {ref}")
                if len(usage['other']) > 10:
                    logger.info(f"   ... and {len(usage['other']) - 10} more")

            logger.info("\n" + "-"*80)
            if total_refs == 0:
                logger.warning("⚠️  NO REFERENCES FOUND")
                logger.warning("   Certificate may not be in active use, or search patterns need adjustment")
            else:
                logger.info(f"✓ TOTAL: {total_refs} reference(s) found")
                logger.info("   These locations will need to be updated with the new certificate")

            logger.info("="*80 + "\n")

            return usage

        except Exception as e:
            logger.error(f"✗ Failed to search configuration: {e}")
            logger.error("="*80 + "\n")
            return usage

    def upload_certificate(self, cert_name: str, cert_file: str, key_file: str,
                          passphrase: Optional[str] = None) -> bool:
        """
        Upload certificate and private key to firewall.

        Args:
            cert_name: Name for the certificate on firewall
            cert_file: Path to certificate file
            key_file: Path to private key file
            passphrase: Optional passphrase for encrypted private key

        Returns:
            True if upload successful, False otherwise
        """
        logger.info(f"Uploading certificate: {cert_name}")
        logger.info(f"  Certificate file: {Path(cert_file).name}")
        logger.info(f"  Private key file: {Path(key_file).name}")

        try:
            # Prepare multipart form data
            # IMPORTANT: Use 'keypair' category (not 'certificate') to include private key
            params = {
                'type': 'import',
                'category': 'keypair',
                'certificate-name': cert_name,
                'format': 'pem'
            }

            if passphrase:
                params['passphrase'] = passphrase
                logger.info(f"  Using encrypted private key")

            # Read certificate and key files
            with open(cert_file, 'rb') as cf:
                cert_content = cf.read()

            with open(key_file, 'rb') as kf:
                key_content = kf.read()

            # Combine certificate and private key into single PEM file
            # PAN-OS expects: certificate + private key in one file for keypair import
            combined_pem = cert_content + b'\n' + key_content

            logger.debug(f"   Certificate size: {len(cert_content)} bytes")
            logger.debug(f"   Private key size: {len(key_content)} bytes")
            logger.debug(f"   Combined PEM size: {len(combined_pem)} bytes")

            # Upload as single file
            files = {
                'file': ('certificate.pem', combined_pem, 'application/x-pem-file')
            }

            # Make API call with POST and files
            response = self._api_call(params, method='POST', files=files)

            # Parse response
            root = etree.fromstring(response.content)
            status = root.get('status')

            if status == 'success':
                logger.info(f"✓ Certificate and private key uploaded successfully")
                return True
            else:
                error_msg = root.findtext('.//msg', default='Unknown error')
                error_line = root.findtext('.//line', default='')
                logger.error(f"✗ Certificate upload failed: {error_msg}")
                if error_line:
                    logger.error(f"   Details: {error_line}")
                logger.debug(f"   Response: {etree.tostring(root, encoding='unicode')}")
                return False

        except Exception as e:
            logger.error(f"✗ Certificate upload failed: {e}")
            logger.debug(f"   Certificate file: {cert_file}")
            logger.debug(f"   Key file: {key_file}")
            logger.debug(traceback.format_exc())
            return False

    def verify_certificate_exists(self, cert_name: str, max_retries: int = 3, delay: int = 2) -> bool:
        """
        Verify that a certificate exists in the firewall configuration.

        Args:
            cert_name: Name of certificate to verify
            max_retries: Maximum number of retry attempts
            delay: Delay in seconds between retries

        Returns:
            True if certificate exists, False otherwise
        """
        import time

        logger.debug(f"Verifying certificate exists: {cert_name}")

        for attempt in range(1, max_retries + 1):
            try:
                # Query for the certificate in shared config
                xpath = f"/config/shared/certificate/entry[@name='{cert_name}']"
                params = {
                    'type': 'config',
                    'action': 'get',
                    'xpath': xpath
                }

                response = self._api_call(params)
                root = etree.fromstring(response.content)
                status = root.get('status')

                if status == 'success':
                    # Check if result contains the certificate entry
                    result = root.find('.//entry')
                    if result is not None and result.get('name') == cert_name:
                        logger.debug(f"✓ Certificate verified in configuration (attempt {attempt}/{max_retries})")
                        return True

                if attempt < max_retries:
                    logger.debug(f"Certificate not yet visible, waiting {delay}s... (attempt {attempt}/{max_retries})")
                    time.sleep(delay)
                else:
                    logger.warning(f"Certificate '{cert_name}' not found in configuration after {max_retries} attempts")
                    return False

            except Exception as e:
                logger.debug(f"Error verifying certificate (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    time.sleep(delay)
                else:
                    return False

        return False

    def upload_certificate_chain(self, chain_name: str, chain_file: str) -> bool:
        """
        Upload certificate chain to firewall.

        Args:
            chain_name: Name for the certificate chain on firewall
            chain_file: Path to certificate chain file

        Returns:
            True if upload successful, False otherwise
        """
        logger.info(f"Uploading certificate chain: {chain_name}")
        logger.info(f"  Chain file: {Path(chain_file).name}")

        try:
            # Prepare parameters
            params = {
                'type': 'import',
                'category': 'certificate',
                'certificate-name': chain_name,
                'format': 'pem'
            }

            # Read chain file into memory
            with open(chain_file, 'rb') as cf:
                chain_content = cf.read()

            # Prepare files dict with content in memory
            files = {
                'file': ('chain.pem', chain_content, 'application/x-pem-file')
            }

            # Make API call
            response = self._api_call(params, method='POST', files=files)

            # Parse response
            root = etree.fromstring(response.content)
            status = root.get('status')

            if status == 'success':
                logger.info(f"✓ Certificate chain uploaded successfully")
                return True
            else:
                error_msg = root.findtext('.//msg', default='Unknown error')
                logger.error(f"✗ Certificate chain upload failed: {error_msg}")
                return False

        except Exception as e:
            logger.error(f"✗ Certificate chain upload failed: {e}")
            return False

    def update_ssl_tls_profile(self, profile_name: str, new_cert_name: str) -> bool:
        """
        Update SSL/TLS service profile to use new certificate.

        Args:
            profile_name: Name of SSL/TLS profile to update
            new_cert_name: Name of new certificate to use

        Returns:
            True if update successful, False otherwise
        """
        logger.info(f"Updating SSL/TLS profile: {profile_name}")
        logger.info(f"  New certificate: {new_cert_name}")

        try:
            # XPath to the SSL/TLS profile
            xpath = f"/config/shared/ssl-tls-service-profile/entry[@name='{profile_name}']"

            # XML element to update certificate
            element = f"<certificate>{new_cert_name}</certificate>"

            params = {
                'type': 'config',
                'action': 'set',
                'xpath': xpath,
                'element': element
            }

            response = self._api_call(params)

            # Parse response
            root = etree.fromstring(response.content)
            status = root.get('status')

            if status == 'success':
                logger.info(f"✓ SSL/TLS profile updated successfully")
                return True
            else:
                # Extract detailed error information
                error_msg = root.findtext('.//msg', default='Unknown error')
                error_line = root.findtext('.//line', default='')
                error_details = root.findtext('.//details/line', default='')

                # Log the full response for debugging
                logger.debug(f"API Response Status: {status}")
                logger.debug(f"Full API Response:\n{response.content.decode('utf-8')}")

                logger.error(f"✗ SSL/TLS profile update failed: {error_msg}")
                if error_line:
                    logger.error(f"   Error line: {error_line}")
                if error_details:
                    logger.error(f"   Details: {error_details}")
                return False

        except Exception as e:
            logger.error(f"✗ SSL/TLS profile update failed: {e}")
            logger.debug(traceback.format_exc())
            return False

    def update_portal_certificate(self, portal_name: str, new_cert_name: str) -> bool:
        """
        Update GlobalProtect portal to use new certificate.

        Args:
            portal_name: Name of GlobalProtect portal to update
            new_cert_name: Name of new certificate to use

        Returns:
            True if update successful, False otherwise
        """
        logger.info(f"Updating GlobalProtect portal: {portal_name}")
        logger.info(f"  New certificate: {new_cert_name}")

        try:
            # XPath to the GlobalProtect portal
            xpath = f"/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/global-protect/global-protect-portal/entry[@name='{portal_name}']"

            # XML element to update certificate
            element = f"<certificate>{new_cert_name}</certificate>"

            params = {
                'type': 'config',
                'action': 'set',
                'xpath': xpath,
                'element': element
            }

            response = self._api_call(params)

            # Parse response
            root = etree.fromstring(response.content)
            status = root.get('status')

            if status == 'success':
                logger.info(f"✓ GlobalProtect portal updated successfully")
                return True
            else:
                # Extract detailed error information
                error_msg = root.findtext('.//msg', default='Unknown error')
                error_line = root.findtext('.//line', default='')
                error_details = root.findtext('.//details/line', default='')

                logger.debug(f"API Response Status: {status}")
                logger.debug(f"Full API Response:\n{response.content.decode('utf-8')}")

                logger.error(f"✗ GlobalProtect portal update failed: {error_msg}")
                if error_line:
                    logger.error(f"   Error line: {error_line}")
                if error_details:
                    logger.error(f"   Details: {error_details}")
                return False

        except Exception as e:
            logger.error(f"✗ GlobalProtect portal update failed: {e}")
            logger.debug(traceback.format_exc())
            return False

    def update_gateway_certificate(self, gateway_name: str, new_cert_name: str) -> bool:
        """
        Update GlobalProtect gateway to use new certificate.

        Args:
            gateway_name: Name of GlobalProtect gateway to update
            new_cert_name: Name of new certificate to use

        Returns:
            True if update successful, False otherwise
        """
        logger.info(f"Updating GlobalProtect gateway: {gateway_name}")
        logger.info(f"  New certificate: {new_cert_name}")

        try:
            # XPath to the GlobalProtect gateway
            xpath = f"/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/global-protect/global-protect-gateway/entry[@name='{gateway_name}']"

            # XML element to update certificate
            element = f"<certificate>{new_cert_name}</certificate>"

            params = {
                'type': 'config',
                'action': 'set',
                'xpath': xpath,
                'element': element
            }

            response = self._api_call(params)

            # Parse response
            root = etree.fromstring(response.content)
            status = root.get('status')

            if status == 'success':
                logger.info(f"✓ GlobalProtect gateway updated successfully")
                return True
            else:
                # Extract detailed error information
                error_msg = root.findtext('.//msg', default='Unknown error')
                error_line = root.findtext('.//line', default='')
                error_details = root.findtext('.//details/line', default='')

                logger.debug(f"API Response Status: {status}")
                logger.debug(f"Full API Response:\n{response.content.decode('utf-8')}")

                logger.error(f"✗ GlobalProtect gateway update failed: {error_msg}")
                if error_line:
                    logger.error(f"   Error line: {error_line}")
                if error_details:
                    logger.error(f"   Details: {error_details}")
                return False

        except Exception as e:
            logger.error(f"✗ GlobalProtect gateway update failed: {e}")
            logger.debug(traceback.format_exc())
            return False


def select_certificate_to_replace(certificates: List[Dict[str, str]]) -> Optional[str]:
    """
    Interactive prompt for user to select certificate to replace.

    Args:
        certificates: List of certificate dictionaries

    Returns:
        Name of selected certificate, or None if cancelled
    """
    if not certificates:
        logger.error("No certificates available to select")
        return None

    print("\n" + "="*80)
    print("CERTIFICATES ON FIREWALL")
    print("="*80)

    for idx, cert in enumerate(certificates, 1):
        print(f"\n{idx}. {cert['name']}")
        print(f"   Common Name: {cert['common_name']}")
        print(f"   Issuer: {cert['issuer']}")
        print(f"   Expiry: {cert['expiry']}")

    print("\n" + "="*80)

    while True:
        try:
            choice = input(f"\nSelect certificate to replace (1-{len(certificates)}, or 'q' to quit): ").strip()

            if choice.lower() == 'q':
                logger.info("Certificate selection cancelled by user")
                return None

            choice_num = int(choice)
            if 1 <= choice_num <= len(certificates):
                selected_cert = certificates[choice_num - 1]['name']
                print(f"\n✓ Selected: {selected_cert}")
                return selected_cert
            else:
                print(f"Please enter a number between 1 and {len(certificates)}")

        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user")
            return None


def setup_logging(verbose: bool = False, log_dir: str = DEFAULT_LOG_DIR):
    """
    Setup logging configuration.

    Args:
        verbose: Enable verbose (DEBUG) logging
        log_dir: Directory for log files
    """
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Generate log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = Path(log_dir) / f"pa-cert-update-{timestamp}.log"

    # Set log level
    log_level = logging.DEBUG if verbose else logging.INFO

    # Configure logging format
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Setup handlers
    handlers = [
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )

    logger.info("="*80)
    logger.info("Palo Alto Firewall Certificate Update - Phase 1")
    logger.info("="*80)
    logger.info(f"Log file: {log_file}")


def display_api_key_instructions():
    """Display instructions for obtaining API key from firewall."""
    print("\n" + "="*80)
    print("HOW TO GET YOUR API KEY")
    print("="*80)
    print("""
To obtain your PAN-OS API key, use one of these methods:

METHOD 1: Using curl
--------------------
curl -k -X GET 'https://<FIREWALL>/api/?type=keygen&user=<USERNAME>&password=<PASSWORD>'

METHOD 2: Using web browser
---------------------------
https://<FIREWALL>/api/?type=keygen&user=<USERNAME>&password=<PASSWORD>

The response will contain your API key in XML format:
    <response status="success">
      <result>
        <key>LUFRPT14MW5xOEo1R09KVlBZNnpnemh0VHRBOWl6TGM9...</key>
      </result>
    </response>

Copy the key value and use it with the --api-key argument.

IMPORTANT: Store your API key securely and never commit it to version control!
""")
    print("="*80 + "\n")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Automate SSL certificate updates on Palo Alto firewalls',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Phase 1: Backup and discover certificate usage
  %(prog)s --firewall fw.example.com --api-key YOUR_KEY \\
           --cert-name "New-Cert-2026" --cert-file cert.crt --key-file cert.key

  # Dry run mode
  %(prog)s --firewall fw.example.com --api-key YOUR_KEY \\
           --cert-name "New-Cert-2026" --cert-file cert.crt --key-file cert.key --dry-run

  # Show API key instructions
  %(prog)s --show-api-instructions
        """
    )

    parser.add_argument(
        '--firewall',
        required='--show-api-instructions' not in sys.argv,
        help='Firewall hostname or IP address'
    )

    parser.add_argument(
        '--api-key',
        required='--show-api-instructions' not in sys.argv,
        help='PAN-OS API key (use --show-api-instructions for help)'
    )

    parser.add_argument(
        '--cert-name',
        required='--show-api-instructions' not in sys.argv,
        help='Name for new certificate on firewall'
    )

    parser.add_argument(
        '--cert-file',
        required='--show-api-instructions' not in sys.argv,
        help='Path to public certificate file (.crt or .pem)'
    )

    parser.add_argument(
        '--key-file',
        required='--show-api-instructions' not in sys.argv,
        help='Path to private key file (.key)'
    )

    parser.add_argument(
        '--chain-file',
        help='Path to certificate chain file (optional)'
    )

    parser.add_argument(
        '--passphrase',
        help='Private key passphrase (if encrypted)'
    )

    parser.add_argument(
        '--backup-dir',
        default=DEFAULT_BACKUP_DIR,
        help=f'Directory for configuration backups (default: {DEFAULT_BACKUP_DIR})'
    )

    parser.add_argument(
        '--log-dir',
        default=DEFAULT_LOG_DIR,
        help=f'Directory for log files (default: {DEFAULT_LOG_DIR})'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--show-api-instructions',
        action='store_true',
        help='Display instructions for obtaining API key'
    )

    # Note: SSL verification is always disabled for firewall connections
    # since firewalls typically use self-signed certificates

    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()

    # Handle --show-api-instructions
    if args.show_api_instructions:
        display_api_key_instructions()
        sys.exit(0)

    # Setup logging
    setup_logging(args.verbose, args.log_dir)

    # Display execution parameters
    logger.info("\n" + "="*80)
    logger.info("EXECUTION PARAMETERS")
    logger.info("="*80)
    logger.info(f"Target Firewall: {args.firewall}")
    logger.info(f"Backup Directory: {args.backup_dir}")
    logger.info(f"Log Directory: {args.log_dir}")
    logger.info("")
    logger.info("Certificate Details:")
    logger.info(f"  • Current (to replace): <will be selected interactively>")
    logger.info(f"  • New certificate name: {args.cert_name}")
    logger.info(f"  • Certificate file: {args.cert_file}")
    logger.info(f"  • Private key file: {args.key_file}")
    if args.chain_file:
        logger.info(f"  • Chain file: {args.chain_file}")
    if args.passphrase:
        logger.info(f"  • Passphrase: <provided>")
    logger.info("")
    if args.dry_run:
        logger.warning("🔍 DRY RUN MODE - No changes will be made to firewall")
    else:
        logger.info("⚡ LIVE MODE - Changes will be applied to firewall")
    logger.info("="*80 + "\n")

    # Validate certificate files exist
    logger.info("📂 Validating certificate files...")
    for file_path, file_type in [(args.cert_file, 'Certificate'), (args.key_file, 'Key')]:
        if not os.path.exists(file_path):
            logger.error(f"{file_type} file not found: {file_path}")
            sys.exit(1)
        logger.info(f"   ✓ {file_type} file found: {Path(file_path).name}")

    if args.chain_file:
        if not os.path.exists(args.chain_file):
            logger.error(f"Chain file not found: {args.chain_file}")
            sys.exit(1)
        logger.info(f"   ✓ Chain file found: {Path(args.chain_file).name}")
    logger.info("")

    # Initialize firewall client
    # Note: SSL verification is disabled by default since firewalls typically use self-signed certs
    verify_ssl = False  # Always disable SSL verification for firewall management
    client = PAFirewallClient(args.firewall, args.api_key, verify_ssl)

    # PHASE 1: Backup and Discovery
    logger.info("="*80)
    logger.info("PHASE 1: BACKUP AND CERTIFICATE DISCOVERY")
    logger.info("="*80 + "\n")

    # Step 1: Test connection
    logger.info("📡 Step 1/5: Testing firewall connection...")
    if not client.test_connection():
        logger.error("Failed to connect to firewall - exiting")
        sys.exit(1)
    logger.info("")

    # Step 2: Perform full backup (configuration + device state)
    logger.info("💾 Step 2/5: Performing full firewall backup...")
    backups = client.full_backup(args.backup_dir)
    if not backups['config']:
        logger.error("Failed to backup configuration - exiting for safety")
        logger.error("Cannot proceed without configuration backup!")
        sys.exit(1)

    # Use config backup for certificate usage analysis
    config_backup = backups['config']

    # Step 3: List certificates
    logger.info("📜 Step 3/5: Retrieving certificate list...")
    certificates = client.list_certificates()
    if not certificates:
        logger.error("No certificates found on firewall")
        sys.exit(1)
    logger.info("")

    # Step 4: Interactive certificate selection
    logger.info("🎯 Step 4/5: Select certificate to replace...")
    old_cert_name = select_certificate_to_replace(certificates)
    if not old_cert_name:
        logger.info("No certificate selected - exiting")
        sys.exit(0)

    # Step 5: Search configuration for certificate usage
    logger.info("\n🔍 Step 5/5: Analyzing certificate usage in configuration...")
    cert_usage = client.search_certificate_usage(config_backup, old_cert_name)

    # ========================================================================
    # PHASE 1 COMPLETION SUMMARY
    # ========================================================================
    logger.info("\n" + "="*80)
    logger.info("PHASE 1 COMPLETION SUMMARY")
    logger.info("="*80)

    # Count total references for display
    total_refs = sum(len(v) for v in cert_usage.values())

    logger.info("\n✅ BACKUP STATUS:")
    logger.info(f"   • Configuration: {Path(config_backup).name}")
    logger.info(f"     Location: {config_backup}")
    if backups['device_state']:
        logger.info(f"   • Device State: {Path(backups['device_state']).name}")
        logger.info(f"     Location: {backups['device_state']}")
        logger.info(f"     Size: {Path(backups['device_state']).stat().st_size / (1024*1024):.1f} MB")
    else:
        logger.info(f"   • Device State: ⚠️  Not backed up (non-critical)")

    logger.info("\n📝 CERTIFICATE INFORMATION:")
    logger.info(f"   • Current certificate: {old_cert_name}")
    logger.info(f"   • New certificate: {args.cert_name}")
    logger.info(f"   • Usage locations found: {total_refs}")

    if total_refs > 0:
        logger.info("\n🎯 LOCATIONS TO UPDATE:")
        if cert_usage['ssl_tls_profiles']:
            logger.info(f"   • SSL/TLS Profiles: {len(cert_usage['ssl_tls_profiles'])} profile(s)")
        if cert_usage['portals']:
            logger.info(f"   • GlobalProtect Portals: {len(cert_usage['portals'])} portal(s)")
        if cert_usage['gateways']:
            logger.info(f"   • GlobalProtect Gateways: {len(cert_usage['gateways'])} gateway(s)")
        if cert_usage['other']:
            logger.info(f"   • Other References: {len(cert_usage['other'])} location(s)")

    logger.info("\n" + "="*80)
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE")
        logger.info("="*80)
        logger.info("Phase 2 would perform the following actions:")
    else:
        logger.info("📋 NEXT STEPS - PHASE 2")
        logger.info("="*80)
        logger.info("Phase 2 will perform the following actions:")

    logger.info(f"\n1️⃣  Upload New Certificate")
    logger.info(f"   • Certificate file: {args.cert_file}")
    logger.info(f"   • Private key: {args.key_file}")
    if args.chain_file:
        logger.info(f"   • Certificate chain: {args.chain_file}")
    logger.info(f"   • Name on firewall: {args.cert_name}")

    if total_refs > 0:
        logger.info(f"\n2️⃣  Update Configuration References")
        if cert_usage['ssl_tls_profiles']:
            logger.info(f"   • Update {len(cert_usage['ssl_tls_profiles'])} SSL/TLS profile(s)")
        if cert_usage['portals']:
            logger.info(f"   • Update {len(cert_usage['portals'])} GlobalProtect portal(s)")
        if cert_usage['gateways']:
            logger.info(f"   • Update {len(cert_usage['gateways'])} GlobalProtect gateway(s)")
        if cert_usage['other']:
            logger.info(f"   • Update {len(cert_usage['other'])} other reference(s)")
    else:
        logger.info(f"\n⚠️  Note: No existing references found to update")
        logger.info(f"   New certificate will be uploaded but not automatically applied")

    logger.info(f"\n3️⃣  Commit Changes")
    logger.info(f"   • Validate configuration")
    logger.info(f"   • Commit (admin-only scope)")
    logger.info(f"   • Monitor commit status")

    # Exit if dry run
    if args.dry_run:
        logger.info("\n" + "="*80)
        logger.info("✓ DRY RUN COMPLETE")
        logger.info("="*80)
        logger.info("To execute Phase 2, run this command again without --dry-run")
        logger.info("="*80 + "\n")
        sys.exit(0)

    # ========================================================================
    # PHASE 2: CERTIFICATE UPLOAD AND CONFIGURATION UPDATE
    # ========================================================================
    logger.info("\n" + "="*80)
    logger.info("PHASE 2: CERTIFICATE UPLOAD AND CONFIGURATION UPDATE")
    logger.info("="*80 + "\n")

    phase2_success = True
    phase2_results = {
        'cert_uploaded': False,
        'chain_uploaded': False,
        'profiles_updated': [],
        'profiles_failed': []
    }

    # Step 1: Upload certificate and private key
    logger.info("📤 Step 1/3: Uploading new certificate and private key...")
    cert_uploaded = client.upload_certificate(
        args.cert_name,
        args.cert_file,
        args.key_file,
        args.passphrase
    )

    if cert_uploaded:
        phase2_results['cert_uploaded'] = True
        logger.info("")
    else:
        logger.error("✗ Failed to upload certificate - cannot proceed with Phase 2")
        phase2_success = False

    # Step 2: Upload certificate chain (if provided)
    if args.chain_file and phase2_success:
        logger.info("📤 Step 2/3: Uploading certificate chain...")
        chain_name = f"{args.cert_name}-chain"
        chain_uploaded = client.upload_certificate_chain(chain_name, args.chain_file)

        if chain_uploaded:
            phase2_results['chain_uploaded'] = True
            logger.info("")
        else:
            logger.warning("⚠️  Certificate chain upload failed (non-critical)")
            logger.info("")
    elif not args.chain_file:
        logger.info("ℹ️  Step 2/3: No certificate chain provided - skipping")
        logger.info("")

    # Verify certificate exists in configuration before updating profiles
    if phase2_success:
        logger.debug("Verifying new certificate is visible in firewall configuration...")
        cert_exists = client.verify_certificate_exists(args.cert_name)

        if not cert_exists:
            logger.error(f"✗ Certificate '{args.cert_name}' not found in firewall configuration")
            logger.error("   The certificate was uploaded but is not yet visible in the config.")
            logger.error("   This may indicate an import issue or permission problem.")
            phase2_success = False

    # Step 3: Update SSL/TLS service profiles
    if cert_usage['ssl_tls_profiles'] and phase2_success:
        logger.info(f"🔧 Step 3/3: Updating SSL/TLS service profiles...")
        logger.info(f"   Found {len(cert_usage['ssl_tls_profiles'])} profile(s) to update\n")

        for profile_name in cert_usage['ssl_tls_profiles']:
            profile_updated = client.update_ssl_tls_profile(profile_name, args.cert_name)

            if profile_updated:
                phase2_results['profiles_updated'].append(profile_name)
            else:
                phase2_results['profiles_failed'].append(profile_name)
                phase2_success = False

            logger.info("")  # Blank line between profiles
    else:
        logger.info("ℹ️  Step 3/3: No SSL/TLS profiles to update")
        logger.info("")

    # ========================================================================
    # PHASE 2 COMPLETION SUMMARY
    # ========================================================================
    logger.info("="*80)
    logger.info("PHASE 2 COMPLETION SUMMARY")
    logger.info("="*80)

    if phase2_success:
        logger.info("\n✅ STATUS: SUCCESS")
    else:
        logger.info("\n❌ STATUS: PARTIAL FAILURE")

    logger.info("\n📤 CERTIFICATE UPLOAD:")
    if phase2_results['cert_uploaded']:
        logger.info(f"   ✓ Certificate: {args.cert_name}")
        logger.info(f"     File: {Path(args.cert_file).name}")
    else:
        logger.info(f"   ✗ Certificate upload FAILED")

    if args.chain_file:
        if phase2_results['chain_uploaded']:
            logger.info(f"   ✓ Chain: {args.cert_name}-chain")
            logger.info(f"     File: {Path(args.chain_file).name}")
        else:
            logger.info(f"   ⚠️  Chain upload failed (non-critical)")

    if phase2_results['profiles_updated'] or phase2_results['profiles_failed']:
        logger.info("\n🔧 SSL/TLS PROFILES UPDATED:")
        for profile in phase2_results['profiles_updated']:
            logger.info(f"   ✓ {profile}")

        if phase2_results['profiles_failed']:
            logger.info("\n❌ SSL/TLS PROFILES FAILED:")
            for profile in phase2_results['profiles_failed']:
                logger.info(f"   ✗ {profile}")

    # ========================================================================
    # PHASE 3: PORTAL & GATEWAY UPDATES
    # ========================================================================
    logger.info("\n" + "="*80)
    logger.info("PHASE 3: PORTAL & GATEWAY UPDATES")
    logger.info("="*80 + "\n")

    phase3_success = True
    phase3_results = {
        'portals_updated': [],
        'portals_failed': [],
        'gateways_updated': [],
        'gateways_failed': []
    }

    if cert_usage['portals'] or cert_usage['gateways']:
        # Update GlobalProtect portals
        if cert_usage['portals'] and phase2_success:
            logger.info(f"🔐 Step 1/2: Updating GlobalProtect portals...")
            logger.info(f"   Found {len(cert_usage['portals'])} portal(s) to update\n")

            for portal_name in cert_usage['portals']:
                portal_updated = client.update_portal_certificate(portal_name, args.cert_name)

                if portal_updated:
                    phase3_results['portals_updated'].append(portal_name)
                else:
                    phase3_results['portals_failed'].append(portal_name)
                    phase3_success = False

                logger.info("")  # Blank line between portals
        elif cert_usage['portals']:
            logger.info("ℹ️  Step 1/2: Skipping portal updates (Phase 2 had errors)")
            logger.info("")

        # Update GlobalProtect gateways
        if cert_usage['gateways'] and phase2_success:
            logger.info(f"🚪 Step 2/2: Updating GlobalProtect gateways...")
            logger.info(f"   Found {len(cert_usage['gateways'])} gateway(s) to update\n")

            for gateway_name in cert_usage['gateways']:
                gateway_updated = client.update_gateway_certificate(gateway_name, args.cert_name)

                if gateway_updated:
                    phase3_results['gateways_updated'].append(gateway_name)
                else:
                    phase3_results['gateways_failed'].append(gateway_name)
                    phase3_success = False

                logger.info("")  # Blank line between gateways
        elif cert_usage['gateways']:
            logger.info("ℹ️  Step 2/2: Skipping gateway updates (Phase 2 had errors)")
            logger.info("")

        # Phase 3 Summary
        logger.info("="*80)
        logger.info("PHASE 3 COMPLETION SUMMARY")
        logger.info("="*80)

        if phase3_success:
            logger.info("\n✅ STATUS: SUCCESS")
        else:
            logger.info("\n❌ STATUS: PARTIAL FAILURE")

        if phase3_results['portals_updated'] or phase3_results['portals_failed']:
            logger.info("\n🔐 GLOBALPROTECT PORTALS UPDATED:")
            for portal in phase3_results['portals_updated']:
                logger.info(f"   ✓ {portal}")

            if phase3_results['portals_failed']:
                logger.info("\n❌ GLOBALPROTECT PORTALS FAILED:")
                for portal in phase3_results['portals_failed']:
                    logger.info(f"   ✗ {portal}")

        if phase3_results['gateways_updated'] or phase3_results['gateways_failed']:
            logger.info("\n🚪 GLOBALPROTECT GATEWAYS UPDATED:")
            for gateway in phase3_results['gateways_updated']:
                logger.info(f"   ✓ {gateway}")

            if phase3_results['gateways_failed']:
                logger.info("\n❌ GLOBALPROTECT GATEWAYS FAILED:")
                for gateway in phase3_results['gateways_failed']:
                    logger.info(f"   ✗ {gateway}")
    else:
        logger.info("ℹ️  No GlobalProtect portals or gateways found to update")
        logger.info("✓ Phase 3 skipped - no portal/gateway configurations using this certificate")

    logger.info("\n" + "="*80)
    logger.info("⚠️  IMPORTANT: Changes NOT yet committed!")
    logger.info("="*80)
    logger.info("Configuration changes are staged but not active.")
    logger.info("Phase 4 will validate and commit changes to make them active.")
    logger.info("="*80 + "\n")

    # Check overall success
    overall_success = phase2_success and phase3_success

    if not overall_success:
        if not phase2_success:
            logger.error("Phase 2 completed with errors - review log before proceeding")
        if not phase3_success:
            logger.error("Phase 3 completed with errors - review log before proceeding")
        sys.exit(1)

    logger.info("✅ All phases completed successfully!")
    logger.info("Certificate update ready for commit (Phase 4)\n")
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)
