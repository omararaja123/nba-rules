# 🧹 Project Cleanup Guide

## Quick Start

### Step 1: Preview Changes (SAFE - No files modified)
```bash
cd /Users/omar/Documents/Claude-Vibe-Code/nba-rules
bash cleanup_project.sh --dry-run
```

This will show you exactly what will be deleted/archived **without making any changes**.

### Step 2: Review Output
The script will:
- Show all files to be deleted
- Show all files to be archived
- Generate a detailed log
- Create a summary report

**Files you'll see marked:**
- `[DELETE]` - Files that will be permanently removed
- `[ARCHIVE]` - Files that will be backed up

### Step 3: Execute Cleanup (Permanent)
```bash
bash cleanup_project.sh --execute
```

**You'll need to confirm:**
```
⚠️  WARNING: This will PERMANENTLY DELETE files
Are you sure you want to proceed? (yes/no)
```

Type `yes` to confirm.

---

## What Gets Deleted

### Sensitive Files (CRITICAL)
- ❌ `.env` - API keys and secrets
- ❌ `.claude/settings.local.json` - Local settings

### Raw Data (Can be recreated)
- ❌ `data/pages/` - 70 extracted PDF page files
- ❌ `data/chunks/` - 140+ individual chunk text files
- ❌ Raw extraction metadata and intermediate formats

### Obsolete Scripts
- ❌ One-off test scripts
- ❌ Old PDF extraction tools
- ❌ Debugging utilities
- ❌ Comparison scripts

---

## What Gets Archived

### Old Versions (Kept in backup)
- 📦 `data/09_stable_chunks_*.json` (except aggressive_rebuild)
- 📦 `data/10_embeddings_*.npy` (except aggressive_rebuild)
- 📦 `data/11_*` (parent-child approach files)

### Development Scripts (Kept in backup)
- 📦 `phase1_*.py`, `phase2_*.py`, `phase3_*.py` - Phase implementations
- 📦 `phase4_evaluate*.py` - Old evaluation scripts
- 📦 `phase4_retrieval_*.py` - Old retrieval variants
- 📦 Optimization and rebuilding scripts

### Documentation (Kept in backup)
- 📦 Progress tracking documents
- 📦 Phase summaries and guides
- 📦 Architecture comparisons
- 📦 Reference documentation

---

## What Gets Kept

### ✅ Essential Files (In root)
```
phase4_langgraph_rag.py           # Main RAG system
phase4_prompts.py                 # Prompts
README.md                         # Documentation
requirements.txt                  # Dependencies
FINAL_SUBMISSION_SUMMARY.md       # Results
.gitignore                        # Git config
Official-2025-26-NBA-Playing-Rules.pdf  # Source
```

### ✅ Data Files (In data/)
```
data/09_stable_chunks_aggressive_rebuild.json     # Final chunks
data/10_embeddings_aggressive_rebuild.npy         # Final embeddings
data/100_test_questions.json                      # Test benchmark
data/50_additional_test_questions.json            # Validation set
```

### ✅ Optional Evaluation Scripts (In root - for reference)
```
final_evaluation_both.py                          # Evaluation methodology
validate_all_stages.py                            # Validation pipeline
test_hybrid_with_reranking.py                    # Testing approach
aggressive_rebuild_rules_7_9_12_13.py            # Optimization demo
optimize_reranking_threshold.py                  # Tuning approach
generate_50_additional_questions.py              # Robustness testing
```

---

## Output Files

After running the script, you'll get:

### 📋 Log Files
```
cleanup_log_YYYYMMDD_HHMMSS.txt     # Detailed operation log
cleanup_summary_YYYYMMDD_HHMMSS.txt # Quick summary
```

### 📦 Archive (if using --execute)
```
_archive_YYYYMMDD_HHMMSS/           # Backup of archived files
├── data/09_stable_chunks_*.json
├── data/10_embeddings_*.npy
├── data/11_*
├── phase1_*.py
├── phase4_evaluate*.py
└── ... (all archived files)
```

**Keep this archive** - it contains your entire development history.

---

## Safety Features

### 🔒 Built-in Protections

1. **Dry-run by default** - Running without flags shows what WOULD happen
2. **Explicit --execute flag** - Must explicitly request permanent deletion
3. **Confirmation prompt** - Must type "yes" to proceed
4. **Automatic backup** - Archive created before any deletion
5. **Detailed logging** - Every action logged and timestamped
6. **Verification** - Checks critical files still exist after cleanup

### 🔄 Rollback

If something goes wrong:

```bash
# Restore from archive
cp -r _archive_YYYYMMDD_HHMMSS/* .
```

Or simply restore from git:

```bash
git checkout HEAD -- <file>
```

---

## Example Run

### Dry-run Output
```
════════════════════════════════════════════════════════
🧹 NBA Rules RAG Project Cleanup
════════════════════════════════════════════════════════

[21:15:32] DRY-RUN MODE: Previewing changes without modifying files

════════════════════════════════════════════════════════
Phase 1: Deleting Sensitive Files
════════════════════════════════════════════════════════

[21:15:32] Removing sensitive configuration files...
[21:15:32]   [DELETE] .env
[21:15:32]   [DELETE] .claude/settings.local.json
[21:15:33] ✓ Sensitive files handled

... (more phases)

════════════════════════════════════════════════════════
CLEANUP SUMMARY
════════════════════════════════════════════════════════

Files to DELETE:  45
Files to ARCHIVE: 180
Total Actions:    225

⚠ DRY-RUN MODE - No files were actually deleted or archived

Log saved to: cleanup_log_20260610_211533.txt
```

### Then Execute
```bash
bash cleanup_project.sh --execute
# Type: yes
# Cleanup proceeds...
```

---

## Command Reference

```bash
# Preview changes (safe)
bash cleanup_project.sh --dry-run

# Execute cleanup (requires confirmation)
bash cleanup_project.sh --execute

# View help
bash cleanup_project.sh --help
```

---

## Verification Checklist

After cleanup, verify:

```bash
# 1. Check critical files exist
ls -lh phase4_langgraph_rag.py
ls -lh data/09_stable_chunks_aggressive_rebuild.json
ls -lh data/10_embeddings_aggressive_rebuild.npy
ls -lh FINAL_SUBMISSION_SUMMARY.md

# 2. Check no sensitive files remain
ls -la | grep "\.env"
ls -la | grep "\.claude"

# 3. Check optional scripts
ls -lh final_evaluation_both.py

# 4. Verify git status
git status

# 5. Count remaining files
find . -type f ! -path './.git/*' | wc -l
```

---

## Before & After

### Before Cleanup
- 📊 ~300+ files
- 💾 ~1.5GB total
- 🐍 40+ Python scripts
- 📁 150+ data files
- 📚 20+ documentation files

### After Cleanup
- 📊 ~20 files
- 💾 ~50MB total
- 🐍 8 Python scripts
- 📁 4 data files
- 📚 2 documentation files

---

## Common Issues & Solutions

### Issue: "Permission denied"
```bash
# Fix: Make script executable
chmod +x cleanup_project.sh
```

### Issue: "File not found"
```bash
# This is OK in dry-run mode - means file already doesn't exist
# In execute mode, it's safely skipped
```

### Issue: "Archive directory not created"
```bash
# Create manually if needed
mkdir -p _archive_$(date +%Y%m%d_%H%M%S)
```

### Issue: Want to keep a specific file?
```bash
# Edit the script and comment out (or remove) its delete_file or archive_file line
# Search for the filename and remove that section
```

---

## Next Steps After Cleanup

1. ✅ Run `git status` to see changes
2. ✅ Review the cleanup log
3. ✅ Add cleanup to git:
   ```bash
   git add -A
   git commit -m "chore: cleanup project for submission"
   ```
4. ✅ Verify final structure:
   ```bash
   tree -L 2 -I '__pycache__|*.pyc|_archive*'
   ```
5. ✅ Push to GitHub:
   ```bash
   git push origin main
   ```

---

## Questions?

- **What should I keep?** - See "What Gets Kept" section
- **Can I undo this?** - Yes, restore from `_archive_*` folder or git
- **Should I run this?** - YES! Clean projects are better for submission
- **Will it break anything?** - No, all essential files are kept

---

**Ready? Run: `bash cleanup_project.sh --dry-run`**
