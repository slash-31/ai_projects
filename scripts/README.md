# Scripts Directory

This directory contains utility scripts and tools for managing infrastructure.

## Projects

### Palo Alto Firewall Address Manager

Location: [`pa-firewall-manager/`](pa-firewall-manager/)

**Purpose**: Automated creation and management of Palo Alto Networks firewall address objects from GKE cluster data using the XML API.

**Quick Start**:
```bash
cd pa-firewall-manager
./setup.sh              # One-time setup
export PA_API_KEY="your-key"
./update-firewall-gke.sh dry-run
```

**Documentation**: See [`pa-firewall-manager/INDEX.md`](pa-firewall-manager/INDEX.md) for complete documentation index.

**Features**:
- Bulk address object creation from CSV
- Automatic tag generation (environment, type, namespace, zone, service, cluster)
- Python virtual environment support
- Dry-run mode for safe testing
- Comprehensive error handling

---

## Adding New Scripts

When adding new utility scripts to this directory:

1. **Create a dedicated folder** for multi-file projects
2. **Include documentation**:
   - README.md with purpose and usage
   - QUICKSTART.md for quick reference
   - Inline code comments
3. **Use virtual environments** for Python projects
4. **Add to this README** with a brief description
5. **Include examples** and expected output

## Project Structure

```
scripts/
├── README.md                      # This file
├── pa-firewall-manager/           # Palo Alto firewall automation
│   ├── INDEX.md                   # Documentation index
│   ├── README.md                  # Complete documentation
│   ├── QUICKSTART.md              # 5-minute quick start
│   ├── SETUP.md                   # Virtual environment setup
│   ├── CSV_STRUCTURE.md           # CSV format reference
│   ├── EXAMPLE_OUTPUT.txt         # Example script output
│   ├── pa_address_manager.py      # Main Python script
│   ├── update-firewall-gke.sh     # Wrapper script
│   ├── setup.sh                   # One-time setup
│   ├── requirements.txt           # Python dependencies
│   ├── gke-cluster-private-ips.csv # Sample data
│   └── .gitignore                 # Git ignore patterns
└── (future scripts here)
```

## Best Practices

### For Shell Scripts
- Use `#!/bin/bash` shebang
- Include usage examples in header comments
- Make executable: `chmod +x script.sh`
- Use `set -e` to exit on errors
- Validate inputs and dependencies

### For Python Scripts
- Use virtual environments (`python3 -m venv venv`)
- Include `requirements.txt`
- Add comprehensive docstrings
- Include `if __name__ == '__main__'` guard
- Use logging instead of print for status

### For Documentation
- README.md for overview
- QUICKSTART.md for immediate usage
- Detailed docs in separate files
- Include examples with expected output
- Document prerequisites and dependencies

## Related Directories

- **Lab Tasks**: `/home/slash-31/ai_projects/lab_task/` - GKE cluster documentation
- **Rental Repair Tracker**: `/home/slash-31/ai_projects/rentalproprepairtracker/` - Full-stack app
- **Terraform Infrastructure**: `/home/slash-31/argolis_v2/` - Infrastructure as code
