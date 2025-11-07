# Step-by-Step Deployment Guide

This guide shows how to deploy address objects incrementally, testing at each step.

## Quick Reference

| Command | Purpose | What It Does |
|---------|---------|--------------|
| `--test-one` | Test with one record | Creates tag + address object for first CSV row only |
| `--tags-only` | Create all tags | Creates all tags, skips address objects |
| `--objects-only` | Create address objects | Creates address objects, skips tag creation |
| (normal) | Full deployment | Creates tags + address objects for all rows |

## Step-by-Step Workflow

### Step 1: Test with One Record

Test everything works with just the first CSV row:

```bash
export PA_API_KEY="your-api-key"

python3 pa_address_manager.py \
  --api-key "$PA_API_KEY" \
  --csv-file gke-cluster-private-ips.csv \
  --test-one
```

**Expected output:**
```
🔬 TEST MODE - Processing only first CSV row
Phase 1: Collecting tags from CSV...
Found 7 unique tags across 1 valid objects
Phase 2: Creating tags...
✓ Created tag: env:prod
✓ Created tag: type:infrastructure
... (5 more tags)
Phase 3: Creating address objects...
✓ Created address object: meraki-vmx-small (172.27.0.2/32)

Summary
======================================================================
🔬 TEST MODE: Processed 1 object
   Address Objects - Created: 1, Failed: 0, Skipped: 0

TEST completed - created tag and object for first CSV row only
Next steps: Use --tags-only, then --objects-only, or run normally
```

**Verify in firewall:**
1. Check tags exist: Device → Objects → Tags
2. Check object exists: Device → Objects → Addresses
3. Look for `meraki-vmx-small`

---

### Step 2: Create All Tags

Create all tags that will be needed (without creating address objects):

```bash
python3 pa_address_manager.py \
  --api-key "$PA_API_KEY" \
  --csv-file gke-cluster-private-ips.csv \
  --tags-only
```

**Expected output:**
```
🏷️  TAGS ONLY MODE - Creating tags only
Phase 1: Collecting tags from CSV...
Found 22 unique tags across 25 valid objects
🏷️  Tags covering ALL GKE resources: cluster:us-central1-prod, auto-created

Phase 2: Creating tags...
Tag 'env:prod' already exists, skipping creation
✓ Created tag: type:internalloadbalancer
✓ Created tag: type:clusterip
... (18 more tags)
Tags - Created: 20, Already existed: 2, Failed: 0

🏷️  Tags-only mode: Skipping address object creation

Summary
======================================================================
🏷️  TAGS ONLY MODE: Created tags, skipped address objects

Tags created successfully
Next step: Run with --objects-only to create address objects
```

**Verify in firewall:**
1. Go to: Device → Objects → Tags
2. You should see all 22 tags
3. Tags show "0 references" (no objects using them yet)

---

### Step 3: Create All Address Objects

Create all address objects using the existing tags:

```bash
python3 pa_address_manager.py \
  --api-key "$PA_API_KEY" \
  --csv-file gke-cluster-private-ips.csv \
  --objects-only
```

**Expected output:**
```
📦 OBJECTS ONLY MODE - Skipping tag creation
Phase 1: Collecting tags from CSV...
Found 22 unique tags across 25 valid objects

📦 Objects-only mode: Skipping tag creation (assuming tags exist)

Phase 3: Creating address objects...
⊘ Skipping meraki-vmx-small - already exists
✓ Created address object: gke-us-central1-prod-cec941c1-no3d (172.27.32.12/32)
... (23 more objects)

Summary
======================================================================
📦 OBJECTS ONLY MODE: Created address objects (skipped tag creation)
   Address Objects - Created: 24, Failed: 0, Skipped: 1

Address objects created (assumed tags already exist)
Changes have been committed to the firewall
```

**Verify in firewall:**
1. Go to: Device → Objects → Addresses
2. Filter by tag: `cluster:us-central1-prod`
3. You should see all 25 objects
4. Each object should have multiple tags

---

### Step 4: Full Deployment (All-in-One)

Once you're confident everything works, you can deploy everything at once:

```bash
python3 pa_address_manager.py \
  --api-key "$PA_API_KEY" \
  --csv-file gke-cluster-private-ips.csv
```

**Expected output:**
```
Phase 1: Collecting tags from CSV...
Found 22 unique tags across 25 valid objects

Phase 2: Creating tags...
Tag 'env:prod' already exists, skipping creation
... (all tags already exist)
Tags - Created: 0, Already existed: 22, Failed: 0

Phase 3: Creating address objects...
⊘ Skipping meraki-vmx-small - already exists
... (all objects already exist)

Summary
======================================================================
Address Objects - Created: 0, Failed: 0, Skipped: 25

All changes have been committed to the firewall
```

---

## Common Scenarios

### Scenario 1: First Time Setup

```bash
# Step 1: Test with one record
python3 pa_address_manager.py --api-key "$PA_API_KEY" --csv-file data.csv --test-one

# If successful, continue:
# Step 2: Create all tags
python3 pa_address_manager.py --api-key "$PA_API_KEY" --csv-file data.csv --tags-only

# Step 3: Create all objects
python3 pa_address_manager.py --api-key "$PA_API_KEY" --csv-file data.csv --objects-only
```

### Scenario 2: Tags Already Exist

If tags were created previously or manually:

```bash
# Skip tag creation, just create objects
python3 pa_address_manager.py --api-key "$PA_API_KEY" --csv-file data.csv --objects-only
```

### Scenario 3: Update Existing Deployment

Adding new resources to existing deployment:

```bash
# Tags already exist, just create new objects
# Existing objects will be skipped automatically
python3 pa_address_manager.py --api-key "$PA_API_KEY" --csv-file updated-data.csv --objects-only
```

### Scenario 4: Test After CSV Changes

After modifying your CSV:

```bash
# Test with first row to validate changes
python3 pa_address_manager.py --api-key "$PA_API_KEY" --csv-file new-data.csv --test-one
```

---

## Error Recovery

### If Tag Creation Fails

```bash
# Fix the issue, then retry just tags
python3 pa_address_manager.py --api-key "$PA_API_KEY" --csv-file data.csv --tags-only

# Tags that succeeded will be skipped automatically
```

### If Object Creation Fails Mid-Way

```bash
# Fix the issue, then retry just objects
python3 pa_address_manager.py --api-key "$PA_API_KEY" --csv-file data.csv --objects-only

# Objects that were created will be skipped automatically
```

### If You Want to Start Fresh

To remove everything and start over:

```bash
# 1. In firewall: Device → Objects → Addresses
#    Filter by: auto-created
#    Select all → Delete

# 2. In firewall: Device → Objects → Tags
#    Delete tags (or leave them for reuse)

# 3. Start from step 1
python3 pa_address_manager.py --api-key "$PA_API_KEY" --csv-file data.csv --test-one
```

---

## Validation Checklist

After each step, verify:

### After --test-one:
- [ ] First tag exists in firewall
- [ ] First address object exists
- [ ] Object has correct IP and description
- [ ] Object has all expected tags
- [ ] No errors in output

### After --tags-only:
- [ ] All tags visible in Device → Objects → Tags
- [ ] Tag count matches script output
- [ ] Tags show "0 references" (not used yet)
- [ ] No failed tag creations

### After --objects-only:
- [ ] All objects visible in Device → Objects → Addresses
- [ ] Filter by `cluster:us-central1-prod` shows all objects
- [ ] Each object has correct tags
- [ ] Object count matches CSV row count
- [ ] No failed object creations

---

## Wrapper Script

For convenience, create a wrapper script:

```bash
#!/bin/bash
# deploy-step-by-step.sh

export PA_API_KEY=$(cat ~/.pa-api-key)
CSV_FILE="gke-cluster-private-ips.csv"

echo "Step 1: Testing with one record..."
python3 pa_address_manager.py --api-key "$PA_API_KEY" --csv-file "$CSV_FILE" --test-one
read -p "Continue to step 2? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 1; fi

echo "Step 2: Creating all tags..."
python3 pa_address_manager.py --api-key "$PA_API_KEY" --csv-file "$CSV_FILE" --tags-only
read -p "Continue to step 3? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 1; fi

echo "Step 3: Creating all address objects..."
python3 pa_address_manager.py --api-key "$PA_API_KEY" --csv-file "$CSV_FILE" --objects-only

echo "Deployment complete!"
```

---

## Tips

1. **Always start with --test-one** when testing changes
2. **Use --tags-only first** to validate tag creation separately
3. **Use --objects-only** to avoid recreating tags
4. **Check firewall UI** after each step to validate
5. **Script is idempotent** - safe to run multiple times
6. **Existing items are skipped** - no duplicates created

## Troubleshooting

**"Missing Query Parameter: name"**
- Fixed in v2.0.0 - tags now include name parameter

**"Invalid Object"**
- Check JSON body format in debug output
- Verify API key has correct permissions

**"Object already exists"**
- This is normal - script skips existing objects
- Shows as "Skipped" in statistics

**Tags show "Failed: X"**
- Check firewall logs
- Verify API key permissions
- Try creating one tag manually in firewall UI to test
