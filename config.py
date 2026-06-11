"""
Configuration settings for NBA Rules RAG Chatbot
"""

import os

# ============================================================================
# PATHS & FILES
# ============================================================================

DATA_DIR = "data"
CHUNKS_FILE = os.path.join(DATA_DIR, "09_stable_chunks_aggressive_rebuild.json")
EMBEDDINGS_FILE = os.path.join(DATA_DIR, "10_embeddings_aggressive_rebuild.npy")

# ============================================================================
# RETRIEVAL SETTINGS
# ============================================================================

# Number of chunks to retrieve for each question
TOP_K_RETRIEVAL = 3

# Hybrid retrieval weights (semantic + BM25)
SEMANTIC_WEIGHT = 0.7
KEYWORD_WEIGHT = 0.3

# Re-ranking settings
RERANKER_WEIGHT = 0.2  # Weight for cross-encoder re-ranking (0.0-1.0)
HYBRID_WEIGHT = 0.8    # Weight for hybrid retrieval (1-RERANKER_WEIGHT)

# ============================================================================
# LLM SETTINGS
# ============================================================================

LLM_MODEL = "claude-haiku-4-5-20251001"  # Fast (2-3x faster than Opus, still accurate)
LLM_MAX_TOKENS = 500
LLM_TEMPERATURE = 0.7

# ============================================================================
# EMBEDDING SETTINGS
# ============================================================================

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# ============================================================================
# UI SETTINGS
# ============================================================================

PAGE_TITLE = "NBA Rules RAG Chatbot"
PAGE_ICON = "🏀"
LAYOUT = "wide"

WELCOME_MESSAGE = """
# 🏀 NBA Rules Chatbot

Welcome! Ask any question about the Official 2025–26 NBA Playing Rules.

**How it works:**
- Your question is matched against the NBA rulebook using advanced retrieval
- The most relevant rule sections are retrieved
- An AI assistant generates an answer grounded in the official rules
- Source chunks are shown on the right for complete transparency

**Examples you can ask:**
- "What is traveling?"
- "When is a foul called?"
- "What are the court dimensions?"
- "How many timeouts does each team get?"

*All answers are grounded in the official NBA rulebook.*
"""

ABOUT_MESSAGE = """
### About This System

This chatbot uses **Retrieval-Augmented Generation (RAG)** to answer questions about NBA rules:

1. **Retrieval:** Your question is compared against 112 optimized chunks from the NBA rulebook
2. **Ranking:** Results are scored using both semantic similarity and keyword matching
3. **Generation:** The top-3 most relevant chunks are passed to an AI model
4. **Answer:** Claude generates a grounded answer with citations
5. **Transparency:** You can see exactly which rule sections were used

**Performance:**
- Retrieval Accuracy: 90%
- LLM Answer Quality: 4.77/5.0
- Test Coverage: 160+ questions

**Architecture:**
- Embeddings: SentenceTransformers (384D)
- Vector Search: FAISS
- Retrieval: Hybrid (semantic + keyword)
- Re-ranking: Cross-encoder
- LLM: Claude Opus
"""

# ============================================================================
# DISPLAY SETTINGS
# ============================================================================

# Maximum characters to display in source chunk preview
CHUNK_PREVIEW_LENGTH = 200

# Confidence threshold for showing relevance scores
SHOW_RELEVANCE_SCORE = True

