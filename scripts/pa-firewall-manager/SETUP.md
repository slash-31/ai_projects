# Setup Guide - Python Virtual Environment

This guide shows how to set up a Python virtual environment for the Palo Alto Address Object Manager.

## Why Use a Virtual Environment?

✅ **Benefits**:
- Isolates dependencies from system Python
- Prevents version conflicts with other projects
- Makes dependencies explicit and reproducible
- Follows Python best practices
- Easy to recreate on different systems

## Quick Setup

### 1. Create Virtual Environment

```bash
cd /home/slash-31/ai_projects/scripts

# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Your prompt should now show (venv)
```

### 2. Install Dependencies

```bash
# With venv activated
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
# Check installed packages
pip list

# Should show:
# requests
# urllib3
```

### 4. Test the Script

```bash
# Set API key
export PA_API_KEY="your-api-key"

# Test with dry run (venv still activated)
python pa_address_manager.py \
  --csv-file gke-cluster-private-ips.csv \
  --dry-run \
  --api-key "$PA_API_KEY"
```

### 5. Deactivate When Done

```bash
deactivate
```

## Using the Virtual Environment

### Manual Usage

**Every time you want to run the script:**

```bash
# Activate venv
source /home/slash-31/ai_projects/scripts/venv/bin/activate

# Run script
export PA_API_KEY="your-api-key"
python pa_address_manager.py --csv-file gke-cluster-private-ips.csv --api-key "$PA_API_KEY"

# Deactivate when done
deactivate
```

### Using the Wrapper Script

The updated `update-firewall-gke.sh` automatically handles venv activation:

```bash
# Just run it - venv is handled automatically
./update-firewall-gke.sh dry-run
```

## For Cron Jobs

When running from cron, use the full path to the venv Python:

```bash
# Crontab entry
0 2 * * * /home/slash-31/ai_projects/scripts/venv/bin/python /home/slash-31/ai_projects/scripts/pa_address_manager.py --api-key "$(cat ~/.pa-api-key)" --csv-file /home/slash-31/ai_projects/scripts/gke-cluster-private-ips.csv >> /var/log/pa-updates.log 2>&1
```

Or use the wrapper script which handles the venv:

```bash
# Crontab entry (simpler)
0 2 * * * /home/slash-31/ai_projects/scripts/update-firewall-gke.sh >> /var/log/pa-updates.log 2>&1
```

## Recreating Environment on Another System

### Export Dependencies (optional, but helpful)

```bash
# With venv activated
pip freeze > requirements-frozen.txt
```

This creates a file with exact versions for reproducibility.

### On New System

```bash
# Clone/copy the scripts directory
cd /path/to/scripts

# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or use frozen versions
pip install -r requirements-frozen.txt
```

## Troubleshooting

### "python3: command not found"

Try `python` instead of `python3`:
```bash
python -m venv venv
```

### "No module named venv"

Install python3-venv:
```bash
# Ubuntu/Debian
sudo apt-get install python3-venv

# RHEL/CentOS
sudo yum install python3-venv
```

### Wrong Python Version

Specify the Python version explicitly:
```bash
python3.9 -m venv venv
# or
/usr/bin/python3 -m venv venv
```

### Permissions Issues

Make sure you own the scripts directory:
```bash
ls -la /home/slash-31/ai_projects/scripts
# Should show your username
```

## Best Practices

### 1. Always Activate Before Running

```bash
source venv/bin/activate
python pa_address_manager.py ...
```

### 2. Update Dependencies Regularly

```bash
source venv/bin/activate
pip install --upgrade pip
pip install --upgrade -r requirements.txt
```

### 3. Don't Commit venv to Git

Add to `.gitignore`:
```bash
echo "venv/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
```

### 4. Document Python Version

Create a `.python-version` file:
```bash
python3 --version > .python-version
```

## Complete Setup Checklist

- [ ] Create virtual environment: `python3 -m venv venv`
- [ ] Activate venv: `source venv/bin/activate`
- [ ] Upgrade pip: `pip install --upgrade pip`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify installation: `pip list`
- [ ] Test with dry run: `./update-firewall-gke.sh dry-run`
- [ ] Set up API key securely
- [ ] Add venv/ to .gitignore
- [ ] Deactivate when done: `deactivate`

## Quick Reference

```bash
# Create venv (one time)
python3 -m venv venv

# Activate venv (every session)
source venv/bin/activate

# Install/update packages (as needed)
pip install -r requirements.txt

# Deactivate venv (end of session)
deactivate

# Run script with venv
source venv/bin/activate && python pa_address_manager.py --help

# Or use wrapper (handles venv automatically)
./update-firewall-gke.sh
```
