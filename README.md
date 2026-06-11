# NBA Rulebook RAG Pipeline
## A Production-Grade Retrieval-Augmented Generation System for Strategic Rule Analysis

**Status**: Phase 1 (Document Extraction) ✅ Complete | Ready for Phase 2 (Chunking)

---

## Overview

This project builds a RAG system to analyze the NBA rulebook and identify strategic opportunities, underutilized rules, and edge cases—similar to how elite players study rules for competitive advantage.

**Key Features**:
- Structured pipeline from PDF extraction through LLM generation
- Production-quality validation and error handling
- Full citation tracking back to source document
- Measurable quality metrics at each phase
- Emphasis on reproducibility and documentation

---

## Quick Start

### Phase 1: Document Extraction (✅ COMPLETE)

Extract and validate the NBA rulebook:

```bash
# Install dependencies
pip install -r requirements.txt

# Run extraction
python3 extract_pdf.py

# Verify outputs
ls -lh data/
```

**Outputs**:
- `data/01_raw_extracted_text.txt` — Clean, full rulebook text (211 KB)
- `data/02_extraction_metadata.json` — Page-level metadata for citations
- `data/03_validation_report.json` — Quality assurance results
- `data/pages/` — Individual page files for debugging

**Validation Results**:
```
Overall Status: PASS ✅
- Completeness: 71/71 pages extracted (signal diagrams removed)
- Quality: All checks pass
- Content Volume: Avg 2,976 chars/page ✅
- Structure: Rule numbers and sections preserved ✅
```

### Phase 2: Chunking Strategy (NEXT)

See `02_chunking_strategy.md` (coming soon)

### Phase 3: Embedding (THEN)

See `03_embedding_strategy.md` (coming soon)

---

## Documentation Structure

```
Project Root
├── README.md (this file)
├── requirements.txt (Python dependencies)
├── extract_pdf.py (Phase 1 extraction code)
│
├── DOCS/
│   ├── 01_EXTRACTION_FRAMEWORK.md - Why we chose this approach
│   ├── PROJECT_STRUCTURE.md - How outputs fit together
│   ├── EXTRACTION_BEST_PRACTICES.md - Deep dive into decisions & tradeoffs
│   ├── 02_CHUNKING_STRATEGY.md (planned)
│   ├── 03_EMBEDDING_STRATEGY.md (planned)
│   └── 04_RETRIEVAL_STRATEGY.md (planned)
│
├── data/
│   ├── 01_raw_extracted_text.txt ✅
│   ├── 02_extraction_metadata.json ✅
│   ├── 03_validation_report.json ✅
│   ├── pages/ (individual page files) ✅
│   ├── 04_chunked_text.json (Phase 2)
│   ├── 05_chunk_metadata.json (Phase 2)
│   ├── 06_embeddings.h5 (Phase 3)
│   └── 08_retrieval_index.db (Phase 4)
│
└── notebooks/ (Jupyter analysis)
    ├── 01_extraction_analysis.ipynb
    └── 02_quality_validation.ipynb
```

---

## Phase 1: Document Extraction Complete ✅

### What Was Done

1. **PDF Parsing**
   - Library: PyMuPDF (fitz)
   - Approach: Page-by-page text extraction
   - Result: 211,315 characters of clean text

2. **Cleaning**
   - Removed headers, footers, page numbers
   - Preserved rule structure (rule numbers, sections)
   - Detected and removed OCR artifacts (none found)

3. **Validation**
   - Verified all 71 pages extracted
   - Checked for encoding errors (none)
   - Confirmed content volume reasonable
   - Detected structure markers (rule numbers, sections)

4. **Metadata Generation**
   - Created page-level index for citations
   - Saved individual page files for debugging
   - Stored extraction timestamp and statistics

### Key Decisions Made

| Decision | Choice | Why | Impact |
|----------|--------|-----|--------|
| **Library** | PyMuPDF | Fast, handles text-based PDFs well | Can't change without re-extracting |
| **Extraction Method** | `get_text(option="text")` | Simple, sufficient for rules | Downstream phases inherit this choice |
| **Header/Footer Removal** | Pattern detection + regex | Automatic, generalizable | Cleaner chunks, better embeddings |
| **Citation Tracking** | Page-level metadata | Enable precise document references | Phase 4 can cite exact pages |
| **Validation** | 4-point framework | Comprehensive quality checks | Confidence in downstream work |

### Quality Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Pages Extracted | 76 | 76 | ✅ PASS |
| Content Volume (avg) | >500 chars | 2,798 chars | ✅ PASS |
| Quality Issues | 0-1 | 1 (expected) | ✅ PASS |
| Structure Preserved | Yes | Yes (rule numbers, sections) | ✅ PASS |
| OCR Artifacts | None | None | ✅ PASS |

---

## How to Inspect the Results

### View Extracted Text

```bash
# First 50 lines (table of contents)
head -50 data/01_raw_extracted_text.txt

# Search for a specific rule
grep -n "RULE NO. 2" data/01_raw_extracted_text.txt

# View a specific page
cat data/pages/page_010.txt
```

### Check Validation Report

```bash
# Pretty-print JSON
cat data/03_validation_report.json | python3 -m json.tool

# Check for quality issues
cat data/03_validation_report.json | jq '.checks.quality'
```

### Verify No Headers/Footers

```bash
# Search for repeated "PAGE" string (should be minimal)
grep -c "PAGE" data/01_raw_extracted_text.txt

# Look for page number patterns
grep -E "^[-\s]*[0-9]+[-\s]*$" data/01_raw_extracted_text.txt | head

# Should output: (empty or very few results)
```

---

## Design Decisions & Tradeoffs

### Why PyMuPDF Instead of Alternatives?

| Alternative | Tradeoff |
|-------------|----------|
| **pdfplumber** | Better table support, but 3-5x slower. Not needed for prose-heavy rulebook. |
| **pypdf** | Pure Python (no C deps), but weaker text ordering on complex layouts. |
| **pdfminer.six** | Academic tool, overkill for this use case, very slow. |
| **Tesseract OCR** | Only needed for scanned PDFs; your rulebook is text-based. |

**Our choice**: PyMuPDF is 80/20—fast enough, good enough, simple.

### Why Preserve Structure?

Keeping rule numbers, section headers, and numbering:
- **Benefit**: Phase 2 can chunk hierarchically (rule → section → content)
- **Benefit**: Phase 4 can cite exact rule section (e.g., "Rule 4, Section III, part (d)")
- **Cost**: None (we can always flatten structure later if needed)
- **Trade-off**: Favors citation accuracy over simplicity

### Why Remove Headers/Footers?

Headers and footers repeated 76 times:
- **Benefit**: Cleaner chunks, better embeddings, smaller storage
- **Benefit**: Reduce noise in retrieval ranking
- **Cost**: Can't recover removed text
- **Trade-off**: Irreversible, but safe (headers add no semantic value)

---

## Downstream Implications

### For Phase 2: Chunking

**Input**: `01_raw_extracted_text.txt` (full text with structure)

**Key Questions Phase 2 Will Answer**:
1. How large should chunks be? (tokens, characters?)
2. Should chunks overlap?
3. Should we chunk hierarchically (rule → section)?
4. What metadata to attach to each chunk?

**Benefit of Phase 1 Decisions**: Clear structure makes these questions answerable.

### For Phase 3: Embedding

**Input**: Chunks from Phase 2 (with metadata)

**Key Questions Phase 3 Will Answer**:
1. Which embedding model? (OpenAI, local open-source?)
2. Should metadata be embedded separately?
3. How to handle long documents (>512 tokens)?

**Benefit of Phase 1 Decisions**: No wasted tokens on headers/footers.

### For Phase 4: Retrieval

**Input**: Vectors from Phase 3 (with chunk metadata)

**Key Questions Phase 4 Will Answer**:
1. Semantic search only, or hybrid (semantic + keyword)?
2. How many results to retrieve?
3. How to rerank results?

**Benefit of Phase 1 Decisions**: Metadata enables precise citations ("Rule 2, Section I, page 10").

---

## Known Limitations

### What Extraction DOES NOT Handle

- ❌ Scanned PDFs (images instead of text)
- ❌ Complex multi-column layouts (may merge columns)
- ❌ Tables with detailed structure (converted to plain text)
- ❌ Handwritten notes or annotations
- ❌ Embedded images or diagrams (text extraction only)

### For Your NBA Rulebook

✅ None of the above limitations apply—rulebook is clean, text-based, well-structured.

### What to Check Manually

If you ever update the PDF:
1. Verify no pages are blank/missing
2. Check that rule numbers are still present
3. Spot-check table content for readability
4. Confirm no OCR artifacts (if PDF changes format)

---

## Next Steps

### Immediate (Before Phase 2)

1. ✅ **Extract**: Done—all 71 pages extracted and validated
2. ✅ **Validate**: Done—quality checks passed
3. ✅ **Document**: Done—framework, structure, best practices documented

### Phase 2: Chunking Strategy

Next, you'll decide:
1. Chunk size (e.g., 512 tokens, 1024 tokens?)
2. Overlap (e.g., 20% overlap between chunks?)
3. Hierarchical chunking (rule → section → content)?
4. Metadata attachment (section number, page number, etc.)

See `02_chunking_strategy.md` when ready.

### Phase 3-5: Embedding, Retrieval, Generation

Coming next: Full guidance on embedding models, retrieval strategies, and LLM integration.

---

## Reference: Complete RAG Pipeline

```
┌──────────────────────────────────────────────────────┐
│     NBA Rulebook RAG Pipeline: Full Architecture     │
├──────────────────────────────────────────────────────┤
│                                                       │
│  INPUT: Official-2025-26-NBA-Playing-Rules.pdf      │
│           ↓                                           │
│  PHASE 1: Extraction ✅                              │
│  ├─ PyMuPDF: Extract text from 71 pages             │
│  ├─ Clean: Remove headers, footers, artifacts       │
│  ├─ Validate: Quality checks (4-point framework)    │
│  └─ Output: 01_raw_extracted_text.txt (212 KB)     │
│           ↓                                           │
│  PHASE 2: Chunking (planned)                        │
│  ├─ Strategy: Semantic chunking with metadata       │
│  ├─ Size: TBD (goal: ~512-1024 tokens)             │
│  ├─ Overlap: TBD (goal: ~20%)                       │
│  └─ Output: 04_chunked_text.json                    │
│           ↓                                           │
│  PHASE 3: Embedding (planned)                       │
│  ├─ Model: TBD (OpenAI, Ollama, SentenceTransformers) │
│  ├─ Dimension: TBD (typically 768-1536)            │
│  └─ Output: 06_embeddings.h5                        │
│           ↓                                           │
│  PHASE 4: Retrieval (planned)                       │
│  ├─ Database: TBD (Weaviate, Milvus, Pinecone)    │
│  ├─ Search: Semantic + keyword hybrid               │
│  ├─ Reranking: Cross-encoder                        │
│  └─ Output: Top-k relevant chunks                   │
│           ↓                                           │
│  PHASE 5: Generation (planned)                      │
│  ├─ LLM: TBD (Claude, GPT-4, local model)          │
│  ├─ Prompt: Rule-aware generation                   │
│  ├─ Citation: Map back to page numbers              │
│  └─ Output: Answer with source citations            │
│           ↓                                           │
│  EVALUATION: Metrics (planned)                      │
│  ├─ Retrieval accuracy (NDCG, MAP, MRR)            │
│  ├─ Citation accuracy (can we verify claims?)      │
│  ├─ Hallucination rate (false claims?)              │
│  └─ Strategic usefulness (does it find loopholes?)  │
│                                                       │
│  OUTPUT: Strategic rule insights + citations        │
│           ↓                                           │
│  APPLICATION: Competitive advantage discovery      │
│                                                       │
└──────────────────────────────────────────────────────┘
```

---

## Questions?

Each phase of the pipeline has dedicated documentation:

- **Phase 1 (Extraction)**: This README + `01_EXTRACTION_FRAMEWORK.md` + `EXTRACTION_BEST_PRACTICES.md`
- **Phase 2 (Chunking)**: See `02_chunking_strategy.md`
- **Phase 3 (Embedding)**: See `03_embedding_strategy.md`
- **Phase 4 (Retrieval)**: See `04_retrieval_strategy.md`
- **Phase 5 (Generation)**: See `05_generation_strategy.md`
- **Evaluation**: See `06_evaluation_framework.md`

Start with `PROJECT_STRUCTURE.md` for an overview of how all phases connect.

---

## Project Metadata

- **Source Document**: Official NBA Playing Rules 2025-26
- **Extraction Date**: 2026-06-10
- **Pages**: 76
- **Content Size**: 211,315 characters
- **Format**: Plain text with structure preserved
- **Status**: Phase 1 Complete ✅

---

**Ready to proceed to Phase 2 (Chunking)? Review the extracted text and validation report, then move to `02_chunking_strategy.md`.**

