# Palo Alto Address Object Manager - Documentation Index

Complete guide to all documentation and files in this project.

## 📚 Documentation Files

### For Getting Started

| File | Purpose | Read Time |
|------|---------|-----------|
| **[QUICKSTART.md](QUICKSTART.md)** | 5-minute quick start guide | 5 min |
| **[SETUP.md](SETUP.md)** | Detailed virtual environment setup | 10 min |
| **[README.md](README.md)** | Complete reference documentation | 30 min |

### For Reference

| File | Purpose | Use When |
|------|---------|----------|
| **[CSV_STRUCTURE.md](CSV_STRUCTURE.md)** | CSV file format and examples | Creating/modifying CSV files |
| **requirements.txt** | Python dependencies | Setting up environment |
| **.gitignore** | Git ignore patterns | Setting up version control |

## 🛠️ Script Files

### Main Scripts

| File | Purpose | Executable |
|------|---------|-----------|
| **pa_address_manager.py** | Main Python script for firewall API | ✓ |
| **update-firewall-gke.sh** | Wrapper script (auto-detects venv) | ✓ |
| **setup.sh** | One-time environment setup | ✓ |

### Data Files

| File | Purpose |
|------|---------|
| **gke-cluster-private-ips.csv** | Your GKE cluster IP inventory (25 resources) |

## 🚀 Getting Started Paths

### Path 1: Quick Start (Recommended)

For users who want to get started immediately:

1. Read **QUICKSTART.md** (5 minutes)
2. Run `./setup.sh` to create venv and install dependencies
3. Set API key: `export PA_API_KEY="your-key"`
4. Test: `./update-firewall-gke.sh dry-run`
5. Run: `./update-firewall-gke.sh`

### Path 2: Detailed Setup

For users who want to understand everything:

1. Read **README.md** - Overview and features
2. Read **SETUP.md** - Virtual environment details
3. Read **CSV_STRUCTURE.md** - Understand data format
4. Manually create venv and install dependencies
5. Test with dry run
6. Deploy to firewall

### Path 3: Advanced/Custom

For users with specific requirements:

1. Review **CSV_STRUCTURE.md** for custom CSV formats
2. Modify `pa_address_manager.py` if needed
3. Read inline script documentation
4. Create custom wrapper scripts
5. Integrate with CI/CD or automation

## 📖 Documentation by Task

### "I want to install and run it"
→ Start with **QUICKSTART.md**, then run **setup.sh**

### "I want to understand how it works"
→ Read **README.md** sections:
  - Features
  - Architecture
  - Command-line Options
  - Error Handling

### "I need to create/modify my CSV file"
→ Read **CSV_STRUCTURE.md** sections:
  - Required Columns
  - CSV Templates
  - Data Extraction Examples (GKE, GCP, AWS)
  - Validation Rules

### "I want to use a virtual environment"
→ Read **SETUP.md** for complete venv guide

### "I want to customize the tagging"
→ Read **README.md** section: "Tagging Structure"
→ Modify `generate_tags()` in **pa_address_manager.py** (line ~95)

### "I want to automate this with cron"
→ Read **README.md** section: "For Cron Jobs"
→ Read **SETUP.md** section: "For Cron Jobs"

### "I want to use this for multiple environments"
→ Read **README.md** section: "Reusability Guidelines"
→ Read **SETUP.md** section: "For Multiple Environments"

### "Something went wrong"
→ Read **README.md** section: "Troubleshooting"
→ Read **SETUP.md** section: "Troubleshooting"
→ Run with `--verbose` flag for debug output

## 🔍 Quick Reference

### Most Common Commands

```bash
# One-time setup
./setup.sh

# Set API key (do this each session)
export PA_API_KEY="your-key"

# Test before running
./update-firewall-gke.sh dry-run

# Run for real
./update-firewall-gke.sh

# Manual with venv
source venv/bin/activate
python pa_address_manager.py --help
deactivate
```

### File Sizes

```
pa_address_manager.py    16 KB   (Main script)
README.md                14 KB   (Complete docs)
CSV_STRUCTURE.md         14 KB   (CSV reference)
SETUP.md                 4.7 KB  (venv guide)
QUICKSTART.md            4.0 KB  (Quick start)
update-firewall-gke.sh   3.1 KB  (Wrapper)
setup.sh                 3.4 KB  (Setup script)
requirements.txt         108 B   (Dependencies)
```

## 📋 Checklist for First-Time Users

- [ ] Read QUICKSTART.md
- [ ] Run `./setup.sh` to create venv
- [ ] Generate Palo Alto API key
- [ ] Set API key: `export PA_API_KEY="..."`
- [ ] Verify CSV file exists: `ls gke-cluster-private-ips.csv`
- [ ] Test with dry run: `./update-firewall-gke.sh dry-run`
- [ ] Review output and tags
- [ ] Run for real: `./update-firewall-gke.sh`
- [ ] Verify objects in firewall web UI
- [ ] (Optional) Set up in crontab for automation

## 🎯 Use Cases

### Use Case 1: One-Time Import
1. Prepare CSV with current infrastructure
2. Run setup.sh
3. Execute script once
4. Done - objects created in firewall

### Use Case 2: Regular Updates
1. Set up script once
2. Update CSV regularly (manual or automated)
3. Run via cron daily/weekly
4. Firewall stays in sync with infrastructure

### Use Case 3: Multi-Environment
1. Create separate CSV files per environment
   - `gke-prod-ips.csv`
   - `gke-dev-ips.csv`
   - `gke-staging-ips.csv`
2. Run with different `--environment` and `--cluster` flags
3. Objects tagged appropriately per environment

### Use Case 4: CI/CD Integration
1. Export GKE IPs in CI pipeline
2. Format as CSV
3. Call script with API key from secrets
4. Firewall automatically updated on deployments

## 🔗 External Resources

- [Palo Alto API Documentation](https://docs.paloaltonetworks.com/pan-os/11-0/pan-os-panorama-api)
- [Python Virtual Environments](https://docs.python.org/3/library/venv.html)
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [CSV Format Specification](https://tools.ietf.org/html/rfc4180)

## 🆘 Support

### Documentation Issues
- Check INDEX.md (this file) for the right documentation
- Search within files (all are text/markdown)

### Script Issues
- Run with `--verbose` for debug output
- Check TROUBLESHOOTING section in README.md
- Review error messages carefully

### CSV Format Issues
- Consult CSV_STRUCTURE.md
- Use `--dry-run` to test without changes
- Validate CSV headers match required columns

## 📝 File Modification Guide

### Which file to edit for different needs:

**Change firewall defaults (host, environment, cluster)**
→ Edit **update-firewall-gke.sh** (lines 24-28)

**Change tag generation logic**
→ Edit **pa_address_manager.py** `generate_tags()` method (line ~95)

**Add new CSV columns support**
→ Edit **pa_address_manager.py** `REQUIRED_COLUMNS` (line ~30)

**Change API endpoints or XML structure**
→ Edit **pa_address_manager.py** `create_address_object()` (line ~132)

**Add pre/post-processing logic**
→ Edit **update-firewall-gke.sh** before/after main script call

## 🎓 Learning Resources

### Python Skills Needed
- Basic: Running scripts, using pip, virtual environments
- Intermediate: Reading Python code, understanding classes
- Advanced: Modifying script logic, adding features

### Palo Alto Skills Needed
- Basic: Understanding address objects, tags
- Intermediate: API key generation, XML API basics
- Advanced: Custom API calls, firewall automation

### Recommended Learning Path
1. Start with QUICKSTART.md - learn by doing
2. Read README.md - understand the full picture
3. Review script code - see how it works
4. Experiment with dry run - safe testing
5. Customize for your needs - make it yours

---

**Version**: 1.0.0
**Last Updated**: 2025-11-07
**Author**: Joshua Koch
