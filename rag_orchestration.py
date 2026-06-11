"""
LangGraph RAG Orchestration
Production-grade orchestration of NBA Rules RAG using LangChain and LangGraph.

Combines:
- LangChain: Individual operation chains (retrieval, formatting, LLM)
- LangGraph: Orchestrates full workflow with structured state management
- Components: Reusable retriever, generator, and evaluation modules
"""

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from retriever import NBARetriever
from generator import AnswerGenerator


class RAGState(TypedDict):
    """State object for the RAG workflow graph."""
    question: str
    retrieved_chunks: List[Dict[str, Any]]
    context: str
    answer: str
    citations: List[Dict[str, Any]]
    chunks_used: int
    success: bool
    error: str


class RAGOrchestration:
    """
    LangGraph-based RAG orchestration for NBA Rules system.

    Workflow:
        [START] → retrieve → format_context → generate → extract_citations → [END]

    Each node is independent and can be tested, monitored, and modified separately.
    """

    def __init__(self):
        """Initialize orchestration with retriever and generator."""
        self.retriever = NBARetriever()
        self.generator = AnswerGenerator()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow DAG.

        Graph structure:
            retrieve: Takes question, returns top-3 chunks
            format_context: Formats chunks into LLM-readable text
            generate: Calls Claude with context
            extract_citations: Extracts rule metadata from chunks

        Returns:
            Compiled graph ready for invocation
        """
        workflow = StateGraph(RAGState)

        # Node 1: Retrieve relevant chunks
        workflow.add_node("retrieve", self._retrieve_node)

        # Node 2: Format context for LLM
        workflow.add_node("format_context", self._format_context_node)

        # Node 3: Generate answer with Claude
        workflow.add_node("generate", self._generate_node)

        # Node 4: Extract and format citations
        workflow.add_node("extract_citations", self._extract_citations_node)

        # Define edges (workflow flow)
        workflow.add_edge(START, "retrieve")
        workflow.add_edge("retrieve", "format_context")
        workflow.add_edge("format_context", "generate")
        workflow.add_edge("generate", "extract_citations")
        workflow.add_edge("extract_citations", END)

        # Compile into executable graph
        return workflow.compile()

    def _retrieve_node(self, state: RAGState) -> RAGState:
        """
        Node 1: Retrieve top-3 most relevant rule chunks.

        Input: state['question']
        Output: state['retrieved_chunks']

        Process:
            1. Encode question to vector
            2. Semantic search (FAISS)
            3. Keyword search (BM25)
            4. Hybrid scoring (70% semantic + 30% keyword)
            5. Cross-encoder re-ranking
            6. Return top-3
        """
        try:
            retrieved_chunks = self.retriever.retrieve(state["question"])
            state["retrieved_chunks"] = retrieved_chunks
            return state
        except Exception as e:
            state["error"] = f"Retrieval failed: {str(e)}"
            state["success"] = False
            return state

    def _format_context_node(self, state: RAGState) -> RAGState:
        """
        Node 2: Format retrieved chunks into LLM context.

        Input: state['retrieved_chunks']
        Output: state['context']

        Process:
            1. Organize chunks by rule number
            2. Add metadata (section, page)
            3. Create readable text for Claude
        """
        try:
            context = self.retriever.format_context(state["retrieved_chunks"])
            state["context"] = context
            return state
        except Exception as e:
            state["error"] = f"Context formatting failed: {str(e)}"
            state["success"] = False
            return state

    def _generate_node(self, state: RAGState) -> RAGState:
        """
        Node 3: Generate answer using Claude LLM.

        Input: state['question'], state['context'], state['retrieved_chunks']
        Output: state['answer'], state['chunks_used']

        Process:
            1. Build system prompt (grounding instructions)
            2. Format user message with context + question
            3. Call Claude API
            4. Extract answer text
            5. Record number of chunks used
        """
        try:
            result = self.generator.generate_answer(
                question=state["question"],
                context=state["context"],
                chunks=state["retrieved_chunks"]
            )

            if result["success"]:
                state["answer"] = result["answer"]
                state["chunks_used"] = result["chunks_used"]
                state["success"] = True
            else:
                state["error"] = result.get("error", "Generation failed")
                state["success"] = False

            return state
        except Exception as e:
            state["error"] = f"Answer generation failed: {str(e)}"
            state["success"] = False
            return state

    def _extract_citations_node(self, state: RAGState) -> RAGState:
        """
        Node 4: Extract and format citations from retrieved chunks.

        Input: state['retrieved_chunks']
        Output: state['citations']

        Process:
            1. Get metadata from each chunk
            2. Format as citation objects
            3. Store for display/logging
        """
        try:
            citations = self.generator._extract_citations(state["retrieved_chunks"])
            state["citations"] = citations
            return state
        except Exception as e:
            # Citation extraction is optional, don't fail the whole workflow
            state["citations"] = []
            return state

    def invoke(self, question: str) -> Dict[str, Any]:
        """
        Execute the RAG workflow for a given question.

        Args:
            question: User's question about NBA rules

        Returns:
            Dictionary containing:
                - answer: Generated answer grounded in rulebook
                - chunks: List of rule chunks used
                - citations: Formatted citations
                - success: Whether generation succeeded
                - error: Error message if failed

        Process:
            1. Initialize state with question
            2. Execute workflow graph
            3. Return final state with answer

        Example:
            rag = RAGOrchestration()
            result = rag.invoke("What is traveling?")
            print(result['answer'])
            print(result['citations'])
        """
        initial_state: RAGState = {
            "question": question,
            "retrieved_chunks": [],
            "context": "",
            "answer": "",
            "citations": [],
            "chunks_used": 0,
            "success": False,
            "error": ""
        }

        # Execute the graph
        final_state = self.graph.invoke(initial_state)

        # Format output
        return {
            "success": final_state["success"],
            "answer": final_state["answer"],
            "chunks": final_state["retrieved_chunks"],
            "citations": final_state["citations"],
            "chunks_used": final_state["chunks_used"],
            "error": final_state["error"]
        }

    def get_graph(self):
        """
        Return the compiled LangGraph for inspection/visualization.

        Useful for:
            - Debugging workflow
            - Visualizing graph structure
            - Testing individual nodes
        """
        return self.graph


# Example usage
if __name__ == "__main__":
    # Initialize RAG orchestration
    rag = RAGOrchestration()

    # Example question
    question = "What is traveling?"

    print("=" * 80)
    print(f"Question: {question}")
    print("=" * 80)

    # Invoke the workflow
    result = rag.invoke(question)

    # Display results
    print(f"\nAnswer: {result['answer']}")
    print(f"\nChunks Used: {result['chunks_used']}")
    print(f"Success: {result['success']}")

    if result['citations']:
        print(f"\nCitations:")
        for citation in result['citations']:
            print(f"  - {citation}")
