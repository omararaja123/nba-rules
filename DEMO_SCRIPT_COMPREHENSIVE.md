# NBA Rules RAG Chatbot: 5-Minute Demo Script

**Total Time: 5 minutes**  
**Sections: 4 (Prep, Engineering, Results, Live Demo)**

---

## 📋 SECTION 1: THE PROBLEM (0:00 - 0:30)

### Slide/Screen: Problem Statement

**Speak:**
"I built a Retrieval-Augmented Generation system to answer NBA rules questions with source citations. The challenge: How do you take a 76-page rulebook and make it queryable?

Here are the final results: 90% retrieval accuracy, 4.77/5.0 quality, zero hallucinations. Let me show you how I got there."

**Show on screen:**
- Show metrics in terminal: `echo "90% accuracy | 4.77/5.0 quality | 160 questions tested"`

---

## 🔍 SECTION 2: VALIDATION & PREPARATION (0:30 - 1:45)

### Step 1: Structure Discovery (20 seconds)

**Speak:**
"First, I analyzed the rulebook structure. I found it's HIGHLY hierarchical—13 rules with 2-8 sections each."

**Show on screen:**
```
Rule 1: Court Dimensions
Rule 4: Traveling (Problem area!)
Rule 5: Scoring and Timing
  ├─ Section I: Scoring
  ├─ Section II: Timing
  ├─ Section III: Timeouts
  └─ ... 8 sections total

Rule 6: Fouls and Penalties
  └─ ... 6 sections
```

**Speak:**
"This matters because most RAG systems use arbitrary token windows. But NBA rules need semantic boundaries. If someone asks 'What is traveling?', they need the exact rule, not a chunk split across boundaries."

---

### Step 2: Chunking & Validation (25 seconds)

**Speak:**
"I used rule-based hierarchical chunking (~512 tokens per chunk) with full metadata."

**Show on screen:**
```
112 total chunks
Metadata: rule_number, section, page_number
Before embedding: validated chunks with Claude
Result: 95% semantically valid
Issues found: goaltending, traveling (multiple locations)
```

**Speak:**
"Key insight: I validated chunks BEFORE embedding. Found that traveling appeared 3 times in different contexts. Made note to create super-chunks later. This saved me from garbage-in-garbage-out problems."

---

## 🧠 SECTION 3: THE ENGINEERING (1:45 - 3:00)

### Embedding & Optimization (25 seconds)

**Speak:**
"Generated 384D embeddings with SentenceTransformers, built FAISS index. Initial semantic-only test: 70% accuracy.

Problem: 'Traveling' appeared 3 times. 'Goaltending' semantic match was wrong."

**Show on screen:**
```
Optimization Journey:
70% (semantic only)
  ↓ + BM25 keyword (30% weight)
85% (hybrid retrieval)
  ↓ + super chunks for traveling/fouls
88% (better chunking)
  ↓ + cross-encoder re-ranking (0.2 weight)
90% (final system)
```

**Speak:**
"The jump from 79% to 90% came from fixing chunks, not magic algorithms. Rule-based chunking matters."

---

### Production Architecture (10 seconds)

**Speak:**
"I wrapped everything in LangGraph—a production workflow engine with 4 nodes: retrieve → format → generate → cite."

**Show on screen:**
```
User Question
    ↓
LangGraph Workflow (rag_orchestration.py)
    ├─ Node 1: Hybrid search (FAISS + BM25)
    ├─ Node 2: Format context
    ├─ Node 3: Claude generates answer
    └─ Node 4: Extract citations
```

**Speak:**
"This is reusable by REST APIs, batch jobs, etc. Not just Streamlit."

---

## 📊 SECTION 4: LIVE DEMO (3:00 - 4:00)

### Live Demonstration (60 seconds)

**Speak:**
"Let me show you it working. I'll ask three questions to show different aspects."

**Do this:**

**DEMO 1: "What is traveling?" (20 seconds)**
1. Open terminal: `streamlit run app.py`
2. Wait for localhost:8501
3. Type in chat: "What is traveling?"
4. Wait for response

**While thinking:**
"Behind the scenes: hybrid search for 'traveling', formatting context, Claude generating answer, extracting citations. All in LangGraph."

**When answer shows:**
- Expand "Source Chunks" section
- Show 3 retrieved rules with relevance scores
- Point out: "See Rule 4, Section I? That's the exact definition we retrieved."

---

**DEMO 2: "Goaltending rules?" (15 seconds)**
1. Click a demo question or type new one
2. Show sources

**Speak:**
"Notice goaltending is now correct—it retrieves the right rule, not a false positive. This is the super-chunk optimization working."

---

**DEMO 3: Test grounding (15 seconds)**
1. Type: "How many points is a touchdown?"

**Show result:**
"The system correctly responds 'not in rulebook'. This is zero hallucinations—it grounds answers only in the data."

---

**DEMO 4: Performance highlight (10 seconds)**
1. Ask the same question again
2. Point out: "**[Cached]** label appears. <1 second response."

**Speak:**
"Same question returns instantly from cache. First answer was 3-5 seconds. Cached answers are instant."

---

## 🎯 CLOSING (4:00 - 5:00)

**Speak:**
"What you saw:

1. **Structure discovery** - I analyzed the rulebook before chunking
2. **Validation** - Checked chunks for quality before embedding
3. **Optimization** - Iteratively improved from 70% → 90%
4. **Production patterns** - LangGraph orchestration, not scripts
5. **Grounding** - Zero hallucinations through careful engineering

**Why this matters:**
- Shows discipline in building RAG systems
- Demonstrates data validation practices
- Proves iterative optimization with measurement
- Uses production patterns (LangGraph)
- Results backed by 160 test questions

This project demonstrates RAG engineering done right: validate early, measure everything, iterate deliberately, use production patterns.

**Questions?**"

---

## 📝 SPEAKER NOTES

### Timing Guide
- **Problem statement**: 30 seconds
- **Validation & preparation**: 75 seconds
  - Structure discovery: 20s
  - Chunking & validation: 25s
- **Engineering**: 75 seconds
  - Embedding & optimization: 25s
  - Production architecture: 10s
- **Live demo**: 60 seconds (🎬 THE MAIN EVENT!)
  - Demo 1 (traveling): 20s
  - Demo 2 (goaltending): 15s
  - Demo 3 (grounding test): 15s
  - Demo 4 (caching): 10s
- **Closing**: 60 seconds

### Key Points to Emphasize
1. **Validation first** - "I validated chunks before embedding them"
2. **Structure matters** - "The rulebook is hierarchical; chunks should respect that"
3. **Iterative optimization** - "70% → 90% through deliberate improvements"
4. **Domain-specific solutions** - "Pure semantic search failed; hybrid retrieval succeeded"
5. **Production patterns** - "LangGraph for orchestration, not quick scripts"

### Demo Troubleshooting
If Streamlit doesn't start quickly:
- Have a cached response ready to show
- Or have screenshots of previous demo runs
- Or explain: "The LLM call takes 2-3 seconds; let me show you the architecture while it thinks"

### Questions You Might Get
- **"Why 70/30 semantic/keyword?"** - "Tested 60/40, 70/30, 80/20. 70/30 was empirically optimal."
- **"Why remove last 5 pages?"** - "They had no text content, just images. Would add noise to embeddings."
- **"Why rule-based chunking?"** - "NBA rules are structured by rule → section. Chunks should respect that for citations and semantic coherence."
- **"Why LangGraph?"** - "Production systems need orchestration. It's reusable by APIs, batch jobs, etc."

---

## 🎬 PRESENTATION CHECKLIST

Before presenting:
- [ ] Terminal ready (cd to /nba-rules directory)
- [ ] Streamlit app ready to launch
- [ ] Browser bookmarked to localhost:8501
- [ ] Example questions in mind
- [ ] Screenshots as backup
- [ ] Time yourself once (should be ~5 min)
- [ ] Have FINAL_SUBMISSION_COMBINED.md open as reference

Backup slides (if running short):
- Show github.com/omararaja123/nba-rules
- Walk through rag_orchestration.py code
- Explain RAGState TypedDict
- Show git log of 15 commits

---

## 🎥 SCRIPT VARIATIONS

### For Instructors (Emphasize Learning)
- Focus on "What I learned" at each stage
- Highlight validation and testing
- Show iteration process
- Discuss trade-offs (accuracy vs speed)

### For Recruiters (Emphasize Engineering)
- Start with results (90%, 4.77/5.0)
- Emphasize production patterns (LangGraph)
- Discuss system design decisions
- Show code quality and architecture

### For Peers (Emphasize Process)
- Show the full journey including failures
- Discuss optimization phases
- Explain intuition behind choices
- Ask for feedback on architecture

---

**Good luck with your demo!** 🚀
