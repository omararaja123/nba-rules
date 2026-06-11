#!/bin/bash
# Second cleanup phase: Remove legacy files while keeping essential ones

echo "🧹 Second Cleanup Phase: Removing Legacy Files"
echo "=============================================="
echo ""

# Files to remove
echo "Removing old scripts and temporary files..."
rm -f dry_run_output.txt cleanup_full_run.log 2>/dev/null

# Remove old implementations
rm -f phase1_*.py phase2_*.py phase3_*.py 2>/dev/null
rm -f phase4_evaluate*.py phase4_retrieval_*.py phase4_rag_*.py 2>/dev/null
rm -f extract_pdf.py chunk_rulebook.py create_*.py save_*.py 2>/dev/null
rm -f fix_*.py generate_100_*.py rebuild_*.py implement_*.py 2>/dev/null
rm -f diagnose_retrieval.py evaluate_retrieval.py validate_embeddings.py verify_extraction.py test_env.py compare_*.py 2>/dev/null
rm -f final_optimized_rebuild.py 2>/dev/null

echo "✅ Removed old scripts"
echo ""

# Remove old data versions  
echo "Archiving old chunk/embedding versions..."
mkdir -p _archive_legacy
mv data/09_stable_chunks.json data/09_stable_chunks*.json _archive_legacy/ 2>/dev/null
mv data/09_chunks_index.json data/09_stable_chunks_metadata.csv data/09_stable_chunks.jsonl _archive_legacy/ 2>/dev/null
mv data/10_embeddings.npy data/10_embeddings_*.npy data/10_chunk_id_map.json data/10_embeddings_metadata.json _archive_legacy/ 2>/dev/null
mv data/11_*.json data/11_*.npy _archive_legacy/ 2>/dev/null
mv data/0*.json data/0*.txt _archive_legacy/ 2>/dev/null
mv data/evaluation_*.json data/langgraph_*.json data/phase1_*.json data/validation_report.json data/final_evaluation_results.json _archive_legacy/ 2>/dev/null

echo "✅ Archived old data files"
echo ""

# Keep critical files only
echo "Keeping critical submission files..."
ls -lh phase4_langgraph_rag.py phase4_prompts.py requirements.txt .gitignore README.md FINAL_SUBMISSION_SUMMARY.md 2>/dev/null | awk '{print "  ✓", $9}'

echo ""
echo "✅ Second cleanup complete!"
echo ""
echo "Remaining files in project:"
find . -type f ! -path './.git/*' ! -path './_archive*/*' -name '*.py' -o -name '*.json' -o -name '*.npy' 2>/dev/null | grep -E "^\./(phase|data|final|aggressive|optimize|test_|validate_|generate_)" | wc -l | xargs echo "  Scripts/data files:"

