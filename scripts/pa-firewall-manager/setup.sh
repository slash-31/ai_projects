#!/bin/bash
#
# One-time setup script for Palo Alto Address Object Manager
#
# This script:
#   1. Creates a Python virtual environment
#   2. Installs required dependencies
#   3. Validates the installation
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================================================"
echo "Palo Alto Address Object Manager - Setup"
echo "========================================================================"
echo ""

# Check if venv already exists
if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment already exists at: $VENV_DIR${NC}"
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing venv..."
        rm -rf "$VENV_DIR"
    else
        echo "Using existing venv. To reinstall dependencies, activate and run:"
        echo "  source venv/bin/activate"
        echo "  pip install --upgrade pip"
        echo "  pip install -r requirements.txt"
        exit 0
    fi
fi

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    echo "Please install Python 3.7 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓${NC} Found Python $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv "$VENV_DIR"
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to create virtual environment${NC}"
    echo "You may need to install python3-venv:"
    echo "  Ubuntu/Debian: sudo apt-get install python3-venv"
    echo "  RHEL/CentOS:   sudo yum install python3-venv"
    exit 1
fi
echo -e "${GREEN}✓${NC} Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✓${NC} Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo -e "${GREEN}✓${NC} pip upgraded to $(pip --version | cut -d' ' -f2)"
echo ""

# Install requirements
echo "Installing requirements..."
if [ -f "${SCRIPT_DIR}/requirements.txt" ]; then
    pip install -r "${SCRIPT_DIR}/requirements.txt"
    echo -e "${GREEN}✓${NC} Requirements installed"
else
    echo -e "${RED}Error: requirements.txt not found${NC}"
    exit 1
fi
echo ""

# Verify installation
echo "Verifying installation..."
echo "Installed packages:"
pip list | grep -E "(requests|urllib3)" || echo -e "${RED}Warning: Expected packages not found${NC}"
echo ""

# Deactivate
deactivate

echo "========================================================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Set your API key:"
echo "     export PA_API_KEY='your-api-key-here'"
echo ""
echo "  2. Test with dry run:"
echo "     ./update-firewall-gke.sh dry-run"
echo ""
echo "  3. Run for real:"
echo "     ./update-firewall-gke.sh"
echo ""
echo "The wrapper script will automatically use the virtual environment."
echo ""
echo "To manually use the venv:"
echo "  source venv/bin/activate"
echo "  python pa_address_manager.py --help"
echo "  deactivate"
echo ""
