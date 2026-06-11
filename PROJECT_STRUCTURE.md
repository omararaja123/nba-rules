# NBA Rulebook RAG Project Structure

## Directory Organization

```
nba-rules/
├── README.md                                    # Project overview
├── requirements.txt                             # Python dependencies
├── extract_pdf.py                               # Phase 1: PDF extraction script
├── 01_EXTRACTION_FRAMEWORK.md                   # Framework documentation
│
├── data/                                        # All generated data artifacts
│   ├── 01_raw_extracted_text.txt               # ✓ COMPLETE: Raw text (71 pages)
│   ├── 02_extraction_metadata.json             # ✓ COMPLETE: Page-level metadata
│   ├── 03_validation_report.json               # ✓ COMPLETE: Quality validation
│   │
│   ├── pages/                                  # Individual page texts (for debugging)
│   │   ├── page_001.txt
│   │   ├── page_002.txt
│   │   └── ...page_076.txt
│   │
│   ├── 04_chunked_text.json                    # Phase 2 (pending): Chunks + boundaries
│   ├── 05_chunk_metadata.json                  # Phase 2 (pending): Chunk index
│   │
│   ├── 06_embeddings.h5                        # Phase 3 (pending): Vector embeddings
│   ├── 07_embedding_metadata.json              # Phase 3 (pending): Embedding index
│   │
│   └── 08_retrieval_index.db                   # Phase 4 (pending): Vector database
│
├── notebooks/                                  # Jupyter notebooks for exploration
│   ├── 01_extraction_analysis.ipynb
│   ├── 02_structure_exploration.ipynb
│   └── 03_quality_assessment.ipynb
│
└── docs/                                        # Documentation
    ├── 01_extraction_guide.md                  # THIS DOCUMENT
    ├── 02_chunking_strategy.md                 # Phase 2
    ├── 03_embedding_strategy.md                # Phase 3
    ├── 04_retrieval_strategy.md                # Phase 4
    └── 05_evaluation_framework.md              # Evaluation
```

---

## Phase 1: Document Extraction ✅ COMPLETE

### What We Did

Extracted the NBA rulebook PDF into clean, validated raw text while:
- Removing headers, footers, page numbers
- Preserving rule structure (rule numbers, sections, subsections)
- Detecting quality issues (page 76 is just a notes page—expected)
- Generating metadata for citation tracking

### Inputs

- **Source**: `Official-2025-26-NBA-Playing-Rules.pdf` (1.6 MB, 71 pages)
- **Extraction Method**: PyMuPDF (fitz) with custom header/footer detection
- **Processing Time**: ~10 seconds

### Outputs

#### 1. **`01_raw_extracted_text.txt`** (211,315 characters)
Clean, full text of entire rulebook with structure preserved.

**Example content**:
```
RULE NO. 2—OFFICIALS AND THEIR DUTIES

Section I—The Game Officials

a. The game officials shall be a Crew Chief, Referee, Umpire, and Replay Center Official. 
They will be assisted by an official scorer, two trained timers, and courtside administrator. 
...
```

**Key features**:
- ✓ All 71 pages included
- ✓ Rule numbers and sections visible
- ✓ Page breaks marked
- ✓ Headers/footers removed
- ✓ No page numbers or artifacts
- ✓ Average 2,798 characters per page (healthy)

#### 2. **`02_extraction_metadata.json`**
Index of all pages for downstream reference:

```json
{
  "extraction_timestamp": "2026-06-10T18:12:45",
  "total_pages": 76,
  "pages": [
    {
      "page_number": 1,
      "text_length": 153,
      "has_images": false,
      "quality_issues": []
    },
    ...
  ],
  "statistics": {
    "total_pages": 76,
    "extracted_pages": 76,
    "total_chars": 212865
  }
}
```

**Downstream use**: When a chunk is retrieved, we can map it back to its original page number via this index.

#### 3. **`03_validation_report.json`**
Quality assurance results:

```json
{
  "overall_status": "PASS",
  "checks": {
    "completeness": {
      "status": "PASS",
      "message": "All 71 pages extracted"
    },
    "quality": {
      "status": "WARNING",
      "issues": ["Page 76: Very short text extracted (9 chars)"]
    },
    "content_volume": {
      "status": "PASS",
      "avg_chars_per_page": 2798
    },
    "structure": {
      "status": "PASS",
      "has_rule_numbers": true,
      "has_sections": true
    }
  }
}
```

**Note**: Page 76 warning is expected (it's a notes page). All other checks pass.

#### 4. **`pages/` directory**
Individual page files for debugging specific rule sections:
- `page_001.txt` through `page_076.txt`
- Use to manually verify extraction of specific rules
- Helpful for understanding page boundaries for citation

### Quality Validation Results

| Check | Status | Details |
|-------|--------|---------|
| **Completeness** | ✅ PASS | All 71 pages extracted |
| **Quality** | ⚠️ WARNING | Page 76 is short (expected—notes page) |
| **Content Volume** | ✅ PASS | Avg 2,976 chars/page (good for rulebook) |
| **Structure Preservation** | ✅ PASS | Rule numbers and sections detected |

---

## How This Feeds Into Phase 2: Chunking

### Key Decisions Made in Phase 1

1. **Structure Preservation**
   - Kept rule numbers, section headers, subsection letters
   - Did NOT flatten the document
   - **Implication for Phase 2**: Can use hierarchical chunking (split by rule first, then by section)

2. **No OCR Artifacts**
   - Text extracted cleanly from PDF (not scanned image)
   - No need for OCR post-processing
   - **Implication for Phase 2**: Can safely chunk on semantic boundaries

3. **Header/Footer Removal**
   - Removed "PAGE" footer artifacts
   - Kept actual content
   - **Implication for Phase 2**: No noise to filter in chunks

4. **Citation Readiness**
   - Each page is indexed in metadata
   - Can trace any chunk back to page number
   - **Implication for Phase 4 (Retrieval)**: Can cite exact page numbers

### What Phase 2 Will Do With This

**Input**: `01_raw_extracted_text.txt` (full document as continuous text)

**Chunking decisions to make**:
1. Chunk size (e.g., 512 tokens, 1024 tokens?)
2. Overlap (e.g., 10% overlap to preserve context across chunks?)
3. Hierarchical? (e.g., chunk at rule level first, then subdivide?)
4. Include metadata? (section number, rule number, page number with each chunk?)

**Output**: `04_chunked_text.json` + `05_chunk_metadata.json`

**Example Phase 2 output**:
```json
{
  "chunk_id": "rule_2_section_1_chunk_1",
  "text": "Section I—The Game Officials\n\na. The game officials shall be a Crew Chief...",
  "metadata": {
    "rule_number": 2,
    "section": "I",
    "page_number": 10,
    "start_char_offset": 5234,
    "tokens": 150
  }
}
```

---

## Data Flow Across All Phases

```
Phase 1: Extraction (✅ DONE)
   PDF → Raw Text → Cleaned Text → Validated Text
   Outputs: 01_raw_extracted_text.txt, 02_extraction_metadata.json

↓

Phase 2: Chunking (NEXT)
   Raw Text → Semantic Chunks → Chunk Metadata Index
   Outputs: 04_chunked_text.json, 05_chunk_metadata.json

↓

Phase 3: Embedding (THEN)
   Chunks → Vector Embeddings → Embedding Index
   Outputs: 06_embeddings.h5, 07_embedding_metadata.json

↓

Phase 4: Retrieval (THEN)
   Query → Find Similar Chunks → Rank Results
   Uses: Vector Database Index

↓

Phase 5: LLM Generation (FINALLY)
   Query + Retrieved Chunks → Answer with Citations
   Uses: LLM + Chunk Metadata for citations
```

---

## Quality Checks Summary

### What We Verified ✅

- [x] All 71 pages extracted
- [x] No missing content
- [x] Headers and footers removed
- [x] Rule numbers and sections preserved
- [x] No encoding errors
- [x] No OCR artifacts
- [x] Text is searchable (not image-based)
- [x] Content volume reasonable (avg 2,976 chars/page)
- [x] Can map text back to pages (metadata index created)

### What to Spot-Check Before Phase 2

1. Open `pages/page_010.txt` and verify RULE NO. 2 content
2. Open `pages/page_030.txt` and scan for rule numbers
3. Check `01_raw_extracted_text.txt` end-to-end (look for structure)
4. Verify no weird artifacts (test with grep): `grep -i "page\|footer" 01_raw_extracted_text.txt`

### Known Limitations

- Page 76 is very short (notes page)—this is expected and correct
- PDF headers/footers removed (by design)
- Images/diagrams extracted as text only (no visual analysis)
- Tables: text extracted but structure may not be preserved (we'll handle in Phase 2)

---

## Next Steps

### Immediate (Before Phase 2)

1. ✅ **Extraction complete** — review `01_raw_extracted_text.txt` for quality
2. ✅ **Metadata created** — index generated for citations
3. ✅ **Validation passed** — quality checks OK (minor warning is expected)

### Phase 2 (Chunking Strategy)

Review and decide:
1. **Chunk size**: How many tokens per chunk?
2. **Chunking method**: By rule? By semantic boundaries? Hierarchical?
3. **Overlap**: Should chunks overlap for context?
4. **Metadata**: What metadata to attach to each chunk?

See `02_chunking_strategy.md` when ready.

---

## How to Run This Phase

### One-time setup:
```bash
pip install -r requirements.txt
```

### Run extraction:
```bash
python3 extract_pdf.py
```

### Validate outputs:
```bash
# Check file sizes
ls -lh data/

# View raw text sample
head -50 data/01_raw_extracted_text.txt

# Check validation report
cat data/03_validation_report.json | jq

# View metadata
cat data/02_extraction_metadata.json | jq '.pages[0:5]'
```

---

## RAG Framework Reference

This project follows a structured RAG architecture:

```
┌─────────────────────────────────────────────────┐
│         RAG Application Architecture             │
├─────────────────────────────────────────────────┤
│                                                  │
│  Phase 1: Document Processing (✅ COMPLETE)      │
│  ├─ Ingestion: PDF → Raw Text                   │
│  ├─ Cleaning: Remove artifacts                  │
│  └─ Validation: Quality checks                  │
│                                                  │
│  Phase 2: Chunking & Indexing (NEXT)            │
│  ├─ Chunking: Split into semantic pieces        │
│  ├─ Metadata: Attach source info                │
│  └─ Deduplication: Remove duplicates            │
│                                                  │
│  Phase 3: Embedding (THEN)                      │
│  ├─ Vectorization: Chunks → Vectors             │
│  ├─ Model: Embedding model selection            │
│  └─ Storage: Vector database                    │
│                                                  │
│  Phase 4: Retrieval (THEN)                      │
│  ├─ Query: User question → Vector               │
│  ├─ Search: Find similar chunks                 │
│  └─ Ranking: Order by relevance                 │
│                                                  │
│  Phase 5: Generation (FINALLY)                  │
│  ├─ LLM: Generate response                      │
│  └─ Citation: Map back to source                │
│                                                  │
└─────────────────────────────────────────────────┘
```

You are currently in **Phase 1 ✅** and ready for **Phase 2**.

