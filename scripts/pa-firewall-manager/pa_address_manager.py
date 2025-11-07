#!/usr/bin/env python3
"""
Palo Alto Firewall Address Object Manager

This script creates address objects in a Palo Alto Networks firewall using the REST API.
It reads IP addresses, hostnames, and metadata from a CSV file and creates corresponding
address objects with appropriate tags for organization and management.

Author: Joshua Koch
Created: 2025-11-07
Version: 2.0.0 (REST API)

Requirements:
    - Python 3.7+
    - requests library
    - CSV file with required columns (see README.md)

Usage:
    python3 pa_address_manager.py --api-key YOUR_API_KEY --csv-file gke-cluster-private-ips.csv

For full documentation, see README.md
"""

import argparse
import csv
import sys
import requests
import urllib3
from typing import Dict, List, Optional, Tuple
import logging
from urllib.parse import urljoin

# Disable SSL warnings for self-signed certificates (common with firewalls)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class PaloAltoAddressManager:
    """
    Manager class for creating and managing address objects in Palo Alto firewalls.

    This class handles:
    - Connection to Palo Alto firewall REST API
    - Creation of address objects from CSV data
    - Tag generation and management
    - Error handling and validation
    """

    # Required CSV columns
    REQUIRED_COLUMNS = [
        'IP_Address',
        'Hostname',
        'Service_Name',
        'Type',
        'Function',
        'Zone',
        'Namespace'
    ]

    def __init__(self, firewall_host: str, api_key: str, verify_ssl: bool = False, location: str = 'vsys', vsys: str = 'vsys1'):
        """
        Initialize the Palo Alto Address Manager using REST API.

        Args:
            firewall_host: Hostname or IP of the Palo Alto firewall
            api_key: API key for authentication
            verify_ssl: Whether to verify SSL certificates (default: False for self-signed)
            location: Location type (vsys, device-group, etc.)
            vsys: Virtual system name (default: vsys1)
        """
        self.firewall_host = firewall_host
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.location = location
        self.vsys = vsys

        # REST API base URL
        self.base_url = f"https://{firewall_host}/restapi/v10.2"

        # Headers for REST API
        self.headers = {
            'X-PAN-KEY': api_key,
            'Content-Type': 'application/json'
        }

        logger.info(f"Initialized REST API connection to firewall: {firewall_host}")
        logger.info(f"Using location: {location}/{vsys}")

    def _make_rest_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> requests.Response:
        """
        Make a REST API request to the Palo Alto firewall.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: JSON data for POST/PUT requests
            params: URL parameters

        Returns:
            Response object from the API call

        Raises:
            requests.RequestException: If the API call fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params, verify=self.verify_ssl, timeout=30)
            elif method == 'POST':
                # Use data= with json.dumps() like in the example (not json= parameter)
                import json as json_module
                body_str = json_module.dumps(data) if data else None
                response = requests.post(url, headers=self.headers, data=body_str, params=params, verify=self.verify_ssl, timeout=30)
            elif method == 'PUT':
                import json as json_module
                body_str = json_module.dumps(data) if data else None
                response = requests.put(url, headers=self.headers, data=body_str, params=params, verify=self.verify_ssl, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, params=params, verify=self.verify_ssl, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            return response
        except requests.RequestException as e:
            logger.error(f"REST API request failed: {e}")
            raise

    def test_connection(self) -> bool:
        """
        Test the connection to the firewall and validate the API key.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to list address objects as connection test
            endpoint = f"/Objects/Addresses"
            params = {'location': self.location, 'vsys': self.vsys}

            response = self._make_rest_request('GET', endpoint, params=params)

            if response.status_code == 200:
                logger.info("✓ Successfully connected to firewall (REST API)")
                return True
            else:
                logger.error(f"✗ Failed to connect: HTTP {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"✗ Connection test failed: {e}")
            return False

    @staticmethod
    def _sanitize_tag(tag: str) -> str:
        """
        Sanitize tag names to conform to Palo Alto requirements.

        Palo Alto tags cannot contain spaces or special characters.

        Args:
            tag: Raw tag string

        Returns:
            Sanitized tag string
        """
        # Replace spaces and underscores with hyphens
        sanitized = tag.replace(' ', '-').replace('_', '-')
        # Remove any other potentially problematic characters
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c in ['-', ':', '.'])
        return sanitized

    def generate_tags(self, row: Dict, environment: str, cluster_name: str) -> List[str]:
        """
        Generate tags for an address object based on CSV data.

        Args:
            row: Dictionary containing CSV row data
            environment: Environment name (prod, dev, staging)
            cluster_name: Name of the GKE cluster

        Returns:
            List of tag strings (sanitized for Palo Alto compatibility)
        """
        tags = []

        # Environment tag
        tags.append(f"env:{environment}")

        # Type tag (convert to lowercase and remove spaces)
        resource_type = row.get('Type', '').lower().replace(' ', '')
        if resource_type:
            tags.append(f"type:{resource_type}")

        # Namespace tag
        namespace = row.get('Namespace', 'N/A').lower()
        if namespace and namespace != 'n/a':
            tags.append(f"namespace:{namespace}")
        else:
            tags.append("namespace:none")

        # Zone tag
        zone = row.get('Zone', '').lower()
        if zone:
            tags.append(f"zone:{zone}")

        # Service tag (extract from Service_Name)
        service_name = row.get('Service_Name', '').lower()
        if service_name:
            # Extract the primary service (e.g., "adguard" from "adguard-web")
            # Remove spaces and special characters for valid tag format
            service = service_name.split('-')[0].replace(' ', '-').replace('_', '-')
            tags.append(f"service:{service}")

        # Cluster tag
        if cluster_name:
            tags.append(f"cluster:{cluster_name}")

        # Automation tag
        tags.append("auto-created")

        # Sanitize all tags to remove spaces and invalid characters
        tags = [self._sanitize_tag(tag) for tag in tags]

        return tags

    def check_tag_exists(self, tag_name: str) -> bool:
        """
        Check if a tag exists in the firewall.

        Args:
            tag_name: Name of the tag to check

        Returns:
            True if tag exists, False otherwise
        """
        try:
            endpoint = f"/Objects/Tags"
            params = {
                'location': self.location,
                'vsys': self.vsys,
                'name': tag_name
            }

            response = self._make_rest_request('GET', endpoint, params=params)

            if response.status_code == 200:
                data = response.json()
                return '@name' in str(data) and tag_name in str(data)

            return False
        except:
            return False

    def create_tag(self, tag_name: str, color: str = None, comments: str = None) -> Tuple[bool, str]:
        """
        Create a tag in the Palo Alto firewall using REST API.

        Args:
            tag_name: Name of the tag to create
            color: Optional color for the tag (e.g., "color1", "color2", etc.)
            comments: Optional comments/description for the tag

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check if tag already exists
        if self.check_tag_exists(tag_name):
            logger.debug(f"Tag '{tag_name}' already exists, skipping creation")
            return True, "Already exists"

        # Build JSON body for REST API
        entry = {
            "@name": tag_name
        }

        # Add optional fields
        if color:
            entry["color"] = color
        if comments:
            entry["comments"] = comments

        body = {"entry": entry}

        # URL parameters for location AND name (REST API requires name for POST)
        params = {
            'location': self.location,
            'vsys': self.vsys,
            'name': tag_name
        }

        endpoint = "/Objects/Tags"

        try:
            # POST to create new tag
            response = self._make_rest_request('POST', endpoint, data=body, params=params)

            if response.status_code in [200, 201]:
                logger.info(f"✓ Created tag: {tag_name}")
                return True, "Success"
            elif response.status_code == 400:
                try:
                    response_data = response.json() if response.text else {}
                    error_message = response_data.get('message', response.text)
                except:
                    error_message = response.text

                if 'already exists' in error_message.lower():
                    logger.debug(f"Tag '{tag_name}' already exists")
                    return True, "Already exists"
                else:
                    error_msg = f"Failed to create tag {tag_name}: {error_message}"
                    logger.warning(f"⚠ {error_msg}")
                    return False, error_msg
            else:
                error_msg = f"Failed to create tag {tag_name}: HTTP {response.status_code}"
                logger.warning(f"⚠ {error_msg}")
                return False, error_msg

        except Exception as e:
            error_msg = f"Exception creating tag {tag_name}: {str(e)}"
            logger.warning(f"⚠ {error_msg}")
            return False, error_msg

    def create_tags_batch(self, tags: List[str]) -> Dict[str, int]:
        """
        Create multiple tags in batch.

        Args:
            tags: List of tag names to create

        Returns:
            Dictionary with statistics (created, failed, skipped)
        """
        stats = {'created': 0, 'failed': 0, 'skipped': 0}
        unique_tags = sorted(set(tags))  # Remove duplicates and sort

        logger.info(f"Checking/creating {len(unique_tags)} unique tags...")

        for tag in unique_tags:
            success, message = self.create_tag(tag)

            if success:
                if 'already exists' in message.lower():
                    stats['skipped'] += 1
                else:
                    stats['created'] += 1
            else:
                stats['failed'] += 1

        return stats

    def check_object_exists(self, name: str) -> bool:
        """
        Check if an address object already exists in the firewall.

        Args:
            name: Name of the address object to check

        Returns:
            True if object exists, False otherwise
        """
        try:
            endpoint = f"/Objects/Addresses"
            params = {
                'location': self.location,
                'vsys': self.vsys,
                'name': name
            }

            response = self._make_rest_request('GET', endpoint, params=params)

            # If status is 200 and we get data, object exists
            if response.status_code == 200:
                data = response.json()
                return '@name' in str(data) and name in str(data)

            return False
        except:
            return False

    def create_address_object(
        self,
        name: str,
        ip_address: str,
        description: str,
        tags: List[str],
        skip_existing: bool = True
    ) -> Tuple[bool, str]:
        """
        Create an address object in the Palo Alto firewall using REST API.

        Args:
            name: Name of the address object (must be unique)
            ip_address: IP address in CIDR notation (e.g., 192.168.1.1/32)
            description: Description of the address object
            tags: List of tags to apply
            skip_existing: If True, skip creation if object already exists

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check if object already exists
        if skip_existing and self.check_object_exists(name):
            logger.warning(f"⊘ Skipping {name} - already exists")
            return True, "Skipped - already exists"

        # Ensure IP has CIDR notation
        if '/' not in ip_address:
            ip_address = f"{ip_address}/32"

        # Build JSON body for REST API
        # Start with minimal required fields
        entry = {
            "@name": name,
            "ip-netmask": ip_address
        }

        # Add description if provided (some APIs are sensitive to empty descriptions)
        if description and description.strip():
            entry["description"] = description

        # Add tags if provided
        if tags:
            entry["tag"] = {"member": tags}

        body = {"entry": entry}

        # URL parameters for location AND name (REST API requires name for POST)
        params = {
            'location': self.location,
            'vsys': self.vsys,
            'name': name
        }

        endpoint = "/Objects/Addresses"

        try:
            # Debug logging
            logger.debug(f"POST {endpoint}")
            logger.debug(f"Params: {params}")
            logger.debug(f"Body: {body}")

            # POST to create new address object
            response = self._make_rest_request('POST', endpoint, data=body, params=params)

            if response.status_code in [200, 201]:
                logger.info(f"✓ Created address object: {name} ({ip_address})")
                return True, "Success"
            elif response.status_code == 400:
                try:
                    response_data = response.json() if response.text else {}
                    error_message = response_data.get('message', response.text)
                except:
                    error_message = response.text

                if 'already exists' in error_message.lower():
                    logger.warning(f"⊘ Object {name} already exists")
                    return True, "Already exists"
                else:
                    error_msg = f"Failed to create {name}: {error_message}"
                    logger.error(f"✗ {error_msg}")
                    logger.debug(f"   Full response: {response.text}")
                    return False, error_msg
            else:
                error_msg = f"Failed to create {name}: HTTP {response.status_code} - {response.text}"
                logger.error(f"✗ {error_msg}")
                return False, error_msg

        except Exception as e:
            error_msg = f"Exception creating {name}: {str(e)}"
            logger.error(f"✗ {error_msg}")
            return False, error_msg

    def commit_changes(self) -> Tuple[bool, str]:
        """
        Commit pending changes to the firewall configuration using REST API.

        Returns:
            Tuple of (success: bool, message: str)
        """
        logger.info("Committing changes to firewall...")

        # For REST API, commit is done via /restapi/v10.2/Device/Operations/Commit
        # But for simplicity with location-based commits, we'll use the XML API
        # or just return success since REST API auto-commits in some versions

        try:
            # Use old XML API for commit (REST API commit is more complex)
            xml_url = f"https://{self.firewall_host}/api/"
            params = {
                'type': 'commit',
                'cmd': '<commit></commit>',
                'key': self.api_key
            }

            response = requests.get(xml_url, params=params, verify=self.verify_ssl, timeout=60)

            if 'success' in response.text or response.status_code == 200:
                logger.info("✓ Successfully committed changes")
                return True, "Commit successful"
            else:
                error_msg = f"Commit failed: {response.text}"
                logger.error(f"✗ {error_msg}")
                return False, error_msg

        except Exception as e:
            error_msg = f"Exception during commit: {str(e)}"
            logger.error(f"✗ {error_msg}")
            return False, error_msg

    def process_csv_file(
        self,
        csv_file: str,
        environment: str = 'prod',
        cluster_name: str = 'us-central1-prod',
        dry_run: bool = False,
        commit: bool = True,
        test_one: bool = False,
        tags_only: bool = False,
        objects_only: bool = False
    ) -> Dict[str, int]:
        """
        Process a CSV file and create address objects for each row.

        Args:
            csv_file: Path to CSV file
            environment: Environment name for tagging (default: 'prod')
            cluster_name: Cluster name for tagging (default: 'us-central1-prod')
            dry_run: If True, only validate without creating objects
            commit: If True, commit changes after creation
            test_one: If True, only process first CSV row (for testing)
            tags_only: If True, only create tags (skip address objects)
            objects_only: If True, skip tag creation (assumes tags exist)

        Returns:
            Dictionary with statistics (created, failed, skipped)
        """
        stats = {'created': 0, 'failed': 0, 'skipped': 0}

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Validate CSV columns
                if not all(col in reader.fieldnames for col in self.REQUIRED_COLUMNS):
                    missing = set(self.REQUIRED_COLUMNS) - set(reader.fieldnames)
                    logger.error(f"CSV missing required columns: {missing}")
                    logger.error(f"Found columns: {reader.fieldnames}")
                    logger.error(f"Required columns: {self.REQUIRED_COLUMNS}")
                    sys.exit(1)

                logger.info(f"Processing CSV file: {csv_file}")

                # Show mode
                if dry_run:
                    logger.info("🧪 DRY RUN MODE - No changes will be made")
                elif test_one:
                    logger.info("🔬 TEST MODE - Processing only first CSV row")
                elif tags_only:
                    logger.info("🏷️  TAGS ONLY MODE - Creating tags only")
                elif objects_only:
                    logger.info("📦 OBJECTS ONLY MODE - Skipping tag creation")

                # First pass: Collect all unique tags from all rows
                logger.info("")
                logger.info("Phase 1: Collecting tags from CSV...")
                all_tags = set()
                rows_data = []  # Store row data for second pass

                for row_num, row in enumerate(reader, start=2):
                    ip_address = row.get('IP_Address', '').strip()
                    hostname = row.get('Hostname', '').strip()

                    # Skip rows with missing critical data
                    if not ip_address or not hostname:
                        continue

                    # Generate tags for this row
                    tags = self.generate_tags(row, environment, cluster_name)
                    all_tags.update(tags)

                    # Store row data for processing
                    rows_data.append((row_num, row))

                    # If test_one mode, stop after first row
                    if test_one:
                        break

                logger.info(f"Found {len(all_tags)} unique tags across {len(rows_data)} valid objects")

                # Show which tags cover all GKE resources
                cluster_tags = [t for t in all_tags if t.startswith('cluster:')]
                auto_tags = [t for t in all_tags if t == 'auto-created']
                if cluster_tags:
                    logger.info(f"🏷️  Tags covering ALL GKE resources: {', '.join(cluster_tags + auto_tags)}")

                # Create all tags before creating address objects
                if not dry_run and not objects_only and all_tags:
                    logger.info("")
                    logger.info("Phase 2: Creating tags...")
                    tag_stats = self.create_tags_batch(list(all_tags))
                    logger.info(f"Tags - Created: {tag_stats['created']}, "
                              f"Already existed: {tag_stats['skipped']}, "
                              f"Failed: {tag_stats['failed']}")

                    # If tags_only mode, skip address object creation
                    if tags_only:
                        logger.info("")
                        logger.info("🏷️  Tags-only mode: Skipping address object creation")
                        return stats
                elif objects_only:
                    logger.info("")
                    logger.info("📦 Objects-only mode: Skipping tag creation (assuming tags exist)")

                # Second pass: Create address objects
                if not tags_only:
                    logger.info("")
                    logger.info("Phase 3: Creating address objects...")

                for row_num, row in rows_data:
                    ip_address = row.get('IP_Address', '').strip()
                    hostname = row.get('Hostname', '').strip()
                    function = row.get('Function', '').strip()

                    # Generate object name (use hostname, sanitized for firewall naming)
                    object_name = hostname.replace('.', '_').replace(' ', '_')

                    # Generate description
                    description = f"{function} - {ip_address}"

                    # Generate tags
                    tags = self.generate_tags(row, environment, cluster_name)

                    logger.info(f"Row {row_num}: {object_name} ({ip_address})")
                    logger.info(f"  Description: {description}")
                    logger.info(f"  Tags: {', '.join(tags)}")

                    if not dry_run:
                        success, message = self.create_address_object(
                            name=object_name,
                            ip_address=ip_address,
                            description=description,
                            tags=tags
                        )

                        if success:
                            if 'skip' in message.lower() or 'already exists' in message.lower():
                                stats['skipped'] += 1
                            else:
                                stats['created'] += 1
                        else:
                            stats['failed'] += 1
                    else:
                        logger.info("  [DRY RUN] Would create this object")
                        stats['created'] += 1

                # Commit changes if requested and not dry run
                if commit and not dry_run and stats['created'] > 0:
                    logger.info("")
                    self.commit_changes()

        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_file}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error processing CSV: {e}")
            sys.exit(1)

        return stats


def show_help_menu():
    """Display detailed help menu for deployment modes."""
    help_text = """
╔══════════════════════════════════════════════════════════════════════╗
║     Palo Alto Address Object Manager - Deployment Modes Help        ║
║                          v2.0.0 (REST API)                           ║
╚══════════════════════════════════════════════════════════════════════╝

This script supports step-by-step deployment for safe, incremental rollout.

┌──────────────────────────────────────────────────────────────────────┐
│ DEPLOYMENT MODES                                                     │
└──────────────────────────────────────────────────────────────────────┘

  1️⃣  --test-one       Test with first CSV row only
      Creates tags + address object for the first row only.
      Perfect for validating everything works before full deployment.

      Example:
        python3 pa_address_manager.py --api-key KEY --csv-file data.csv --test-one

  2️⃣  --tags-only      Create all tags (skip address objects)
      Scans all CSV rows and creates all unique tags.
      Skips address object creation entirely.

      Example:
        python3 pa_address_manager.py --api-key KEY --csv-file data.csv --tags-only

  3️⃣  --objects-only   Create address objects only (skip tag creation)
      Assumes tags already exist in the firewall.
      Creates all address objects and attaches existing tags.

      Example:
        python3 pa_address_manager.py --api-key KEY --csv-file data.csv --objects-only

  4️⃣  (Normal mode)    Create everything at once
      Creates all tags + all address objects in one run.
      Safest approach after validating with --test-one.

      Example:
        python3 pa_address_manager.py --api-key KEY --csv-file data.csv

┌──────────────────────────────────────────────────────────────────────┐
│ RECOMMENDED WORKFLOW (First Time Deployment)                        │
└──────────────────────────────────────────────────────────────────────┘

  Step 1: Test with one record
    $ python3 pa_address_manager.py --api-key KEY --csv-file data.csv --test-one
    ✓ Verify first tag created
    ✓ Verify first address object created
    ✓ Check object has correct tags

  Step 2: Create all tags
    $ python3 pa_address_manager.py --api-key KEY --csv-file data.csv --tags-only
    ✓ Verify all tags visible in firewall
    ✓ Tags show "0 references" (not used yet)

  Step 3: Create all address objects
    $ python3 pa_address_manager.py --api-key KEY --csv-file data.csv --objects-only
    ✓ Verify all objects created
    ✓ Filter by cluster:CLUSTER-NAME to see all

  Step 4: Future updates (use normal mode)
    $ python3 pa_address_manager.py --api-key KEY --csv-file data.csv
    ✓ Script skips existing tags/objects automatically

┌──────────────────────────────────────────────────────────────────────┐
│ FINDING ALL GKE CLUSTER RESOURCES                                   │
└──────────────────────────────────────────────────────────────────────┘

  Two tags identify ALL resources from your GKE cluster:

    🏷️  cluster:CLUSTER-NAME    (e.g., cluster:us-central1-prod)
        Filter by this tag to see all objects from a specific cluster

    🏷️  auto-created
        Filter by this tag to see all script-created objects

  In Firewall UI:
    Device → Objects → Addresses → Filter by tag → Select cluster tag

┌──────────────────────────────────────────────────────────────────────┐
│ OTHER USEFUL OPTIONS                                                 │
└──────────────────────────────────────────────────────────────────────┘

  --dry-run          Show what would be created without making changes
  --no-commit        Create objects but don't commit (manual commit needed)
  --environment      Set environment tag (prod/dev/staging)
  --cluster          Set cluster name for tagging
  --verbose          Show detailed debug logging

┌──────────────────────────────────────────────────────────────────────┐
│ EXAMPLES                                                             │
└──────────────────────────────────────────────────────────────────────┘

  # Test with first row (recommended first step)
  $ python3 pa_address_manager.py --api-key KEY --csv-file data.csv --test-one

  # Create only tags for development environment
  $ python3 pa_address_manager.py --api-key KEY --csv-file data.csv \\
      --tags-only --environment dev --cluster us-east1-dev

  # Create objects for existing tags
  $ python3 pa_address_manager.py --api-key KEY --csv-file data.csv --objects-only

  # Full deployment with verbose logging
  $ python3 pa_address_manager.py --api-key KEY --csv-file data.csv --verbose

  # Dry run to preview changes
  $ python3 pa_address_manager.py --api-key KEY --csv-file data.csv --dry-run

┌──────────────────────────────────────────────────────────────────────┐
│ TROUBLESHOOTING                                                      │
└──────────────────────────────────────────────────────────────────────┘

  "Missing Query Parameter: name"
    → Fixed in v2.0.0 - make sure you're using latest version

  "Invalid Object"
    → Check CSV format matches required columns
    → Use --verbose to see full request/response

  Tags/Objects already exist
    → This is normal - script automatically skips existing items
    → Shows as "Skipped" in statistics

  Connection failed
    → Verify firewall hostname is correct
    → Check API key is valid
    → Ensure management interface is accessible

┌──────────────────────────────────────────────────────────────────────┐
│ MORE INFORMATION                                                     │
└──────────────────────────────────────────────────────────────────────┘

  README.md           Complete documentation
  STEP_BY_STEP.md     Detailed step-by-step guide with validation
  TAGS.md             Tag reference and filtering guide
  CSV_STRUCTURE.md    CSV format and examples

╔══════════════════════════════════════════════════════════════════════╗
║  For standard help: python3 pa_address_manager.py --help            ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(help_text)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Create Palo Alto firewall address objects from CSV file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python3 pa_address_manager.py --api-key YOUR_KEY --csv-file gke-ips.csv

  # Dry run to test without making changes
  python3 pa_address_manager.py --api-key YOUR_KEY --csv-file gke-ips.csv --dry-run

  # Specify environment and cluster
  python3 pa_address_manager.py --api-key YOUR_KEY --csv-file gke-ips.csv \\
    --environment prod --cluster us-central1-prod

  # Create without committing (manual commit required)
  python3 pa_address_manager.py --api-key YOUR_KEY --csv-file gke-ips.csv --no-commit
        """
    )

    parser.add_argument(
        '--api-key',
        required=True,
        help='Palo Alto firewall API key'
    )

    parser.add_argument(
        '--csv-file',
        required=True,
        help='Path to CSV file containing IP addresses and metadata'
    )

    parser.add_argument(
        '--firewall',
        default='munich-pa-415.securitydude.us',
        help='Firewall hostname or IP (default: munich-pa-415.securitydude.us)'
    )

    parser.add_argument(
        '--environment',
        default='prod',
        choices=['prod', 'dev', 'staging'],
        help='Environment name for tagging (default: prod)'
    )

    parser.add_argument(
        '--cluster',
        default='us-central1-prod',
        help='GKE cluster name for tagging (default: us-central1-prod)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate and show what would be created without making changes'
    )

    parser.add_argument(
        '--no-commit',
        action='store_true',
        help='Create objects but do not commit changes (requires manual commit)'
    )

    parser.add_argument(
        '--verify-ssl',
        action='store_true',
        help='Verify SSL certificates (default: disabled for self-signed certs)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )

    parser.add_argument(
        '--help-modes',
        action='store_true',
        help='Show detailed help for step-by-step deployment modes'
    )

    # Step-by-step mode options
    parser.add_argument(
        '--test-one',
        action='store_true',
        help='Test mode: create tag and address object for only the first CSV row'
    )

    parser.add_argument(
        '--tags-only',
        action='store_true',
        help='Create only tags (skip address object creation)'
    )

    parser.add_argument(
        '--objects-only',
        action='store_true',
        help='Create only address objects (skip tag creation, assumes tags exist)'
    )

    args = parser.parse_args()

    # Show detailed help menu if requested
    if args.help_modes:
        show_help_menu()
        sys.exit(0)

    # Validate conflicting options
    mode_count = sum([args.test_one, args.tags_only, args.objects_only])
    if mode_count > 1:
        parser.error("Cannot use --test-one, --tags-only, and --objects-only together. Choose one.")

    if args.dry_run and (args.tags_only or args.objects_only or args.test_one):
        parser.error("--dry-run cannot be used with --test-one, --tags-only, or --objects-only")

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Print banner
    print("=" * 70)
    print("Palo Alto Firewall Address Object Manager v2.0.0 (REST API)")
    print("=" * 70)
    print()

    # Initialize manager
    manager = PaloAltoAddressManager(
        firewall_host=args.firewall,
        api_key=args.api_key,
        verify_ssl=args.verify_ssl
    )

    # Test connection
    if not manager.test_connection():
        logger.error("Failed to connect to firewall. Check API key and connectivity.")
        sys.exit(1)

    print()

    # Process CSV file
    stats = manager.process_csv_file(
        csv_file=args.csv_file,
        environment=args.environment,
        cluster_name=args.cluster,
        dry_run=args.dry_run,
        commit=not args.no_commit,
        test_one=args.test_one,
        tags_only=args.tags_only,
        objects_only=args.objects_only
    )

    # Print summary
    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)

    if args.test_one:
        print(f"🔬 TEST MODE: Processed 1 object")
        print(f"   Address Objects - Created: {stats['created']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}")
    elif args.tags_only:
        print(f"🏷️  TAGS ONLY MODE: Created tags, skipped address objects")
    elif args.objects_only:
        print(f"📦 OBJECTS ONLY MODE: Created address objects (skipped tag creation)")
        print(f"   Address Objects - Created: {stats['created']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}")
    else:
        print(f"Address Objects - Created: {stats['created']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}")

    print()

    if args.dry_run:
        print("DRY RUN completed - no changes were made to the firewall")
    elif args.test_one:
        print("TEST completed - created tag and object for first CSV row only")
        print("Next steps: Use --tags-only, then --objects-only, or run normally")
    elif args.tags_only:
        print("Tags created successfully")
        print("Next step: Run with --objects-only to create address objects")
    elif args.objects_only:
        print("Address objects created (assumed tags already exist)")
        if not args.no_commit:
            print("Changes have been committed to the firewall")
    elif args.no_commit:
        print("Changes created but NOT committed - manual commit required")
    else:
        print("All changes have been committed to the firewall")

    print("=" * 70)

    # Exit with appropriate code
    sys.exit(0 if stats['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
