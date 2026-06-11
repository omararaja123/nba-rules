"""
NBA Rules RAG Chatbot - Streamlit Application
A production-quality RAG interface for querying the official NBA rulebook
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import streamlit as st
from retriever import NBARetriever
from generator import AnswerGenerator
from config import (
    PAGE_TITLE,
    PAGE_ICON,
    LAYOUT,
    WELCOME_MESSAGE,
    ABOUT_MESSAGE,
    TOP_K_RETRIEVAL,
)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {
        padding-top: 0;
    }

    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        gap: 1rem;
    }

    .chat-message.user {
        background-color: #e3f2fd;
        flex-direction: row-reverse;
    }

    .chat-message.assistant {
        background-color: #f5f5f5;
    }

    .chat-content {
        flex: 1;
    }

    .source-panel {
        background-color: #fafafa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1976d2;
    }

    .chunk-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
    }

    .relevance-score {
        display: inline-block;
        background-color: #4caf50;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        margin-left: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'retriever' not in st.session_state:
    with st.spinner("Loading retrieval system..."):
        st.session_state.retriever = NBARetriever()

if 'generator' not in st.session_state:
    try:
        st.session_state.generator = AnswerGenerator()
    except ValueError as e:
        st.error(f"Error initializing generator: {str(e)}")
        st.info("Please set the ANTHROPIC_API_KEY environment variable.")
        st.stop()

if 'retrieved_chunks' not in st.session_state:
    st.session_state.retrieved_chunks = None

if 'answer_cache' not in st.session_state:
    st.session_state.answer_cache = {}  # Cache for question answers

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.title("🎯 Demo & Settings")

    # Load test questions for demo
    try:
        with open('data/100_test_questions.json', 'r') as f:
            test_data = json.load(f)
            test_questions = test_data if isinstance(test_data, list) else test_data.get('questions', [])
    except:
        test_questions = []

    # Test Questions Browser - PROMINENT
    st.markdown("### 🧪 Demo Questions")
    st.markdown("Click any question to load it →")

    if test_questions:
        search_term = st.text_input("🔍 Search (e.g., 'traveling')", placeholder="", label_visibility="collapsed")

        filtered_qs = [q for q in test_questions
                      if search_term.lower() in q.get('question', '').lower()]

        if filtered_qs:
            for i, q in enumerate(filtered_qs[:15]):  # Show top 15
                question_text = q.get('question', '')
                rule_num = q.get('rule', '')

                # Cleaner button layout
                if st.button(
                    f"{question_text[:55]}{'...' if len(question_text) > 55 else ''}",
                    key=f"test_q_{i}_{search_term}",
                    use_container_width=True,
                    type="secondary"
                ):
                    st.session_state.selected_test_question = question_text
                    st.rerun()

            if len(filtered_qs) > 15:
                st.caption(f"📋 Showing 15 of {len(filtered_qs)} matches")
        else:
            st.info("No questions match your search")
    else:
        st.info("Questions not loaded")

    st.divider()

    # Display settings - CLEAN
    st.markdown("### ⚙️ Settings")
    show_relevance = st.checkbox("📊 Show relevance scores", value=True)
    show_all_chunks = st.checkbox("📎 Show chunk details", value=True)

    st.divider()

    # System info
    st.subheader("System Info")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Chunks", "112")
    with col2:
        st.metric("Retrieval Acc.", "90%")

    st.metric("LLM Quality", "4.77/5.0")
    st.metric("Test Coverage", "160 Q")

    st.divider()

    # About section
    with st.expander("ℹ️ About This System", expanded=False):
        st.markdown(ABOUT_MESSAGE)

    st.divider()

    # Clear chat
    if st.button("🔄 Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.retrieved_chunks = None
        st.rerun()

# ============================================================================
# MAIN CONTENT - HEADER
# ============================================================================

st.markdown("# 🏀 NBA Rules Assistant")
st.markdown(
    "Get instant, cited answers to any NBA rules question. "
    "**Type your own** or **try a demo question** from the sidebar."
)
st.divider()

# ============================================================================
# MAIN CONTENT - CHAT DISPLAY
# ============================================================================

col1, col2 = st.columns([1.5, 1], gap="medium")

with col1:
    # Display chat history
    chat_container = st.container(height=500)
    with chat_container:
        if not st.session_state.messages:
            st.info(
                "👋 **Start by typing a question** or select a demo question from the sidebar →\n\n"
                "Examples: \"What is traveling?\", \"How many timeouts?\" or click 🧪 **Try Demo Questions**"
            )

        for message in st.session_state.messages:
            if message["role"] == "user":
                with st.chat_message("user", avatar="👤"):
                    st.write(message["content"])

            else:  # assistant
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(message["content"])

                    # Display sources for assistant messages
                    if message.get("chunks"):
                        with st.expander(
                            f"📎 Source Chunks ({len(message['chunks'])} used)",
                            expanded=False
                        ):
                            for i, chunk in enumerate(message["chunks"], 1):
                                st.markdown(
                                    f"**[{i}] Rule {chunk['rule_number']}: "
                                    f"{chunk['rule_title']}**"
                                )
                                st.caption(
                                    f"{chunk['section_title']} • Page {chunk['page_number']}"
                                )
                                if show_relevance:
                                    relevance = (
                                        f"Relevance: "
                                        f"{chunk.get('relevance_score', 0):.1%}"
                                    )
                                    st.caption(relevance)
                                st.text(chunk["text"][:500] + "...")
                                st.divider()

    # Chat input - PROMINENT
    st.markdown("---")
    st.write("**Your Question:**")

    # Chat input is always available for freeform questions
    user_input = st.chat_input(
        "What do you want to know about NBA rules?",
        key="chat_input"
    )

    # Check if a test question was selected (click from sidebar)
    if 'selected_test_question' in st.session_state and st.session_state.selected_test_question:
        user_input = st.session_state.selected_test_question
        st.session_state.selected_test_question = None  # Clear it

    if user_input:
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        # Show user message
        with st.chat_message("user", avatar="👤"):
            st.write(user_input)

        # Check cache first
        cache_key = user_input.lower().strip()
        if cache_key in st.session_state.answer_cache:
            # Return cached result
            cached_result = st.session_state.answer_cache[cache_key]
            result = cached_result['result']
            retrieved_chunks = cached_result['chunks']
            st.session_state.retrieved_chunks = retrieved_chunks

            with st.chat_message("assistant", avatar="🤖"):
                st.write(f"**[Cached]** {result['answer']}")

                with st.expander(
                    f"📎 Sources ({result['chunks_used']} chunks used)",
                    expanded=False
                ):
                    for i, chunk in enumerate(retrieved_chunks, 1):
                        st.markdown(
                            f"**[{i}] Rule {chunk['rule_number']}: "
                            f"{chunk['rule_title']}**"
                        )
                        st.caption(
                            f"{chunk['section_title']} • Page {chunk['page_number']}"
                        )
                        if show_relevance:
                            relevance = f"Relevance: {chunk['relevance_score']:.1%}"
                            st.caption(relevance)
                        st.text(chunk["text"][:500] + "...")
                        st.divider()

            st.session_state.messages.append({
                "role": "assistant",
                "content": result['answer'],
                "chunks": retrieved_chunks
            })
            st.rerun()

        # Not cached - retrieve and generate
        # Retrieve relevant chunks
        with st.spinner("🔍 Searching rulebook..."):
            retrieved_chunks = st.session_state.retriever.retrieve(user_input)

        st.session_state.retrieved_chunks = retrieved_chunks

        # Format context for LLM
        context = st.session_state.retriever.format_context(retrieved_chunks)

        # Generate answer
        with st.spinner("✍️ Generating answer (⚡ first time, ⚡⚡ cached next time)..."):
            result = st.session_state.generator.generate_answer(
                user_input,
                context,
                retrieved_chunks
            )

        # Display assistant response
        with st.chat_message("assistant", avatar="🤖"):
            if result['success']:
                st.write(result['answer'])

                # Display sources
                with st.expander(
                    f"📎 Sources ({result['chunks_used']} chunks used)",
                    expanded=False
                ):
                    for i, chunk in enumerate(retrieved_chunks, 1):
                        st.markdown(
                            f"**[{i}] Rule {chunk['rule_number']}: "
                            f"{chunk['rule_title']}**"
                        )
                        st.caption(
                            f"{chunk['section_title']} • Page {chunk['page_number']}"
                        )
                        if show_relevance:
                            relevance = f"Relevance: {chunk['relevance_score']:.1%}"
                            st.caption(relevance)
                        st.text(chunk["text"][:500] + "...")
                        st.divider()

            else:
                st.error(f"Error: {result['error']}")

        # Cache the result for future use
        if result['success']:
            st.session_state.answer_cache[cache_key] = {
                'result': result,
                'chunks': retrieved_chunks
            }

        # Add assistant message to history
        st.session_state.messages.append({
            "role": "assistant",
            "content": result['answer'],
            "chunks": retrieved_chunks if result['success'] else []
        })

        st.rerun()

with col2:
    st.markdown("## 📎 Source Chunks")

    if st.session_state.retrieved_chunks:
        st.success(
            f"✅ {len(st.session_state.retrieved_chunks)} rule sections retrieved"
        )

        for i, chunk in enumerate(st.session_state.retrieved_chunks, 1):
            with st.container(border=True):
                # Chunk header
                st.markdown(
                    f"**[{i}] Rule {chunk['rule_number']}: {chunk['rule_title']}**"
                )

                # Metadata
                st.caption(
                    f"🔖 {chunk['section_title']} • 📄 Page {chunk['page_number']}"
                )

                # Relevance score
                if show_relevance:
                    relevance_pct = chunk['relevance_score'] * 100
                    st.metric(
                        "Relevance Score",
                        f"{relevance_pct:.1f}%",
                        delta=None
                    )

                # Chunk text
                st.text(chunk["text"])

                st.divider()

    else:
        st.info(
            "📋 Retrieved source chunks will appear here as you ask questions. "
            "This panel shows the exact rulebook sections used to generate answers."
        )

        # Example chunks
        st.markdown("### Example NBA Rules")
        st.markdown(
            """
            - **Rule 1:** Court Dimensions
            - **Rule 4:** Traveling
            - **Rule 6:** Fouls
            - **Rule 10:** Free Throws
            - **Rule 12:** Timeouts

            Try asking about any rule above!
            """
        )

# (Welcome message shown in chat container)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
col_left, col_center, col_right = st.columns(3)

with col_left:
    st.caption("**Data:** Official 2025–26 NBA Playing Rules")

with col_center:
    st.caption("**Accuracy:** 90% retrieval | 4.77/5.0 quality")

with col_right:
    st.caption("**Speed:** ⚡ ~3-5s first | ⚡⚡ instant cached")
