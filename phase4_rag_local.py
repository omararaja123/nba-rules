"""
Phase 4: RAG System with Local LLM (No API Key Required)
Uses Ollama or similar local model servers.
"""

from typing import Dict, List, Optional
import json
from datetime import datetime
import requests

from phase4_retrieval import RetrievalPipeline
from phase4_prompts import (
    get_system_prompt,
    get_user_prompt,
)


class LocalRAGSystem:
    """RAG system using local LLM (Ollama, LM Studio, etc.)."""

    def __init__(self, model: str = "mistral", base_url: str = "http://localhost:11434"):
        """
        Initialize local RAG system.

        Args:
            model: Model name (mistral, llama2, neural-chat, etc.)
            base_url: Local LLM server URL
        """
        self.retrieval = RetrievalPipeline()
        self.model = model
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/generate"

        print(f"Configured for local model: {model}")
        print(f"Server: {base_url}")

    def setup(self):
        """Setup retrieval pipeline."""
        print()
        print("=" * 80)
        print("PHASE 4: LOCAL RAG SYSTEM (No API Key Required)")
        print("=" * 80)
        print()

        print("Setting up retrieval pipeline...")
        self.retrieval.setup()

        # Test connection to local LLM
        if not self.test_connection():
            print()
            print("⚠️  WARNING: Could not connect to local LLM server")
            print()
            print("To use this system, you need to run a local LLM server.")
            print()
            print("Option 1: Ollama (Recommended)")
            print("  1. Download: https://ollama.ai")
            print("  2. Install and run: ollama serve")
            print("  3. In another terminal: ollama pull mistral")
            print()
            print("Option 2: LM Studio")
            print("  1. Download: https://lmstudio.ai")
            print("  2. Load a model and start server")
            print()
            print("Option 3: GPT4All")
            print("  1. Download: https://gpt4all.io")
            print("  2. Load model and enable API server")
            print()
            return False

        print("✅ Connected to local LLM server")
        print()
        return True

    def test_connection(self) -> bool:
        """Test connection to local LLM server."""
        try:
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.model,
                    "prompt": "test",
                    "stream": False,
                },
                timeout=5,
            )
            return response.status_code == 200
        except Exception as e:
            return False

    def answer_question(
        self,
        question: str,
        top_k: int = 5,
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> Dict:
        """
        Answer a question using local LLM.

        Args:
            question: User question
            top_k: Number of chunks to retrieve
            temperature: LLM temperature (0-1)
            max_tokens: Max tokens in response

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
                "model": self.model,
                "confidence": 0.0,
                "source": "local",
            }

        # Step 2: Format context
        context = self.retrieval.format_context(retrieved_chunks)

        # Step 3: Create prompt
        system_prompt = get_system_prompt()
        user_prompt = get_user_prompt(question, context)

        # Combine for local LLM (many don't support system role)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Step 4: Call local LLM
        try:
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                timeout=120,  # Local inference can be slower
            )

            if response.status_code != 200:
                return {
                    "question": question,
                    "answer": f"Error: {response.text}",
                    "citations": [],
                    "retrieved_chunks": [],
                    "model": self.model,
                    "error": response.text,
                }

            answer = response.json().get("response", "").strip()

        except requests.exceptions.ConnectionError:
            print("\n❌ Could not connect to local LLM server")
            print("Make sure your local LLM server is running on " + self.base_url)
            return {
                "question": question,
                "answer": "Error: Could not connect to local LLM server",
                "citations": [],
                "retrieved_chunks": [],
                "model": self.model,
                "error": "Connection refused",
            }
        except Exception as e:
            return {
                "question": question,
                "answer": f"Error generating answer: {str(e)}",
                "citations": [],
                "retrieved_chunks": [],
                "model": self.model,
                "error": str(e),
            }

        # Step 5: Extract citations
        citations = self.retrieval.get_citation_metadata(retrieved_chunks)

        # Step 6: Calculate confidence
        confidence = self._calculate_confidence(answer, retrieved_chunks)

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
            "model": self.model,
            "temperature": temperature,
            "confidence": confidence,
            "source": "local",
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_confidence(
        self,
        answer: str,
        retrieved_chunks: List[Dict]
    ) -> float:
        """Calculate confidence score (0-1)."""
        if not answer or "error" in answer.lower():
            return 0.0

        if "could not find" in answer.lower():
            return 0.3

        # Average similarity score
        if retrieved_chunks:
            avg_similarity = sum(
                c['similarity_score'] for c in retrieved_chunks[:3]
            ) / min(3, len(retrieved_chunks))
            confidence = avg_similarity

            # Bonus for citations
            if "Rule" in answer:
                confidence = min(1.0, confidence + 0.1)

            return min(1.0, confidence)

        return 0.5

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
        if result['citations']:
            for citation in result['citations']:
                print(f"  • {citation['citation']}")
                print(f"    (Similarity: {citation['similarity_score']:.1%})")
        else:
            print("  (No citations)")
        print()

        print(f"Model: {result['model']}")
        print(f"Confidence: {result['confidence']:.1%}")
        print()

    def save_result(self, result: Dict, output_file: str = None):
        """Save result to JSON."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/rag_local_result_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"✅ Result saved to {output_file}")


def main():
    """Test local RAG system."""
    # Initialize with Ollama (default)
    rag = LocalRAGSystem(
        model="mistral",
        base_url="http://localhost:11434"
    )

    # Setup and check connection
    if not rag.setup():
        print()
        print("Please start your local LLM server and try again.")
        return

    print()
    print("=" * 80)
    print("LOCAL RAG SYSTEM TEST")
    print("=" * 80)

    # Test questions
    test_questions = [
        "What is traveling in basketball?",
        "When is a technical foul called?",
        "How many timeouts does each team get?",
    ]

    for question in test_questions:
        print()
        print(f"Processing: {question}")
        print("(This may take a minute on local hardware...)")
        print()

        result = rag.answer_question(question, top_k=5)

        if "error" in result:
            print(f"❌ Error: {result.get('error')}")
        else:
            rag.print_answer(result)
            rag.save_result(result)


if __name__ == "__main__":
    main()
