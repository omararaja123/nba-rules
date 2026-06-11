# NBA Rulebook RAG Pipeline
## Phase 1: Document Parsing & Raw Text Extraction

---

## 1. Project Context & Use Case

**One-line RAG Statement:**  
Retrieve specific NBA rules, interpretations, and edge cases from the official rulebook to identify underutilized rules and strategic opportunities.

**Key Characteristics:**
- **Corpus Type**: Structured legal/technical document (rulebook)
- **Primary Use**: Rule lookup, edge case discovery, strategic analysis
- **Citation Criticality**: HIGH (must cite exact rule sections for credibility)
- **Ambiguity Level**: MODERATE (some interpretive rules, multiple cross-references)

---

## 2. Corpus Overview

**Source Document**: Official-2025-26-NBA-Playing-Rules.pdf (1.6 MB)

**Expected Structure**:
- Table of contents with rule sections
- Numbered rules with subsections
- Cross-references between sections
- Penalty tables and diagrams (possible OCR challenge)
- Footnotes and official interpretations
- Possibly multi-column layout

**Extraction Challenges**:
- PDF may have headers/footers on every page
- Page numbers should be removed (noise)
- Section breaks may span pages
- Tables (fouls, penalties) require special handling
- Possible images/diagrams (we'll extract text only for now)

---

## 3. PDF Parsing Library Comparison

| Library | Strength | Weakness | Best For |
|---------|----------|----------|----------|
| **PyMuPDF (fitz)** | Fastest, handles complex PDFs well, good text extraction | Requires C dependencies | ✅ PRIMARY CHOICE |
| **pdfplumber** | Excellent table extraction, precise layout info | Slower on large docs | Fallback for table detection |
| **pypdf** | Pure Python, no C deps | Limited layout preservation | Not recommended here |
| **pdfminer.six** | Detailed text positioning | Slow, complex API | Academic use only |

**Recommendation**: Use **PyMuPDF (fitz)** as primary with **pdfplumber** for selective table analysis.

---

## 4. Extraction Strategy

### 4.1 Overall Approach

```
PDF File
   ↓
[PyMuPDF] Extract text page-by-page
   ↓
[Cleaning] Remove headers, footers, page numbers
   ↓
[Validation] Verify structure, check for OCR failures
   ↓
Raw Text File (preserved structure, section headings intact)
   ↓
[Metadata] Create index: section → page number → text offset
   ↓
Ready for Chunking Phase
```

### 4.2 Quality Metrics

We'll validate extraction by:
- **Completeness**: All pages processed, no missing content
- **Structure Preservation**: Section headings, numbering intact
- **Cleanliness**: Headers/footers removed, minimal noise
- **Readability**: No garbled text, proper line breaks
- **Citation-Readiness**: Can map any extracted text back to page number

---

## 5. Implementation Decisions

### 5.1 Why Preserve Original Structure?

- **Downstream Chunking**: Structured text makes semantic chunking easier
- **Citation Accuracy**: Keeping section numbers allows precise rule references
- **Pattern Recognition**: Section hierarchy helps identify rule interdependencies
- **Quality Control**: Easier to spot extraction failures with original structure

### 5.2 Header/Footer Removal Strategy

- Extract text from each page independently
- Identify common first/last lines (likely headers/footers)
- Remove repeated patterns (e.g., "Official NBA Rules 2025-26")
- Preserve page breaks as markers for downstream citation

### 5.3 Metadata Schema

For each page:
```json
{
  "page_number": 1,
  "source": "Official-2025-26-NBA-Playing-Rules.pdf",
  "text": "...",
  "extraction_timestamp": "2026-06-10T...",
  "quality_score": 0.95,
  "detected_sections": ["Table of Contents"],
  "contains_tables": false,
  "ocr_required": false
}
```

---

## 6. Downstream Implications

### 6.1 Chunking (Phase 2)
- **Input**: Well-structured raw text with section numbers
- **Decision Point**: Whether to chunk by section vs. semantic boundaries
- **Benefit**: Clear section hierarchy makes hierarchical chunking possible

### 6.2 Embedding (Phase 3)
- **Input**: Clean, deduplicated chunks with section context
- **Decision Point**: Include section metadata in embedding or embed separately?
- **Benefit**: No wasted tokens on headers/footers/noise

### 6.3 Retrieval (Phase 4)
- **Input**: Indexed chunks with full citation trail back to source
- **Decision Point**: Hybrid search (lexical + semantic) or semantic only?
- **Benefit**: High recall for specific rule references, high precision for concepts

### 6.4 Citation (Phase 5)
- **Input**: Retrieved chunks with page numbers, section numbers
- **Decision Point**: How to surface citation in LLM response?
- **Benefit**: User can verify claims against official document

---

## 7. Quality Validation Checklist

Before moving to chunking, confirm:

- [ ] All pages extracted (check page count matches PDF)
- [ ] No repeated content (headers/footers removed)
- [ ] Section structure visible (rule numbers, subsections intact)
- [ ] Special characters readable (dashes, parentheses, quotes)
- [ ] Table structure preserved (e.g., foul penalty tables readable)
- [ ] Line breaks sensible (no mid-word breaks)
- [ ] No OCR artifacts (garbled characters, mojibake)
- [ ] Text is searchable (not image-based)
- [ ] Can map extracted text back to page numbers

---

## 8. Next Steps

1. Install PyMuPDF and pdfplumber
2. Run extraction script
3. Inspect output for quality issues
4. Generate metadata index
5. Validate against checklist above
6. Save clean text + metadata for Phase 2 (Chunking)

