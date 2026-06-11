# NBA Rules RAG Chatbot - Streamlit Setup Guide

## Overview

This guide walks you through setting up and running the production-quality Streamlit chatbot interface for the NBA Rules RAG system.

**What You Get:**
- 🎨 Beautiful, responsive two-column UI
- 💬 Multi-turn conversation with chat history
- 📎 Source transparency panel showing retrieved chunks
- 🔍 Real-time retrieval with hybrid search (semantic + keyword)
- ✍️ Claude-powered answer generation with citations
- 📊 Performance metrics and system info
- 🎯 Professional, production-ready design

---

## Prerequisites

### System Requirements
- Python 3.9+
- pip or conda
- ~2GB RAM (recommended for models and indices)
- Internet connection (for Anthropic API calls)

### API Key Required
- **Anthropic API Key** (Get one at https://console.anthropic.com/)
  - Used for Claude to generate answers
  - No cost for free tier; pay-as-you-go after that

### Files Required
Ensure these files exist in your project root:
```
data/09_stable_chunks_aggressive_rebuild.json    (Final chunks)
data/10_embeddings_aggressive_rebuild.npy         (Final embeddings)
```

---

## Installation Steps

### Step 1: Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using conda
conda create -n nba-rag python=3.9
conda activate nba-rag
pip install -r requirements.txt
```

### Step 2: Set Up API Key

**Option A: Using .env file (Recommended)**

Create a `.env` file in your project root:
```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

**Option B: Environment variable**

```bash
# macOS/Linux
export ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# Windows
set ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

### Step 3: Verify Setup

Test that all modules load correctly:

```bash
python -c "
from retriever import NBARetriever
from generator import AnswerGenerator
print('✅ Retriever loaded')
print('✅ Generator loaded')
print('Ready to run Streamlit app!')
"
```

---

## Running the Application

### Start the Streamlit Server

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Access the Application

- **Main interface:** `http://localhost:8501`
- **Settings/Info:** Sidebar (right-hand panel)
- **Source chunks:** Right column of chat area

---

## Application Features

### Chat Interface (Left Column)

**User Interaction:**
- Type questions in the input box at the bottom
- Press Enter or click the send button
- Messages appear in conversational format

**Message Types:**
- 👤 **User messages:** Light blue background
- 🤖 **Assistant messages:** Light gray background with expandable sources

**Example Questions:**
```
• What is traveling?
• How many fouls lead to ejection?
• When can a player be substituted?
• What are the court dimensions?
• What is the shot clock rule?
```

### Source Panel (Right Column)

**Shows for each answer:**
- Rule number and title
- Section name
- Page number
- Relevance score (if enabled)
- Full chunk text
- Visual cards for each source

**Expandable Sources:**
- Click "📎 Sources (X chunks used)" under an answer
- View detailed information about each retrieved chunk
- See relevance scores and exact rulebook text used

### Sidebar Settings

**Display Options:**
- ☑️ Show relevance scores: Toggle to display/hide % scores
- ☑️ Show all retrieved chunks: Toggle expanded view

**System Info:**
- Number of chunks (112)
- Retrieval accuracy (90%)
- LLM quality score (4.77/5.0)
- Test coverage (160 questions)

**Controls:**
- 🔄 Clear Chat History: Reset conversation and retrieved chunks
- ℹ️ About This System: Detailed system information

---

## Architecture & Modules

### File Structure

```
nba-rules/
├── app.py                   # Main Streamlit application
├── retriever.py             # Retrieval logic (hybrid search)
├── generator.py             # Answer generation (Claude)
├── config.py                # Configuration settings
├── requirements.txt         # Python dependencies
├── STREAMLIT_SETUP.md       # This file
└── data/
    ├── 09_stable_chunks_aggressive_rebuild.json
    └── 10_embeddings_aggressive_rebuild.npy
```

### Module Responsibilities

**config.py**
- Centralized configuration
- Paths, model settings, UI text
- Weights and hyperparameters

**retriever.py - NBARetriever class**
- Loads chunks and embeddings
- Semantic search (FAISS)
- Keyword search (BM25)
- Hybrid scoring and re-ranking
- Returns top-3 most relevant chunks

**generator.py - AnswerGenerator class**
- Claude API integration
- System prompt definition
- Answer generation with context
- Citation formatting
- Error handling

**app.py**
- Streamlit UI implementation
- Session state management
- Chat history persistence
- Two-column layout
- Real-time interaction

---

## How It Works

### Query Processing Pipeline

```
User Question
    ↓
[Session State] Load retriever, generator
    ↓
[Retrieval] Call retriever.retrieve(question)
    ├─ Encode query to embeddings
    ├─ FAISS search (semantic, top-10)
    ├─ BM25 search (keyword, all chunks)
    ├─ Hybrid scoring (70% semantic + 30% keyword)
    └─ Cross-encoder re-ranking (0.2 weight)
    ↓
[Context Formatting] Format top-3 chunks as context
    ↓
[Generation] Call generator.generate_answer()
    ├─ Build prompt with system instructions
    ├─ Call Claude Opus API
    ├─ Get answer text
    └─ Extract citations from chunks
    ↓
[Display]
    ├─ Show answer in chat
    ├─ Show sources in expandable section
    ├─ Display relevance scores (optional)
    └─ Save to chat history
```

### Retrieval Scoring

**Formula:**
```
hybrid_score = 0.7 × semantic_score + 0.3 × keyword_score
final_score = 0.8 × hybrid_score + 0.2 × reranker_score
```

**Why this works:**
- Semantic search handles meaning and context
- Keyword search handles acronyms and exact terms
- Cross-encoder re-ranking filters false positives
- Top-3 gives LLM multiple options to choose from

---

## Performance Expectations

### Response Times

- **Retrieval:** 1-3 seconds (embedding + search)
- **Generation:** 3-10 seconds (Claude API call)
- **Total:** 5-15 seconds per question

### Accuracy Metrics

- **Retrieval Accuracy:** 90% (9/10 benchmark questions)
- **LLM Answer Quality:** 4.77/5.0 (relevance, completeness, accuracy)
- **Test Coverage:** 160 questions (10 benchmark + 100 diverse + 50 edge cases)

### Limitations

- Queries outside NBA rules return "not available in rulebook"
- Edge case questions may require clarification
- Cross-references between rules may be incomplete
- Rare scenarios have limited training data

---

## Customization

### Adjusting Retrieval Parameters

Edit `config.py`:

```python
# Number of chunks to retrieve
TOP_K_RETRIEVAL = 3  # Change to 1, 5, etc.

# Hybrid weights (must sum to 1.0)
SEMANTIC_WEIGHT = 0.7  # Increase for more semantic
KEYWORD_WEIGHT = 0.3   # Increase for more keyword

# Re-ranking weight
RERANKER_WEIGHT = 0.2  # 0.0 = no re-ranking, 0.5 = equal weight
```

### Changing LLM Model

Edit `config.py`:

```python
LLM_MODEL = "claude-sonnet-4-6"  # For faster responses
# or
LLM_MODEL = "claude-haiku-4-5-20251001"  # For lower cost
```

### Modifying UI Text

Edit `config.py`:

```python
WELCOME_MESSAGE = """Your custom welcome text here"""
ABOUT_MESSAGE = """Your custom about text here"""
```

### Custom System Prompt

Edit `generator.py` in the `system_prompt()` method:

```python
def system_prompt(self) -> str:
    return """Your custom system prompt here"""
```

---

## Troubleshooting

### Common Issues

**Issue: "ANTHROPIC_API_KEY environment variable not set"**
```
Solution:
1. Create .env file with your API key
2. Or export ANTHROPIC_API_KEY in your shell
3. Restart the Streamlit server
```

**Issue: "Could not load embeddings file"**
```
Solution:
1. Check file exists: data/10_embeddings_aggressive_rebuild.npy
2. Check file path in config.py
3. Ensure you're in the correct directory
```

**Issue: "No module named 'sentence_transformers'"**
```
Solution:
pip install sentence-transformers
# or
pip install -r requirements.txt
```

**Issue: "Streamlit not found"**
```
Solution:
pip install streamlit
# or
pip install -r requirements.txt
```

**Issue: Slow responses from Claude**
```
Solutions:
1. Check internet connection
2. Try a faster model (claude-haiku vs claude-opus)
3. Reduce MAX_TOKENS in config.py
```

### Debug Mode

To see detailed logs, run with:

```bash
streamlit run app.py --logger.level=debug
```

---

## Future Enhancements

### Planned Features

1. **Conversation Memory**
   - Multi-turn context awareness
   - Follow-up questions referencing previous answers
   - Conversation summarization

2. **Query Rewriting**
   - Rephrase questions for better retrieval
   - Decompose complex questions into sub-queries
   - Handle typos and abbreviations

3. **Feedback System**
   - 👍 Helpful / 👎 Not helpful buttons
   - User feedback logging for model improvement
   - Citation feedback (is source correct?)

4. **Advanced Retrieval**
   - Hybrid search improvements
   - Query expansion (synonyms, related terms)
   - Semantic re-ranking with larger models
   - Multi-hop retrieval for complex questions

5. **Analytics Dashboard**
   - Question frequency analysis
   - Common failure patterns
   - User satisfaction metrics
   - Performance trends

6. **Retrieval Debugging**
   - Show intermediate scores (semantic, keyword, reranker)
   - Display full chunk similarity rankings
   - Debug why a rule was/wasn't retrieved
   - Chunk metadata visualization

### Implementation Guide

Each feature has a corresponding module stub:

```python
# For conversation memory:
# - Add messages context window to generator
# - Implement conversation summarization

# For query rewriting:
# - Add query_rewriter.py module
# - Integrate with retriever

# For feedback:
# - Add feedback_logger.py module
# - Store in feedback.json

# For debugging:
# - Add debug_dashboard.py (Streamlit page)
# - Export intermediate scores from retriever
```

---

## Deployment (Optional)

### Deploy to Streamlit Cloud

1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Click "New app" → Select repository
4. Set main file: `app.py`
5. Add secrets in Streamlit Cloud dashboard:
   ```
   ANTHROPIC_API_KEY = your_key_here
   ```
6. Deploy!

### Deploy Locally (Production)

```bash
# Use a production server
pip install gunicorn

# Or use Docker:
# docker build -t nba-rag .
# docker run -e ANTHROPIC_API_KEY=... -p 8501:8501 nba-rag
```

---

## Performance Monitoring

### Track System Health

**Metrics to monitor:**
- Average response time per query
- Retrieval accuracy (manual spot checks)
- LLM answer quality (user feedback)
- Error rate
- API cost (Claude calls)

**Optimizations:**
- Cache popular queries
- Batch similar questions
- Monitor API quota usage

---

## Support & Documentation

### Additional Resources

- **Streamlit docs:** https://docs.streamlit.io/
- **Anthropic docs:** https://docs.anthropic.com/
- **SentenceTransformers:** https://sbert.net/
- **FAISS:** https://github.com/facebookresearch/faiss

### Getting Help

1. Check the troubleshooting section above
2. Review error messages in Streamlit logs
3. Check module docstrings (e.g., `help(NBARetriever)`)
4. Refer to config.py for all settings

---

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Set API key: Create `.env` file
3. ✅ Run app: `streamlit run app.py`
4. ✅ Test with example questions
5. ✅ Customize settings as needed
6. ✅ Deploy (optional)

---

**Happy RAG-ing! 🏀**

---

Generated: June 10, 2026  
Version: 1.0  
Status: Production-Ready
