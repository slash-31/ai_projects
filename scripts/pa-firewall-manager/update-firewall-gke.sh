#!/bin/bash
#
# Update Palo Alto Firewall with GKE Cluster Address Objects
#
# This is a wrapper script for pa_address_manager.py that makes it easy to
# repeatedly update firewall objects from GKE cluster data.
#
# Features:
#   - Automatically uses Python venv if available
#   - Validates environment and dependencies
#   - Provides colored output for easy reading
#
# Usage:
#   ./update-firewall-gke.sh [dry-run]
#
# Examples:
#   ./update-firewall-gke.sh           # Update firewall
#   ./update-firewall-gke.sh dry-run   # Test without changes
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSV_FILE="${SCRIPT_DIR}/gke-cluster-private-ips.csv"
FIREWALL="munich-pa-415.securitydude.us"
ENVIRONMENT="prod"
CLUSTER="us-central1-prod"
VENV_DIR="${SCRIPT_DIR}/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect and use Python virtual environment
PYTHON_CMD="python3"
if [ -d "$VENV_DIR" ]; then
    log_info "Found virtual environment at: $VENV_DIR"
    PYTHON_CMD="${VENV_DIR}/bin/python"
    log_info "Using venv Python: $PYTHON_CMD"
else
    log_warn "No virtual environment found (recommended for isolation)"
    log_warn "To create one: python3 -m venv $VENV_DIR"
    log_info "Using system Python: $PYTHON_CMD"
fi
echo ""

# Verify Python is available
if ! command -v $PYTHON_CMD &> /dev/null; then
    log_error "Python not found: $PYTHON_CMD"
    exit 1
fi

# Check if API key is set
if [ -z "$PA_API_KEY" ]; then
    log_error "PA_API_KEY environment variable not set"
    echo ""
    echo "Set your API key with one of these methods:"
    echo ""
    echo "  1. Export as environment variable:"
    echo "     export PA_API_KEY='your-api-key-here'"
    echo ""
    echo "  2. Load from secure file:"
    echo "     export PA_API_KEY=\$(cat ~/.pa-api-key)"
    echo ""
    echo "  3. Load from GCP Secret Manager:"
    echo "     export PA_API_KEY=\$(gcloud secrets versions access latest --secret='pa-api-key')"
    echo ""
    exit 1
fi

# Check if CSV file exists
if [ ! -f "$CSV_FILE" ]; then
    log_error "CSV file not found: $CSV_FILE"
    exit 1
fi

# Parse arguments
DRY_RUN_FLAG=""
if [ "$1" == "dry-run" ]; then
    DRY_RUN_FLAG="--dry-run"
    log_warn "Running in DRY RUN mode - no changes will be made"
fi

# Run the script
log_info "Starting firewall update..."
log_info "Python: $PYTHON_CMD"
log_info "Firewall: $FIREWALL"
log_info "CSV File: $CSV_FILE"
log_info "Environment: $ENVIRONMENT"
log_info "Cluster: $CLUSTER"
echo ""

$PYTHON_CMD "${SCRIPT_DIR}/pa_address_manager.py" \
    --api-key "$PA_API_KEY" \
    --csv-file "$CSV_FILE" \
    --firewall "$FIREWALL" \
    --environment "$ENVIRONMENT" \
    --cluster "$CLUSTER" \
    $DRY_RUN_FLAG

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    log_info "Firewall update completed successfully!"
else
    echo ""
    log_error "Firewall update failed!"
    exit 1
fi
