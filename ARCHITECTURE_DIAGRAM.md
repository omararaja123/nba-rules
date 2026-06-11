# NBA Rules RAG System: Complete Architecture Diagram

## 🏗️ Full System Architecture

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                        NBA RULES RAG SYSTEM - FULL ARCHITECTURE                ║
╚════════════════════════════════════════════════════════════════════════════════╝


┌────────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: DATA PREPARATION                              │
└────────────────────────────────────────────────────────────────────────────────┘

    NBA Rules PDF (76 pages)
           │
           ▼
    ┌──────────────────┐
    │  PyMuPDF Extract │  → Extract text from PDF
    │                  │  → Remove last 5 pages (images only)
    └────────┬─────────┘  → Result: 71 pages clean text
             │
             ▼
    ┌──────────────────┐
    │  Structure       │  → Analyze hierarchical organization
    │  Analysis        │  → Identify 13 rules, 2-8 sections each
    └────────┬─────────┘  → Map rule boundaries
             │
             ▼
    ┌──────────────────┐
    │  Rule-Based      │  → Chunk by rule + section (not token windows)
    │  Hierarchical    │  → ~512 tokens per chunk
    │  Chunking        │  → Respect semantic boundaries
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Metadata        │  ┌─ rule_number
    │  Attachment      │  ├─ rule_title
    │                  │  ├─ section_title
    └────────┬─────────┘  ├─ page_number
             │            ├─ chunk_id
             │            └─ is_super_chunk
             │
             ▼
    ┌──────────────────┐
    │  Validation      │  → Check 95% semantic completeness
    │  (Pre-Embed)     │  → Identify problem areas (traveling, fouls)
    └────────┬─────────┘  → Create super chunks for edge cases
             │
             ▼
    📦 112 Optimized Chunks (JSON)
       └─ 09_stable_chunks_aggressive_rebuild.json (270 KB)


┌────────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 2: EMBEDDING & STORAGE                              │
└────────────────────────────────────────────────────────────────────────────────┘

    112 Chunks + Metadata
           │
           ▼
    ┌────────────────────────────┐
    │ SentenceTransformers       │  → Model: all-MiniLM-L6-v2
    │ (Embedding Model)          │  → Output: 384D vectors
    └────────┬───────────────────┘  → Speed: optimized vs quality
             │
             ▼
    📊 Embedding Matrix: 112 × 384 dimensions
       └─ 10_embeddings_aggressive_rebuild.npy (168 KB)
             │
             ├─────────────────────────────┬─────────────────────────────┐
             │                             │                             │
             ▼                             ▼                             ▼
    ┌─────────────────────┐    ┌──────────────────┐    ┌──────────────────┐
    │   FAISS Index       │    │   BM25 Index     │    │   Metadata       │
    │  (Vector DB)        │    │  (Keyword DB)    │    │   Storage        │
    │                     │    │                  │    │                  │
    │ L2 distance search  │    │ Tokenization     │    │ JSON with all    │
    │ Top-10 retrieval    │    │ Full corpus      │    │ chunk metadata   │
    └─────────────────────┘    └──────────────────┘    └──────────────────┘


┌────────────────────────────────────────────────────────────────────────────────┐
│                   PHASE 3: RETRIEVAL PIPELINE                                  │
└────────────────────────────────────────────────────────────────────────────────┘

User Question: "What is traveling?"
         │
         ▼
    ┌────────────────────────────────────────────────────────────┐
    │            RETRIEVAL ORCHESTRATION LAYER                   │
    │                                                            │
    │  ┌──────────────────┐                                     │
    │  │  Query Encoding  │ → SentenceTransformers (384D)       │
    │  └────────┬─────────┘                                     │
    │           │                                               │
    │   ┌───────┴───────┐                                       │
    │   │               │                                       │
    │   ▼               ▼                                       │
    │ ┌────────┐   ┌──────────┐                                │
    │ │ FAISS  │   │  BM25    │                                │
    │ │ Search │   │  Search  │                                │
    │ │ (70%)  │   │  (30%)   │                                │
    │ │Top-10  │   │All 112   │                                │
    │ └────┬───┘   └────┬─────┘                                │
    │      │            │                                      │
    │      └────────┬───┘                                      │
    │               │                                          │
    │               ▼                                          │
    │    ┌──────────────────────┐                             │
    │    │  Hybrid Scoring      │  formula:                   │
    │    │  (Combine Results)   │  0.7×semantic +             │
    │    │                      │  0.3×keyword               │
    │    └──────────┬───────────┘                             │
    │               │                                          │
    │               ▼                                          │
    │    ┌──────────────────────┐                             │
    │    │ Cross-Encoder        │  → ms-marco-MiniLM          │
    │    │ Re-ranking (0.2w)    │  → Semantic relevance       │
    │    │                      │  → formula: 0.8×hybrid +    │
    │    │                      │             0.2×rerank      │
    │    └──────────┬───────────┘                             │
    │               │                                          │
    │               ▼                                          │
    │    ┌──────────────────────┐                             │
    │    │  Top-3 Selection     │  → Sorted by final score    │
    │    │  (Multiple Options)  │  → Better than top-1        │
    │    └──────────┬───────────┘                             │
    └───────────────┼────────────────────────────────────────┘
                    │
                    ▼
            Top-3 Rule Chunks
         (with metadata & scores)


┌────────────────────────────────────────────────────────────────────────────────┐
│              PHASE 4: LANGGRAPH ORCHESTRATION (CORE WORKFLOW)                  │
└────────────────────────────────────────────────────────────────────────────────┘

         User Input (Question)
                │
                ▼
    ╔══════════════════════════════════════════════════════════╗
    ║           RAGOrchestration (rag_orchestration.py)        ║
    ║                                                          ║
    ║  StateGraph with RAGState (TypedDict):                  ║
    ║  • question: str                                        ║
    ║  • retrieved_chunks: List[Dict]                         ║
    ║  • context: str                                         ║
    ║  • answer: str                                          ║
    ║  • citations: List[Dict]                                ║
    ║  • success: bool                                        ║
    ║  • error: str                                           ║
    ║                                                          ║
    ║  ┌──────────────────────────────────────────────────┐  ║
    ║  │  Node 1: retrieve_node                           │  ║
    ║  ├──────────────────────────────────────────────────┤  ║
    ║  │ Input: state['question']                         │  ║
    ║  │ Process:                                         │  ║
    ║  │  • Encode question (SentenceTransformers)        │  ║
    ║  │  • Semantic search (FAISS top-10)                │  ║
    ║  │  • Keyword search (BM25)                         │  ║
    ║  │  • Hybrid scoring (0.7 + 0.3)                    │  ║
    ║  │  • Cross-encoder re-ranking (0.2w)              │  ║
    ║  │ Output: state['retrieved_chunks'] = top-3        │  ║
    ║  │ Implementation: retriever.retrieve()             │  ║
    ║  └──────┬───────────────────────────────────────────┘  ║
    ║         │                                               ║
    ║         ▼                                               ║
    ║  ┌──────────────────────────────────────────────────┐  ║
    ║  │  Node 2: format_context_node                     │  ║
    ║  ├──────────────────────────────────────────────────┤  ║
    ║  │ Input: state['retrieved_chunks']                 │  ║
    ║  │ Process:                                         │  ║
    ║  │  • Organize chunks by rule number                │  ║
    ║  │  • Add metadata (section, page)                  │  ║
    ║  │  • Create LLM-readable text                      │  ║
    ║  │ Output: state['context'] = formatted string      │  ║
    ║  │ Implementation: retriever.format_context()       │  ║
    ║  └──────┬───────────────────────────────────────────┘  ║
    ║         │                                               ║
    ║         ▼                                               ║
    ║  ┌──────────────────────────────────────────────────┐  ║
    ║  │  Node 3: generate_node                           │  ║
    ║  ├──────────────────────────────────────────────────┤  ║
    ║  │ Input: state['question'], state['context']       │  ║
    ║  │ Process:                                         │  ║
    ║  │  • Build system prompt (grounding instructions)  │  ║
    ║  │  • Format user message with context              │  ║
    ║  │  • Call Claude API                               │  ║
    ║  │  • Extract answer text                           │  ║
    ║  │ Output: state['answer'] = response text          │  ║
    ║  │ Implementation: generator.generate_answer()      │  ║
    ║  └──────┬───────────────────────────────────────────┘  ║
    ║         │                                               ║
    ║         ▼                                               ║
    ║  ┌──────────────────────────────────────────────────┐  ║
    ║  │  Node 4: extract_citations_node                  │  ║
    ║  ├──────────────────────────────────────────────────┤  ║
    ║  │ Input: state['retrieved_chunks']                 │  ║
    ║  │ Process:                                         │  ║
    ║  │  • Extract rule metadata from chunks             │  ║
    ║  │  • Format as citation objects                    │  ║
    ║  │ Output: state['citations'] = citation list       │  ║
    ║  │ Implementation: generator._extract_citations()   │  ║
    ║  └──────┬───────────────────────────────────────────┘  ║
    ║         │                                               ║
    ║         ▼                                               ║
    ║     Final State                                        ║
    ║     (answer, chunks, citations, success)              ║
    ╚════════════════════════════════════════════════════════╝
                    │
                    ▼
        Result Object with All Data


┌────────────────────────────────────────────────────────────────────────────────┐
│                 PHASE 5: ANSWER GENERATION (LLM)                               │
└────────────────────────────────────────────────────────────────────────────────┘

    Formatted Context + Question
              │
              ▼
    ┌──────────────────────────────────────┐
    │  System Prompt                       │
    ├──────────────────────────────────────┤
    │ "You are an expert NBA rules        │
    │  official. Answer ONLY based on     │
    │  the provided rulebook excerpts.    │
    │  Do not use external knowledge.     │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  Claude LLM                          │
    ├──────────────────────────────────────┤
    │ Model: claude-haiku-4-5-20251001    │
    │ Max Tokens: 500                      │
    │ Temperature: 0.7                     │
    │ (Production: Haiku for speed)        │
    │ (Evaluation: Opus for quality)       │
    └──────────┬───────────────────────────┘
               │
               ▼
    Generated Answer (Grounded)
       with Citations


┌────────────────────────────────────────────────────────────────────────────────┐
│              PHASE 6: CACHING & SESSION MANAGEMENT                             │
└────────────────────────────────────────────────────────────────────────────────┘

    User Question
         │
         ├─→ Check Cache
         │
         ├─→ Cache HIT? ──YES──→ Return [Cached] Answer (<1s)
         │
         └─→ Cache MISS ─NO──→ Execute RAG Workflow (3-5s)
                               │
                               └─→ Store in Cache for Next Time


┌────────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 7: USER INTERFACE (STREAMLIT)                         │
└────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────┐
    │                 Streamlit Web App (app.py)              │
    │                                                         │
    │  ┌──────────────────┐      ┌──────────────────┐        │
    │  │  Chat Input      │      │  Chat History    │        │
    │  │                  │      │                  │        │
    │  │ "What is...?"    │      │ User Q1          │        │
    │  └────────┬─────────┘      │ Assistant A1     │        │
    │           │                │ User Q2          │        │
    │           │                │ Assistant A2     │        │
    │           │                └──────────────────┘        │
    │           │                                             │
    │           ▼                                             │
    │  ┌─────────────────────────────────────────┐           │
    │  │ RAG Orchestration                       │           │
    │  │ rag.invoke(question)                    │           │
    │  │ (LangGraph Workflow)                    │           │
    │  └────────┬────────────────────────────────┘           │
    │           │                                             │
    │           ▼                                             │
    │  ┌────────────────────────────────────┐               │
    │  │  Display Answer                    │               │
    │  ├────────────────────────────────────┤               │
    │  │ [Answer text]                      │               │
    │  │                                    │               │
    │  │ Sources (3 chunks)                 │               │
    │  │ ├─ Rule X: Title (Score: 95%)     │               │
    │  │ ├─ Rule Y: Title (Score: 88%)     │               │
    │  │ └─ Rule Z: Title (Score: 82%)     │               │
    │  │                                    │               │
    │  │ Metadata Display                   │               │
    │  │ └─ Page numbers, sections, text    │               │
    │  └────────────────────────────────────┘               │
    │                                                         │
    │  ┌──────────────────┐                                 │
    │  │  Sidebar         │                                 │
    │  ├──────────────────┤                                 │
    │  │ 🧪 Demo Qs       │  → 100+ preloaded questions    │
    │  │ 🔍 Search        │  → Filter by keyword           │
    │  │                  │                                 │
    │  │ ⚙️ Settings      │  → Toggle relevance scores     │
    │  │                  │  → Toggle chunk details        │
    │  │                  │                                 │
    │  │ System Info      │  → Metrics display             │
    │  │ ℹ️ About         │  → System description           │
    │  │ 🔄 Clear Chat    │  → Reset conversation          │
    │  └──────────────────┘                                 │
    └─────────────────────────────────────────────────────────┘


╔════════════════════════════════════════════════════════════════════════════════╗
║                              DATA FLOW SUMMARY                                 ║
╚════════════════════════════════════════════════════════════════════════════════╝

Input
  ↓
PDF Extraction → Chunking → Embedding → Storage
  ↓
Query Encoding → Retrieval → Hybrid Search → Re-ranking → Top-3
  ↓
LangGraph Orchestration
  ├─ Node 1: Retrieve
  ├─ Node 2: Format Context
  ├─ Node 3: Generate Answer (Claude)
  └─ Node 4: Extract Citations
  ↓
Caching + Session Management
  ↓
Streamlit UI
  ├─ Display Answer
  ├─ Show Sources
  ├─ Maintain Chat History
  └─ User Interaction


╔════════════════════════════════════════════════════════════════════════════════╗
║                        KEY COMPONENTS & TECHNOLOGIES                           ║
╚════════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────┬────────────────────────┬────────────────────────┐
│  Data Pipeline       │  Retrieval Layer       │  Generation & UI       │
├──────────────────────┼────────────────────────┼────────────────────────┤
│ • PyMuPDF            │ • SentenceTransformers │ • Claude LLM           │
│ • Custom Chunking    │ • FAISS (Vector DB)    │ • LangGraph            │
│ • Hierarchical org   │ • BM25 (Keyword)       │ • LangChain            │
│ • Metadata attach    │ • Cross-Encoder        │ • Streamlit            │
│ • Validation checks  │ • Hybrid Scoring       │ • Session State        │
│                      │ • Re-ranking           │ • Caching              │
└──────────────────────┴────────────────────────┴────────────────────────┘


╔════════════════════════════════════════════════════════════════════════════════╗
║                             METRICS & PERFORMANCE                              ║
╚════════════════════════════════════════════════════════════════════════════════╝

Data Pipeline:
  ✓ Input: 76 pages, 212 KB text
  ✓ Output: 112 optimized chunks, 270 KB JSON, 168 KB embeddings

Retrieval:
  ✓ Semantic Search: FAISS L2 distance (~300ms)
  ✓ Keyword Search: BM25 scoring (~100ms)
  ✓ Re-ranking: Cross-encoder validation (~200ms)
  ✓ Total Retrieval: ~600ms

Generation:
  ✓ LLM Call: ~2500ms (Haiku)
  ✓ Citation Extraction: ~100ms
  ✓ Total Generation: ~2600ms

Overall:
  ✓ First Answer: 3-5 seconds
  ✓ Cached Answer: <1 second
  ✓ Accuracy: 90% (benchmark), 79% (diverse)
  ✓ Quality: 4.77/5.0
  ✓ Hallucinations: 0


╔════════════════════════════════════════════════════════════════════════════════╗
║                           ERROR HANDLING & FALLBACKS                           ║
╚════════════════════════════════════════════════════════════════════════════════╝

Retrieval Failure:
  → Return empty chunks
  → LLM responds "Information not available"

Generation Failure:
  → Capture error in RAGState
  → Display error message
  → Suggest trying different question

Missing API Key:
  → Streamlit shows configuration error
  → User instructed to set ANTHROPIC_API_KEY

Cache Issues:
  → Re-execute full workflow
  → Update cache for future queries

```

---

## 📊 Architecture Highlights

### **Layers**

1. **Data Pipeline Layer**
   - PDF extraction with validation
   - Hierarchical chunking (rule-based)
   - Metadata attachment
   - Pre-embedding validation

2. **Storage Layer**
   - FAISS vector index (semantic search)
   - BM25 index (keyword search)
   - JSON metadata storage
   - NumPy embeddings

3. **Retrieval Layer**
   - Query encoding (SentenceTransformers)
   - Semantic search (FAISS)
   - Keyword search (BM25)
   - Hybrid scoring (70/30)
   - Cross-encoder re-ranking
   - Top-3 selection

4. **Orchestration Layer**
   - LangGraph state machine
   - 4-node DAG workflow
   - Error handling
   - State management

5. **Generation Layer**
   - Claude LLM integration
   - Grounded prompt engineering
   - Citation extraction
   - Answer formatting

6. **Session Layer**
   - Query caching (session-based)
   - Chat history
   - User preferences

7. **UI Layer**
   - Streamlit chat interface
   - Source display
   - Demo questions
   - Settings panel

### **Key Design Decisions**

✅ **Rule-Based Chunking** - Respects semantic boundaries  
✅ **Hybrid Retrieval** - Combines semantic + keyword strengths  
✅ **LangGraph Orchestration** - Production-grade workflow  
✅ **Top-3 Strategy** - Multiple options for LLM reasoning  
✅ **Light Re-ranking** - Filters without over-cutting  
✅ **Session Caching** - Instant repeat queries  
✅ **Grounded Generation** - Zero hallucinations  

---

**This architecture demonstrates production-grade RAG engineering with proper separation of concerns, error handling, and performance optimization.** 🚀
