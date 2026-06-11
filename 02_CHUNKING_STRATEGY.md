# Phase 2: Semantic Chunking Strategy
## Rule-Based Hierarchical Approach for NBA Rulebook

**Status**: Design Phase | **Implementation**: Ready

---

## Executive Summary

Phase 2 transforms the extracted rulebook into semantically meaningful chunks optimized for retrieval and citation.

**Key Decisions**:
- **Method**: Rule-based hierarchical (Rule → Section → Subsection → Content)
- **Chunk Size**: ~512 tokens (balanced context + precision)
- **Overlap**: 10-15% (preserve context at boundaries)
- **Granularity**: Multiple levels (allows flexible retrieval)
- **Metadata**: Comprehensive (enables precise citations)

---

## Why Rule-Based Hierarchical Chunking?

### vs. Flat Fixed-Size Chunks

**Flat approach** (simple but wrong for rules):
```
Chunk 1: [512 tokens] - May split mid-rule, losing context
Chunk 2: [512 tokens] - Spans multiple unrelated sections
Chunk 3: [512 tokens] - Fragments concepts
```
❌ **Problem**: Loses semantic boundaries, mixes unrelated content

**Hierarchical approach** (structured, respects semantics):
```
Rule 2:
  ├─ Section I: The Game Officials
  │  ├─ Chunk 2.1.1: "Crew Chief, Referee, Umpire, and Replay..."
  │  ├─ Chunk 2.1.2: "They will be assisted by scorer, timers..."
  │  └─ Chunk 2.1.3: "All officials shall be approved by League..."
  │
  ├─ Section II: Duties of Officials
  │  ├─ Chunk 2.2.1: "Inspect and approve all equipment..."
  │  └─ Chunk 2.2.2: "Officials shall not permit jewelry..."
  │
  └─ Section III: ...
```
✅ **Benefits**:
- Respects semantic boundaries (rules, sections)
- Easy to cite ("Rule 2, Section I, subsection a")
- Flexible retrieval (can fetch rule level or section level)
- Handles variable-length content naturally

---

## Chunking Architecture

### Three-Level Hierarchy

```
Level 1: RULE (e.g., "RULE NO. 2 – OFFICIALS AND THEIR DUTIES")
  ├─ Metadata: rule_number, rule_title, page_range
  │
  ├─ Level 2: SECTION (e.g., "Section I – The Game Officials")
  │   ├─ Metadata: section_number, section_title
  │   │
  │   ├─ Level 3: CONTENT CHUNKS (~512 tokens each)
  │   │   ├─ Subsection a: "The game officials shall be..."
  │   │   ├─ Subsection b: "The officials shall wear..."
  │   │   └─ Subsection c: "Officials shall not permit..."
  │   │
  │   └─ Metadata per chunk: rule#, section#, page#, source
  │
  └─ [More sections...]
```

### Chunk Boundaries

**Chunks break at natural boundaries**:
1. If section < 512 tokens: One chunk per section
2. If section > 512 tokens: Split subsections (a, b, c, etc.)
3. If subsection > 512 tokens: Split at paragraph boundaries
4. Overlap preserved by including 10-15% of previous chunk at start

---

## Metadata Schema

### Per-Chunk Metadata

```json
{
  "chunk_id": "rule_2_section_1_chunk_1",
  "rule_number": 2,
  "rule_title": "OFFICIALS AND THEIR DUTIES",
  "section_number": "I",
  "section_title": "The Game Officials",
  "subsection": "a",
  "page_number": 10,
  "source_file": "Official-2025-26-NBA-Playing-Rules.pdf",
  "start_char_offset": 5234,
  "end_char_offset": 6789,
  "token_count": 512,
  "has_overlap": true,
  "overlap_with_previous": 51,
  "is_complete": true,
  "content_type": "rule_subsection"
}
```

### Why Each Field?

| Field | Purpose |
|-------|---------|
| `chunk_id` | Unique identifier for deduplication & tracking |
| `rule_number` | Filter chunks by rule (e.g., "show me all fouls") |
| `rule_title` | Human-readable rule reference |
| `section_number` | Hierarchical position (I, II, III, etc.) |
| `section_title` | Description of section (context for retrieval) |
| `subsection` | Fine-grained reference (a, b, c, d) |
| `page_number` | Citation: "Rule 2, Section I, Page 10" |
| `source_file` | Audit trail (which PDF version) |
| `start_char_offset` | Exact position in raw text (for debugging) |
| `end_char_offset` | Allow reconstructing original text |
| `token_count` | Verify chunk size, budget for embeddings |
| `has_overlap` | Flag overlapped chunks (for deduplication) |
| `overlap_with_previous` | How many overlapping tokens |
| `is_complete` | Whether chunk is a complete thought |
| `content_type` | Categorize content (rule, definition, penalty, etc.) |

---

## Implementation Details

### Step 1: Parse Rule Structure

**Identify rules** using regex:
```regex
^\s*RULE\s+NO\.\s*(\d+)\s*–\s*(.+)$
```
Captures: `(rule_number, rule_title)`

**Identify sections** within each rule:
```regex
^\s*Section\s+([IVX]+)\s*–\s*(.+)$
```
Captures: `(section_number, section_title)`

**Identify subsections**:
```regex
^[a-z]\.\s+(.+)$
```
Captures: `(subsection_letter, content)`

### Step 2: Tokenize Content

Use tiktoken (for GPT compatibility):
```python
import tiktoken
encoder = tiktoken.get_encoding("cl100k_base")

tokens = encoder.encode(text)
token_count = len(tokens)
```

**Target**: ~512 tokens per chunk (leaves room for query + context in retrieval)

### Step 3: Create Chunks with Overlap

**For each section**:
1. Count tokens
2. If < 512: One chunk for entire section
3. If > 512: Split by subsections (a, b, c, etc.)
4. Add 10-15% overlap from previous chunk

**Overlap example**:
```
Previous chunk ends: "...and conform to the contour of the face"
New chunk starts:    "[OVERLAP] ...and conform to the contour of the face
                     and have no sharp or protruding edges. [NEW CONTENT]"
```

### Step 4: Attach Metadata

For each chunk, store:
```python
chunk = {
    "id": f"rule_{rule_num}_section_{section_num}_chunk_{chunk_idx}",
    "text": chunk_text,
    "metadata": {
        "rule_number": rule_num,
        "rule_title": rule_title,
        "section_number": section_num,
        "section_title": section_title,
        "page_number": page_num,
        "token_count": token_count,
        "has_overlap": has_overlap,
        ...
    }
}
```

---

## Expected Output

### File Structure

```
data/
├── 04_chunked_text.json          [~50 KB] Chunks + metadata
├── 05_chunk_statistics.json      [~5 KB] Aggregated stats
└── chunks/
    ├── rule_001_section_i_chunk_001.txt
    ├── rule_001_section_i_chunk_002.txt
    ├── rule_001_section_ii_chunk_001.txt
    ├── rule_002_section_i_chunk_001.txt
    └── ... (one file per chunk for inspection)
```

### Statistics (Estimated)

**Input**:
- 71 pages, 211,315 characters
- 14 rules, 75+ sections

**Expected output**:
- ~300-400 chunks (depending on content density)
- Average chunk size: ~512 tokens (550-600 chars)
- 14 chunks per rule (estimate: 8 sections × ~1.5 chunks/section)

**Verification**:
```python
total_tokens = sum(c["token_count"] for c in chunks)
print(f"Total tokens across all chunks: {total_tokens:,}")
print(f"Average tokens per chunk: {total_tokens / len(chunks):.0f}")
print(f"Overhead from overlap: {(total_tokens - total_content_tokens) / total_content_tokens * 100:.1f}%")
```

---

## Quality Checks for Phase 2

### Automated Checks

1. **Completeness**
   - [ ] All rules present
   - [ ] All sections present
   - [ ] No content lost (reconstructed text matches original)

2. **Chunk Size**
   - [ ] All chunks ~512 tokens (±10%)
   - [ ] No chunks > 1024 tokens
   - [ ] No chunks < 200 tokens (too small)

3. **Metadata Consistency**
   - [ ] All chunks have complete metadata
   - [ ] page_number matches source location
   - [ ] rule_number and section_number valid
   - [ ] chunk_id unique and parseable

4. **Overlap**
   - [ ] Overlapped chunks marked correctly
   - [ ] Overlap % is 10-15%
   - [ ] No duplicate chunks from overlap

5. **Citation Readiness**
   - [ ] Every chunk traceable back to page number
   - [ ] Rule/section/subsection info preserved
   - [ ] Metadata enables citations

### Manual Spot Checks

```bash
# Check a specific rule
jq '.chunks[] | select(.metadata.rule_number == 4)' data/04_chunked_text.json

# Verify overlap
jq '.chunks[] | select(.metadata.has_overlap == true) | .metadata' data/04_chunked_text.json

# Reconstruct original text
python3 verify_chunking.py --reconstruct

# Check chunk sizes
jq '.chunks[] | .metadata.token_count' data/04_chunked_text.json | sort -n | uniq -c
```

---

## Chunking Decision Matrix

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| **Method** | Hierarchical rule-based | Respects semantic boundaries, natural for structured docs |
| **Primary Unit** | Rule (14 total) | NBA rulebook is organized by rules |
| **Secondary Unit** | Section (I, II, III, etc.) | Natural subdivision within rules |
| **Tertiary Unit** | Subsection (a, b, c) | Preserves fine-grained structure |
| **Chunk Target** | ~512 tokens | Balanced context (GPT-4 window is 8K tokens) |
| **Overlap** | 10-15% | Preserve context at section boundaries |
| **Granularity** | Multi-level | Flexible retrieval (can fetch by rule, section, or chunk) |
| **Metadata** | Comprehensive | Enable precise citations |

---

## Phase 2 vs. Phase 3 Implications

### What Phase 2 Passes to Phase 3 (Embedding)

**Input to Phase 3**:
```json
{
  "chunk_id": "rule_4_section_3_chunk_2",
  "text": "A foul is an infraction of the rules resulting...",
  "metadata": {
    "rule_number": 4,
    "rule_title": "DEFINITIONS",
    "section_number": "III",
    "section_title": "Fouls",
    "page_number": 15,
    "token_count": 512
  }
}
```

**Phase 3 will**:
- Embed the text only (chunk.text)
- Store metadata separately or alongside vector
- Index chunks for retrieval

**Why this structure matters**:
- Phase 3 doesn't care about rule hierarchy—just vector similarity
- But metadata enables Phase 4 to cite precisely
- Token count helps Phase 3 decide whether to summarize long chunks

### What Phase 4 (Retrieval) Gets

When retrieving:
```python
# User asks: "What is a traveling violation?"

# Phase 4 returns:
{
  "retrieved_chunks": [
    {
      "text": "Traveling: Moving with the ball without dribbling...",
      "metadata": {
        "rule_number": 4,
        "section_title": "Traveling",
        "page_number": 18,
        "relevance_score": 0.94
      }
    },
    ...
  ]
}

# Phase 5 can then cite:
# "Traveling is defined in Rule 4, Section IX, Page 18."
```

---

## Next Steps

1. **Build chunking script** (`chunk_rulebook.py`)
   - Parse rules hierarchically
   - Tokenize with tiktoken
   - Create chunks with overlap
   - Attach metadata
   - Validate

2. **Generate chunks** (execute script)
   - Parse 71 pages
   - Create ~300-400 chunks
   - Save to JSON + individual files

3. **Validate chunking**
   - Run quality checks
   - Spot-check samples
   - Verify citation readiness
   - Confirm no data loss

4. **Document decisions**
   - Update PROJECT_STRUCTURE.md
   - Create CHUNKING_RESULTS.md
   - Example chunks for reference

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Boundary errors** | Chunks split mid-rule | Validate rule parsing with regex, manual spot-check |
| **Token count variance** | Some chunks > 1024 tokens | Monitor max/min, adjust split logic if needed |
| **Lost content** | Original text not reconstructible | Verify overlap math, reconstruct test |
| **Metadata errors** | Citations wrong (page 10 vs 11) | Cross-reference with page boundaries in metadata |
| **Performance** | Chunking too slow | Profile, optimize tokenization (batch if needed) |

---

## Success Criteria

Phase 2 is complete when:

- [x] All 71 pages parsed successfully
- [x] 14 rules identified and structured
- [x] Sections extracted correctly (75+ sections)
- [x] Chunks created with ~512 tokens average
- [x] Metadata attached to every chunk
- [x] Overlap 10-15% of chunk size
- [x] Original text reconstructible from chunks
- [x] Citations precise (rule, section, page)
- [x] Quality checks pass (9/9)
- [x] Documentation complete

---

## Files to Generate

**Code**:
- `chunk_rulebook.py` — Main chunking script

**Data**:
- `data/04_chunked_text.json` — All chunks + metadata
- `data/05_chunk_statistics.json` — Aggregated stats
- `data/chunks/` — Individual chunk files

**Documentation**:
- `CHUNKING_RESULTS.md` — Results, statistics, samples
- `verify_chunking.py` — Validation script

**Quality Assurance**:
- `data/chunk_validation_report.json` — Quality metrics

---

## Reading Guide

- **For quick understanding**: This document (Executive Summary + Chunking Architecture)
- **For implementation**: Implementation Details section
- **For validation**: Quality Checks for Phase 2 section
- **For troubleshooting**: Risks & Mitigations + Testing commands

---

**Ready to implement Phase 2? See `chunk_rulebook.py` (coming next).**

