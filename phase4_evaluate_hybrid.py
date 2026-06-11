"""
Phase 4: Evaluation with Hybrid Retrieval
Compare hybrid search vs pure semantic search.
"""

import json
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env FIRST
load_dotenv()

from phase4_rag_openai import OpenAIRAGSystem
from phase4_retrieval_hybrid import HybridRetrieval


class HybridRAGSystem:
    """RAG system using hybrid retrieval."""

    def __init__(self, model: str = "gpt-3.5-turbo"):
        """Initialize hybrid RAG."""
        self.retrieval = HybridRetrieval()
        self.model = model
        self.llm_client = None
        self.setup_llm()

    def setup_llm(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            self.llm_client = OpenAI()
            print("✅ OpenAI API client initialized")
            print(f"   Model: {self.model}")
        except ImportError:
            print("❌ openai package not found")
            raise
        except Exception as e:
            print(f"❌ OpenAI initialization error: {e}")
            raise

    def setup(self):
        """Setup retrieval pipeline."""
        print()
        self.retrieval.setup()
        print()

    def answer_question(self, question: str, top_k: int = 5) -> Dict:
        """Answer using hybrid retrieval."""
        from phase4_prompts import get_system_prompt, get_user_prompt

        # Retrieve using hybrid search
        retrieved_chunks = self.retrieval.retrieve_hybrid(
            question,
            top_k=top_k,
            semantic_weight=0.7,
            keyword_weight=0.3,
            verbose=False,
        )

        if not retrieved_chunks:
            return {
                "question": question,
                "answer": "I could not find relevant NBA rules information.",
                "citations": [],
                "model": self.model,
                "confidence": 0.0,
            }

        # Format context
        context = "Retrieved NBA Rules Excerpts:\n"
        context += "=" * 80 + "\n\n"

        for i, chunk in enumerate(retrieved_chunks, 1):
            context += f"[{i}] {chunk['citation']}\n"
            context += f"Hybrid Score: {chunk['combined_score']:.2%}\n"
            context += "-" * 80 + "\n"
            context += chunk['text']
            context += "\n\n"

        # Create prompts
        system_prompt = get_system_prompt()
        user_prompt = get_user_prompt(question, context)

        # Call LLM
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            answer = response.choices[0].message.content

        except Exception as e:
            return {
                "question": question,
                "answer": f"Error: {str(e)}",
                "citations": [],
                "model": self.model,
                "error": str(e),
            }

        # Extract citations
        citations = [
            {
                "chunk_id": c['chunk_id'],
                "citation": c['citation'],
                "rule_number": c['rule_number'],
                "section_title": c['section_title'],
                "combined_score": c['combined_score'],
            }
            for c in retrieved_chunks
        ]

        # Calculate confidence
        confidence = self._calculate_confidence(answer, retrieved_chunks)

        return {
            "question": question,
            "answer": answer,
            "citations": citations,
            "retrieved_chunks": [
                {
                    "chunk_id": c['chunk_id'],
                    "citation": c['citation'],
                    "combined_score": c['combined_score'],
                    "semantic_score": c['semantic_score'],
                    "keyword_score": c['keyword_score'],
                }
                for c in retrieved_chunks
            ],
            "model": self.model,
            "confidence": confidence,
        }

    def _calculate_confidence(self, answer: str, chunks: List[Dict]) -> float:
        """Calculate confidence score."""
        if "could not find" in answer.lower() or "error" in answer.lower():
            return 0.3

        if chunks:
            avg_score = sum(c['combined_score'] for c in chunks[:3]) / min(3, len(chunks))
            confidence = avg_score

            if "Rule" in answer:
                confidence = min(1.0, confidence + 0.1)

            return min(1.0, confidence)

        return 0.5


class HybridRAGEvaluator:
    """Evaluate hybrid RAG system."""

    def __init__(self, model: str = "gpt-3.5-turbo"):
        """Initialize evaluator."""
        self.rag = HybridRAGSystem(model=model)
        self.results = []

        self.benchmark_questions = [
            {
                "id": 1,
                "question": "What actions constitute a traveling violation under NBA rules?",
                "expected_rule": "Rule 4",
            },
            {
                "id": 2,
                "question": "When is defensive goaltending called and what happens after the violation?",
                "expected_rule": "Rule 11",
            },
            {
                "id": 3,
                "question": "Which situations are reviewable using instant replay?",
                "expected_rule": "Rule 13",
            },
            {
                "id": 4,
                "question": "What behaviors can result in a technical foul being assessed?",
                "expected_rule": "Rule 12",
            },
            {
                "id": 5,
                "question": "How many timeouts does a team receive during a regulation NBA game?",
                "expected_rule": "Rule 5",
            },
            {
                "id": 6,
                "question": "When does the shot clock reset to 14 seconds instead of 24 seconds?",
                "expected_rule": "Rule 7",
            },
            {
                "id": 7,
                "question": "In what situations is a jump ball used to resume play?",
                "expected_rule": "Rule 6",
            },
            {
                "id": 8,
                "question": "What is the difference between a Flagrant Foul Penalty 1 and Penalty 2?",
                "expected_rule": "Rule 12",
            },
            {
                "id": 9,
                "question": "When is a player considered out of bounds?",
                "expected_rule": "Rule 10",
            },
            {
                "id": 10,
                "question": "How many free throws are awarded for different types of personal fouls?",
                "expected_rule": "Rule 8",
            },
        ]

    def setup(self):
        """Setup RAG system."""
        print()
        self.rag.setup()
        print()

    def run_evaluation(self, verbose: bool = True) -> Dict:
        """Run evaluation on all 10 questions."""
        print("=" * 80)
        print("PHASE 4: HYBRID RETRIEVAL EVALUATION")
        print("=" * 80)
        print()

        print(f"Testing {len(self.benchmark_questions)} questions...")
        print(f"Model: {self.rag.model}")
        print(f"Retrieval: Hybrid (70% semantic + 30% keyword)")
        print()

        results = []

        for i, test_case in enumerate(self.benchmark_questions, 1):
            print(
                f"[{i}/{len(self.benchmark_questions)}] "
                f"Q: {test_case['question'][:50]}..."
            )

            # Generate answer
            rag_result = self.rag.answer_question(test_case['question'], top_k=5)

            # Evaluate
            evaluation = self._evaluate_single(rag_result, test_case)

            result = {
                "id": test_case['id'],
                "question": test_case['question'],
                "expected_rule": test_case['expected_rule'],
                "answer": rag_result['answer'],
                "citations": rag_result['citations'],
                "retrieved_chunks": rag_result['retrieved_chunks'],
                "confidence": rag_result['confidence'],
                **evaluation,
            }

            results.append(result)

            print(
                f"  → Faithfulness: {evaluation['faithfulness']}/5, "
                f"Relevance: {evaluation['relevance']}/5"
            )
            print()

        self.results = results
        return results

    def _evaluate_single(self, rag_result: Dict, test_case: Dict) -> Dict:
        """Evaluate a single answer."""
        answer = rag_result['answer']
        citations = rag_result['citations']
        expected_rule = test_case['expected_rule']

        faithfulness = self._score_faithfulness(answer, citations)
        relevance = self._score_relevance(answer, expected_rule)

        notes = []

        if "error" in answer.lower() or "could not find" in answer.lower():
            notes.append("System could not find information")
            faithfulness = min(faithfulness, 2)

        if not citations:
            notes.append("No citations")
            faithfulness = min(faithfulness, 2)

        if expected_rule.lower() not in answer.lower():
            notes.append(f"Missing {expected_rule}")
            relevance = min(relevance, 3)

        return {
            "faithfulness": faithfulness,
            "relevance": relevance,
            "notes": "; ".join(notes) if notes else "OK",
        }

    def _score_faithfulness(self, answer: str, citations: List[Dict]) -> int:
        """Score faithfulness (1-5)."""
        if not answer or "error" in answer.lower() or "could not find" in answer.lower():
            return 1

        score = 2

        if citations:
            score = 4
            if len(citations) >= 3:
                score = 5

        if "Rule" in answer and "Section" in answer:
            score = min(5, score + 1)

        return min(5, score)

    def _score_relevance(self, answer: str, expected_rule: str) -> int:
        """Score relevance (1-5)."""
        if not answer or "error" in answer.lower() or "could not find" in answer.lower():
            return 1

        answer_lower = answer.lower()

        if expected_rule.lower() in answer_lower:
            score = 4
            if len(answer.split()) > 50:
                score = 5
            return score
        else:
            return 2 if len(answer) > 20 else 1

    def print_results_table(self):
        """Print results table."""
        print()
        print("=" * 120)
        print("HYBRID RETRIEVAL RESULTS")
        print("=" * 120)
        print()

        print(
            f"{'#':>2} | {'Question':<40} | {'Faith':>5} | {'Rel':>3} | "
            f"{'Notes':<40}"
        )
        print("-" * 120)

        for result in self.results:
            question_short = result['question'][:40]
            faith = result['faithfulness']
            rel = result['relevance']
            notes = result['notes'][:38]

            print(
                f"{result['id']:2d} | {question_short:<40} | "
                f"{faith}/5    | {rel}/5 | {notes:<40}"
            )

        print()

    def print_metrics(self):
        """Print summary metrics."""
        if not self.results:
            print("No results")
            return

        faithfulness_scores = [r['faithfulness'] for r in self.results]
        relevance_scores = [r['relevance'] for r in self.results]

        avg_faith = sum(faithfulness_scores) / len(faithfulness_scores)
        avg_rel = sum(relevance_scores) / len(relevance_scores)

        faith_pct = (sum(1 for s in faithfulness_scores if s >= 4) / len(faithfulness_scores)) * 100
        rel_pct = (sum(1 for s in relevance_scores if s >= 4) / len(relevance_scores)) * 100

        print()
        print("=" * 80)
        print("METRICS SUMMARY")
        print("=" * 80)
        print()

        print(f"Average Faithfulness:    {avg_faith:.2f}/5.00")
        print(f"Average Relevance:       {avg_rel:.2f}/5.00")
        print()
        print(f"Faithfulness ≥ 4:        {faith_pct:.1f}%")
        print(f"Relevance ≥ 4:           {rel_pct:.1f}%")
        print()

        print("Target Metrics:")
        print(f"  ✅ Faithfulness ≥ 90%:  {'PASS ✓' if faith_pct >= 90 else 'FAIL ✗'}")
        print(f"  ✅ Relevance ≥ 85%:     {'PASS ✓' if rel_pct >= 85 else 'FAIL ✗'}")
        print()

    def save_evaluation(self, output_file: str = "data/evaluation_hybrid_results.json"):
        """Save results."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "method": "Hybrid (70% semantic + 30% BM25)",
            "model": self.rag.model,
            "total_questions": len(self.results),
            "results": self.results,
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Evaluation saved to {output_file}")


def main():
    """Run evaluation."""
    evaluator = HybridRAGEvaluator(model="gpt-3.5-turbo")
    evaluator.setup()
    evaluator.run_evaluation(verbose=True)
    evaluator.print_results_table()
    evaluator.print_metrics()
    evaluator.save_evaluation()


if __name__ == "__main__":
    main()
