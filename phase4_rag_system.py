"""
Phase 4: Complete RAG System
Retrieval + Answer Generation + Citations.
"""

from typing import Dict, List, Optional
import json
from datetime import datetime

from phase4_retrieval import RetrievalPipeline
from phase4_prompts import (
    get_system_prompt,
    get_user_prompt,
)


class RAGSystem:
    """Complete RAG system: retrieval + generation + citations."""

    def __init__(self):
        """Initialize RAG system."""
        self.retrieval = RetrievalPipeline()
        self.llm_client = None
        self.setup_llm()

    def setup_llm(self):
        """Initialize LLM client (Claude via Anthropic SDK)."""
        try:
            import anthropic
            self.llm_client = anthropic.Anthropic()
            print("✅ Claude API client initialized")
        except ImportError:
            print("❌ anthropic package not found")
            print("   Install with: pip install anthropic")
            raise

    def setup(self):
        """Setup retrieval pipeline."""
        print()
        self.retrieval.setup()
        print()

    def answer_question(
        self,
        question: str,
        top_k: int = 5,
        model: str = "claude-opus-4-8",
        temperature: float = 0.3,
    ) -> Dict:
        """
        Answer a question using RAG.

        Args:
            question: User question
            top_k: Number of chunks to retrieve
            model: Claude model to use
            temperature: LLM temperature (lower = more deterministic)

        Returns:
            Dictionary with answer, citations, and metadata
        """
        # Step 1: Retrieve relevant chunks
        retrieved_chunks = self.retrieval.retrieve(
            question,
            top_k=top_k,
            verbose=False
        )

        if not retrieved_chunks:
            return {
                "question": question,
                "answer": "I could not find relevant NBA rules information to answer this question.",
                "citations": [],
                "retrieved_chunks": [],
                "model": model,
                "confidence": 0.0,
            }

        # Step 2: Format context
        context = self.retrieval.format_context(retrieved_chunks)

        # Step 3: Create prompt
        system_prompt = get_system_prompt()
        user_prompt = get_user_prompt(question, context)

        # Step 4: Call LLM
        try:
            response = self.llm_client.messages.create(
                model=model,
                max_tokens=1024,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
            )

            answer = response.content[0].text

        except Exception as e:
            print(f"❌ LLM error: {e}")
            return {
                "question": question,
                "answer": f"Error generating answer: {str(e)}",
                "citations": [],
                "retrieved_chunks": [],
                "model": model,
                "error": str(e),
            }

        # Step 5: Extract citations
        citations = self.retrieval.get_citation_metadata(retrieved_chunks)

        # Step 6: Calculate confidence
        confidence = self._calculate_confidence(
            answer,
            retrieved_chunks
        )

        return {
            "question": question,
            "answer": answer,
            "citations": citations,
            "retrieved_chunks": [
                {
                    "chunk_id": c['chunk_id'],
                    "citation": c['citation'],
                    "text_preview": c['text'][:200],
                    "similarity_score": c['similarity_score'],
                }
                for c in retrieved_chunks
            ],
            "model": model,
            "temperature": temperature,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_confidence(
        self,
        answer: str,
        retrieved_chunks: List[Dict]
    ) -> float:
        """
        Calculate confidence score (0-1) for the answer.

        Args:
            answer: Generated answer
            retrieved_chunks: Retrieved chunks

        Returns:
            Confidence score
        """
        confidence = 0.0

        # Check for "could not find" phrases (lower confidence)
        cannot_find_phrases = [
            "could not find",
            "not found",
            "no information",
            "insufficient",
        ]

        if any(phrase in answer.lower() for phrase in cannot_find_phrases):
            return 0.3

        # Average similarity score of top chunks
        if retrieved_chunks:
            avg_similarity = sum(
                c['similarity_score'] for c in retrieved_chunks[:3]
            ) / min(3, len(retrieved_chunks))
            confidence = avg_similarity

        # Bonus for explicit citations
        citation_count = answer.lower().count("rule ")
        if citation_count >= 2:
            confidence = min(1.0, confidence + 0.1)

        return min(1.0, confidence)

    def print_answer(self, result: Dict):
        """Print formatted answer."""
        print()
        print("=" * 80)
        print(f"Question: {result['question']}")
        print("=" * 80)
        print()

        print("Answer:")
        print("-" * 80)
        print(result['answer'])
        print()

        print("Citations:")
        print("-" * 80)
        for citation in result['citations']:
            print(f"  • {citation['citation']}")
            print(f"    (Similarity: {citation['similarity_score']:.1%})")
        print()

        print(f"Confidence: {result['confidence']:.1%}")
        print()

    def save_result(self, result: Dict, output_file: str = None):
        """Save result to JSON file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/rag_result_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"✅ Result saved to {output_file}")


def main():
    """Test RAG system."""
    # Initialize RAG
    print()
    rag = RAGSystem()
    rag.setup()

    print()
    print("=" * 80)
    print("RAG SYSTEM TEST")
    print("=" * 80)

    # Test questions
    test_questions = [
        "What is traveling in basketball?",
        "When is a technical foul called?",
        "How many timeouts does each team get?",
    ]

    for question in test_questions:
        print()
        result = rag.answer_question(question, top_k=5)
        rag.print_answer(result)

        # Save result
        rag.save_result(result)


if __name__ == "__main__":
    main()
