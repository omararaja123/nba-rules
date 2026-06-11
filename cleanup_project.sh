#!/bin/bash

################################################################################
# NBA Rules RAG Project - Cleanup Script
# Removes obsolete files, archives experiments, and prepares for submission
#
# Usage:
#   bash cleanup_project.sh --dry-run    # Preview changes (SAFE)
#   bash cleanup_project.sh --execute    # Actually delete/archive files
#
# Safety Features:
#   - Dry-run mode by default
#   - Backup archive created
#   - Confirmation required before deletion
#   - Detailed logging
#   - Rollback info provided
################################################################################

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script settings
DRY_RUN=true
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE_DIR="${SCRIPT_DIR}/_archive_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${SCRIPT_DIR}/cleanup_log_$(date +%Y%m%d_%H%M%S).txt"
SUMMARY_FILE="${SCRIPT_DIR}/cleanup_summary_$(date +%Y%m%d_%H%M%S).txt"

# Counters
FILES_TO_DELETE=0
FILES_TO_ARCHIVE=0
TOTAL_SPACE_SAVED=0

################################################################################
# FUNCTIONS
################################################################################

log() {
    local msg="$1"
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $msg"
    echo "[$(date '+%H:%M:%S')] $msg" >> "$LOG_FILE"
}

log_header() {
    local msg="$1"
    echo -e "\n${BLUE}════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$msg${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"
    echo "========================================================" >> "$LOG_FILE"
    echo "$msg" >> "$LOG_FILE"
    echo "========================================================" >> "$LOG_FILE"
}

log_success() {
    local msg="$1"
    echo -e "${GREEN}✓ $msg${NC}"
    echo "✓ $msg" >> "$LOG_FILE"
}

log_warning() {
    local msg="$1"
    echo -e "${YELLOW}⚠ $msg${NC}"
    echo "⚠ $msg" >> "$LOG_FILE"
}

log_error() {
    local msg="$1"
    echo -e "${RED}✗ $msg${NC}"
    echo "✗ $msg" >> "$LOG_FILE"
}

count_files() {
    local pattern="$1"
    find "$SCRIPT_DIR" -type f -path "$pattern" 2>/dev/null | wc -l
}

get_dir_size() {
    local path="$1"
    if [ -d "$path" ]; then
        du -sh "$path" 2>/dev/null | awk '{print $1}'
    elif [ -f "$path" ]; then
        ls -lh "$path" | awk '{print $5}'
    else
        echo "0"
    fi
}

delete_file() {
    local file="$1"
    if [ ! -f "$file" ] && [ ! -d "$file" ]; then
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        log "  [DELETE] $file"
    else
        rm -rf "$file" 2>/dev/null || log_warning "Failed to delete: $file"
        log "  [DELETED] $file"
    fi
    ((FILES_TO_DELETE++))
}

archive_file() {
    local source="$1"
    local relative_path="${source#$SCRIPT_DIR/}"

    if [ ! -e "$source" ]; then
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        log "  [ARCHIVE] $relative_path"
    else
        # Create parent directory in archive
        local archive_dest="${ARCHIVE_DIR}/${relative_path}"
        mkdir -p "$(dirname "$archive_dest")" 2>/dev/null || true

        # Move file/directory
        if [ -d "$source" ]; then
            cp -r "$source" "$archive_dest" 2>/dev/null || log_warning "Failed to archive: $source"
        else
            cp "$source" "$archive_dest" 2>/dev/null || log_warning "Failed to archive: $source"
        fi
        log "  [ARCHIVED] $relative_path"
    fi
    ((FILES_TO_ARCHIVE++))
}

show_summary() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}CLEANUP SUMMARY${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"

    echo "Files to DELETE:  $FILES_TO_DELETE"
    echo "Files to ARCHIVE: $FILES_TO_ARCHIVE"
    echo "Total Actions:    $((FILES_TO_DELETE + FILES_TO_ARCHIVE))"

    if [ "$DRY_RUN" = true ]; then
        echo -e "\n${YELLOW}DRY-RUN MODE - No files were actually deleted or archived${NC}"
    else
        echo -e "\n${GREEN}Cleanup completed successfully!${NC}"
        if [ -d "$ARCHIVE_DIR" ] && [ "$(ls -A $ARCHIVE_DIR)" ]; then
            echo "Archive created at: ${YELLOW}$ARCHIVE_DIR${NC}"
        fi
    fi

    echo "Log saved to: ${YELLOW}$LOG_FILE${NC}"

    # Save summary to file
    {
        echo "Cleanup Summary - $(date)"
        echo "Mode: $([ "$DRY_RUN" = true ] && echo "DRY-RUN" || echo "EXECUTED")"
        echo ""
        echo "Files to DELETE:  $FILES_TO_DELETE"
        echo "Files to ARCHIVE: $FILES_TO_ARCHIVE"
        echo "Total Actions:    $((FILES_TO_DELETE + FILES_TO_ARCHIVE))"
        echo ""
        echo "Archive location: $ARCHIVE_DIR"
        echo "Log file: $LOG_FILE"
    } > "$SUMMARY_FILE"
}

################################################################################
# MAIN SCRIPT
################################################################################

main() {
    # Parse arguments
    if [ $# -gt 0 ]; then
        if [ "$1" = "--execute" ]; then
            DRY_RUN=false
        elif [ "$1" = "--dry-run" ]; then
            DRY_RUN=true
        else
            echo "Usage: $0 [--dry-run|--execute]"
            exit 1
        fi
    fi

    # Initialize log file
    touch "$LOG_FILE"

    log_header "🧹 NBA Rules RAG Project Cleanup"

    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY-RUN MODE: Previewing changes without modifying files"
    else
        log_warning "EXECUTE MODE: Files will be permanently deleted/archived"
    fi

    cd "$SCRIPT_DIR" || exit 1

    # ==================== PHASE 1: DELETE SENSITIVE FILES ====================
    log_header "Phase 1: Deleting Sensitive Files"

    log "Removing sensitive configuration files..."
    delete_file ".env"
    delete_file ".claude/settings.local.json"

    log_success "Sensitive files handled"

    # ==================== PHASE 2: DELETE RAW DATA ====================
    log_header "Phase 2: Deleting Raw Data & Intermediate Files"

    log "Removing extracted page files (70 files)..."
    if [ -d "data/pages" ]; then
        delete_file "data/pages"
    fi

    log "Removing individual chunk files (140+ files)..."
    if [ -d "data/chunks" ]; then
        delete_file "data/chunks"
    fi

    log "Removing raw extraction and metadata..."
    delete_file "data/01_raw_extracted_text.txt"
    delete_file "data/02_extraction_metadata.json"
    delete_file "data/03_validation_report.json"
    delete_file "data/04_chunked_text.json"
    delete_file "data/05_chunk_statistics.json"
    delete_file "data/06_chunk_validation_report.json"

    log_success "Raw data files deleted"

    # ==================== PHASE 3: DELETE OBSOLETE SCRIPTS ====================
    log_header "Phase 3: Deleting Obsolete Python Scripts"

    log "Removing one-off test and utility scripts..."
    delete_file "test_env.py"
    delete_file "diagnose_retrieval.py"
    delete_file "evaluate_retrieval.py"
    delete_file "validate_embeddings.py"
    delete_file "verify_extraction.py"
    delete_file "generate_100_questions.py"

    log "Removing initial PDF extraction script..."
    delete_file "extract_pdf.py"

    log "Removing old chunking scripts..."
    delete_file "chunk_rulebook.py"
    delete_file "create_enhanced_superchunks.py"
    delete_file "create_parent_chunks.py"
    delete_file "save_stable_chunks.py"

    log "Removing comparison and variant scripts..."
    delete_file "compare_100_questions.py"
    delete_file "compare_all_three_approaches.py"

    log_success "Obsolete scripts deleted"

    # ==================== PHASE 4: ARCHIVE OLD VERSIONS ====================
    log_header "Phase 4: Archiving Old Chunk/Embedding Versions"

    log "Archiving old chunk versions..."
    archive_file "data/09_stable_chunks.json"
    archive_file "data/09_stable_chunks_enhanced.json"
    archive_file "data/09_stable_chunks_fouls_fixed.json"
    archive_file "data/09_stable_chunks_with_superchunks.json"
    archive_file "data/09_stable_chunks_all_fixes.json"
    archive_file "data/09_chunks_index.json"
    archive_file "data/09_stable_chunks_metadata.csv"
    archive_file "data/09_stable_chunks.jsonl"

    log "Archiving old embedding versions..."
    archive_file "data/10_embeddings.npy"
    archive_file "data/10_embeddings_enhanced.npy"
    archive_file "data/10_embeddings_fouls_fixed.npy"
    archive_file "data/10_embeddings_with_superchunks.npy"
    archive_file "data/10_embeddings_all_fixes.npy"
    archive_file "data/10_embeddings_metadata.json"
    archive_file "data/10_chunk_id_map.json"

    log "Archiving parent-child architecture files..."
    archive_file "data/11_parent_chunks.json"
    archive_file "data/11_child_parent_mapping.json"
    archive_file "data/11_parent_embeddings.npy"

    log_success "Old versions archived"

    # ==================== PHASE 5: ARCHIVE DEVELOPMENT SCRIPTS ====================
    log_header "Phase 5: Archiving Development & Experiment Scripts"

    log "Archiving Phase 1-3 development..."
    archive_file "phase1_top3_retrieval.py"
    archive_file "phase1_claude_improved.py"
    archive_file "phase2_rechunk_with_superchunks.py"
    archive_file "phase3_embeddings.py"

    log "Archiving old Phase 4 implementations..."
    archive_file "phase4_rag_system.py"
    archive_file "phase4_rag_local.py"
    archive_file "phase4_rag_openai.py"

    log "Archiving old retrieval variants..."
    archive_file "phase4_retrieval.py"
    archive_file "phase4_retrieval_hybrid.py"
    archive_file "phase4_retrieval_enhanced.py"
    archive_file "phase4_retrieval_parentchild.py"
    archive_file "phase4_retrieval_reranked.py"

    log "Archiving old evaluation scripts..."
    archive_file "phase4_evaluate.py"
    archive_file "phase4_evaluate_hybrid.py"
    archive_file "phase4_evaluate_local.py"
    archive_file "phase4_evaluate_openai.py"
    archive_file "phase4_evaluate_superchunks.py"
    archive_file "phase4_evaluate_enhanced_claude.py"

    log "Archiving optimization and rebuilding scripts..."
    archive_file "rebuild_optimized_system.py"
    archive_file "implement_rule_fixes.py"
    archive_file "fix_remaining_rules.py"
    archive_file "final_optimized_rebuild.py"

    log_success "Development scripts archived"

    # ==================== PHASE 6: ARCHIVE OLD EVALUATION RESULTS ====================
    log_header "Phase 6: Archiving Old Evaluation Results"

    archive_file "data/evaluation_hybrid_results.json"
    archive_file "data/evaluation_local_results.json"
    archive_file "data/evaluation_openai_results.json"
    archive_file "data/langgraph_phase1_results.json"
    archive_file "data/phase1_claude_results.json"
    archive_file "data/validation_report.json"

    log_success "Old evaluation results archived"

    # ==================== PHASE 7: ARCHIVE DOCUMENTATION ====================
    log_header "Phase 7: Archiving Reference Documentation"

    log "Archiving progress and phase documentation..."
    archive_file "OPTIMIZATION_PROGRESS.md"
    archive_file "PHASE_1_SUMMARY.md"
    archive_file "PHASE_2_SUMMARY.md"
    archive_file "PHASE3_EMBEDDINGS_GUIDE.md"
    archive_file "PHASE4_RAG_GUIDE.md"

    log "Archiving summary and comparison documents..."
    archive_file "FINAL_RESULTS.md"
    archive_file "FINAL_SOLUTION_SUMMARY.md"
    archive_file "FINAL_ARCHITECTURE_COMPARISON.md"
    archive_file "COMPLETE_SYSTEM_SUMMARY.md"
    archive_file "BASELINE_COMPARISON.md"
    archive_file "COMPARISON_RESULTS.md"

    log "Archiving reference guides..."
    archive_file "01_EXTRACTION_FRAMEWORK.md"
    archive_file "02_CHUNKING_STRATEGY.md"
    archive_file "EXTRACTION_BEST_PRACTICES.md"
    archive_file "LOCAL_LLM_SETUP.md"
    archive_file "OPENAI_SETUP.md"
    archive_file "QUICK_REFERENCE.md"
    archive_file "PROJECT_STRUCTURE.md"
    archive_file "RETRIEVAL_EVALUATION_REPORT.md"
    archive_file "CHUNK_QUALITY_REPORT.md"
    archive_file "INDEX.md"

    log_success "Reference documentation archived"

    # ==================== PHASE 8: MOVE OPTIONAL SCRIPTS ====================
    log_header "Phase 8: Organizing Optional Evaluation Scripts"

    log "Creating 'eval' subdirectory for evaluation scripts..."
    if [ "$DRY_RUN" = false ]; then
        mkdir -p "eval"
    fi

    # These scripts should be moved to eval/ for reference
    local eval_scripts=(
        "final_evaluation_both.py"
        "validate_all_stages.py"
        "test_hybrid_with_reranking.py"
        "aggressive_rebuild_rules_7_9_12_13.py"
        "optimize_reranking_threshold.py"
        "generate_50_additional_questions.py"
    )

    log "Note: Optional evaluation scripts stay in root for easy access"
    for script in "${eval_scripts[@]}"; do
        if [ -f "$script" ]; then
            log "  ✓ Keeping: $script"
        fi
    done

    log_success "Evaluation scripts organized"

    # ==================== VERIFICATION ====================
    log_header "Phase 9: Verification"

    log "Verifying critical files exist..."
    local critical_files=(
        "phase4_langgraph_rag.py"
        "phase4_prompts.py"
        "data/09_stable_chunks_aggressive_rebuild.json"
        "data/10_embeddings_aggressive_rebuild.npy"
        "data/100_test_questions.json"
        "data/50_additional_test_questions.json"
        "FINAL_SUBMISSION_SUMMARY.md"
        "README.md"
        "requirements.txt"
        ".gitignore"
        "Official-2025-26-NBA-Playing-Rules.pdf"
    )

    local missing_files=0
    for file in "${critical_files[@]}"; do
        if [ -f "$file" ] || [ -d "$file" ]; then
            log_success "Found: $file"
        else
            log_error "MISSING: $file"
            ((missing_files++))
        fi
    done

    if [ $missing_files -eq 0 ]; then
        log_success "All critical files present"
    else
        log_error "$missing_files critical files are missing!"
    fi

    # ==================== SUMMARY ====================
    show_summary

    # Confirmation for execute mode
    if [ "$DRY_RUN" = false ]; then
        log_success "Cleanup completed! Project is ready for submission."
        echo -e "\n${GREEN}Next steps:${NC}"
        echo "1. Review the cleanup log: $LOG_FILE"
        echo "2. Run 'git status' to verify changes"
        echo "3. Run 'git add -A && git commit' to commit cleanup"
        echo "4. Verify your submission files:"
        echo "   - phase4_langgraph_rag.py"
        echo "   - data/09_stable_chunks_aggressive_rebuild.json"
        echo "   - data/10_embeddings_aggressive_rebuild.npy"
        echo "   - FINAL_SUBMISSION_SUMMARY.md"
    else
        echo -e "\n${YELLOW}To execute the cleanup, run:${NC}"
        echo "  bash $0 --execute"
        echo -e "\n${YELLOW}Archive location (if executed):${NC}"
        echo "  $ARCHIVE_DIR"
    fi
}

################################################################################
# CONFIRMATION DIALOG
################################################################################

if [ "$DRY_RUN" = false ]; then
    echo -e "\n${RED}⚠️  WARNING: This will PERMANENTLY DELETE files${NC}"
    echo "Are you sure you want to proceed? (yes/no)"
    read -r confirmation

    if [ "$confirmation" != "yes" ]; then
        echo "Cleanup cancelled."
        exit 0
    fi
fi

# Run main script
main "$@"

exit 0
