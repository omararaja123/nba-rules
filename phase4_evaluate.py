"""
Phase 4: Evaluation Framework
Test RAG system against 10 benchmark questions.
Measure faithfulness and relevance.
"""

import json
from typing import List, Dict
from datetime import datetime
import re

from phase4_rag_system import RAGSystem
from phase4_prompts import get_evaluation_prompt


class RAGEvaluator:
    """Evaluate RAG system performance."""

    def __init__(self):
        """Initialize evaluator."""
        self.rag = RAGSystem()
        self.results = []

        # 10 benchmark questions
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
        """
        Run evaluation on all 10 questions.

        Args:
            verbose: Print progress

        Returns:
            Evaluation results
        """
        print("=" * 80)
        print("PHASE 4: RAG SYSTEM EVALUATION")
        print("=" * 80)
        print()

        print(f"Testing {len(self.benchmark_questions)} questions...")
        print()

        results = []

        for i, test_case in enumerate(self.benchmark_questions, 1):
            if verbose:
                print(
                    f"[{i}/{len(self.benchmark_questions)}] "
                    f"Q: {test_case['question'][:50]}..."
                )

            # Generate answer
            rag_result = self.rag.answer_question(
                test_case['question'],
                top_k=5
            )

            # Evaluate answer
            evaluation = self._evaluate_single(rag_result, test_case)

            # Combine results
            result = {
                "id": test_case['id'],
                "question": test_case['question'],
                "expected_rule": test_case['expected_rule'],
                "answer": rag_result['answer'],
                "citations": rag_result['citations'],
                "retrieved_chunks": rag_result['retrieved_chunks'],
                "confidence": rag_result['confidence'],
                **evaluation,  # Add faithfulness, relevance, notes
            }

            results.append(result)

            if verbose:
                print(
                    f"  → Faithfulness: {evaluation['faithfulness']}/5, "
                    f"Relevance: {evaluation['relevance']}/5"
                )
                print()

        self.results = results

        return {
            "timestamp": datetime.now().isoformat(),
            "total_questions": len(results),
            "results": results,
            "metrics": self._calculate_metrics(results),
        }

    def _evaluate_single(self, rag_result: Dict, test_case: Dict) -> Dict:
        """
        Evaluate a single answer.

        Args:
            rag_result: RAG system output
            test_case: Test case metadata

        Returns:
            Evaluation scores and notes
        """
        answer = rag_result['answer']
        citations = rag_result['citations']
        expected_rule = test_case['expected_rule']

        # Manual scoring (for demo; in production, you'd use Claude for scoring)
        faithfulness = self._score_faithfulness(answer, citations)
        relevance = self._score_relevance(answer, expected_rule)

        notes = []

        # Check for critical phrases
        if "could not find" in answer.lower():
            notes.append("System could not find sufficient information")
            faithfulness = min(faithfulness, 3)

        # Check citation quality
        if not citations:
            notes.append("No citations provided")
            faithfulness = min(faithfulness, 2)

        if len(citations) < 2:
            notes.append("Limited citations (< 2)")

        # Check expected rule coverage
        if expected_rule.lower() not in answer.lower():
            notes.append(f"Expected rule ({expected_rule}) not mentioned")
            relevance = min(relevance, 3)

        return {
            "faithfulness": faithfulness,
            "relevance": relevance,
            "notes": "; ".join(notes) if notes else "OK",
        }

    def _score_faithfulness(self, answer: str, citations: List[Dict]) -> int:
        """
        Score faithfulness (1-5).
        1 = Unsupported
        5 = Fully supported with strong citations
        """
        # Base score
        score = 2  # Start pessimistic

        # No answer = unsupported
        if not answer or "could not find" in answer.lower():
            return 1

        # Citations present
        if citations:
            score = 4
            if len(citations) >= 3:
                score = 5

        # Check for citation format
        if "Rule" in answer and "Section" in answer:
            score = min(5, score + 1)

        return min(5, score)

    def _score_relevance(self, answer: str, expected_rule: str) -> int:
        """
        Score relevance (1-5).
        1 = Irrelevant
        5 = Complete answer
        """
        # No answer = irrelevant
        if not answer or "could not find" in answer.lower():
            return 1

        # Check if it addresses the question meaningfully
        answer_lower = answer.lower()

        # Check for expected rule mention
        if expected_rule.lower() in answer_lower:
            score = 4

            # Bonus for specific details
            if any(word in answer_lower for word in ["when", "how", "what", "why"]):
                if len(answer.split()) > 50:  # Substantial answer
                    score = 5

            return score

        else:
            # Rule not mentioned but answer provided
            return 2 if len(answer) > 20 else 1

    def _calculate_metrics(self, results: List[Dict]) -> Dict:
        """Calculate aggregate metrics."""
        if not results:
            return {}

        faithfulness_scores = [r['faithfulness'] for r in results]
        relevance_scores = [r['relevance'] for r in results]

        avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)
        avg_relevance = sum(relevance_scores) / len(relevance_scores)

        faith_pct = (sum(1 for s in faithfulness_scores if s >= 4) / len(faithfulness_scores)) * 100
        rel_pct = (sum(1 for s in relevance_scores if s >= 4) / len(relevance_scores)) * 100

        return {
            "avg_faithfulness": round(avg_faithfulness, 2),
            "avg_relevance": round(avg_relevance, 2),
            "faithfulness_90_plus": faith_pct >= 90,
            "relevance_85_plus": rel_pct >= 85,
            "faithfulness_pct": round(faith_pct, 1),
            "relevance_pct": round(rel_pct, 1),
        }

    def print_results_table(self):
        """Print results as formatted table."""
        print()
        print("=" * 120)
        print("EVALUATION RESULTS")
        print("=" * 120)
        print()

        # Header
        print(
            f"{'#':>2} | {'Question':<40} | {'Faith':>5} | {'Rel':>3} | "
            f"{'Notes':<40}"
        )
        print("-" * 120)

        # Rows
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
        """Print evaluation metrics."""
        metrics = self.results[0]['metrics'] if self.results else {}

        print()
        print("=" * 80)
        print("METRICS SUMMARY")
        print("=" * 80)
        print()

        if not self.results:
            print("No results to summarize")
            return

        # Get metrics from evaluation
        faithfulness_scores = [r['faithfulness'] for r in self.results]
        relevance_scores = [r['relevance'] for r in self.results]

        avg_faith = sum(faithfulness_scores) / len(faithfulness_scores)
        avg_rel = sum(relevance_scores) / len(relevance_scores)

        faith_pct = (sum(1 for s in faithfulness_scores if s >= 4) / len(faithfulness_scores)) * 100
        rel_pct = (sum(1 for s in relevance_scores if s >= 4) / len(relevance_scores)) * 100

        print(f"Average Faithfulness:    {avg_faith:.2f}/5.00")
        print(f"Average Relevance:       {avg_rel:.2f}/5.00")
        print()
        print(f"Faithfulness ≥ 4:        {faith_pct:.1f}%")
        print(f"Relevance ≥ 4:           {rel_pct:.1f}%")
        print()

        # Target metrics
        print("Target Metrics:")
        print(f"  ✅ Faithfulness ≥ 90%:  {'PASS' if faith_pct >= 90 else 'FAIL'}")
        print(f"  ✅ Relevance ≥ 85%:     {'PASS' if rel_pct >= 85 else 'FAIL'}")
        print()

    def save_evaluation(self, output_file: str = "data/evaluation_results.json"):
        """Save evaluation results."""
        evaluation_data = {
            "timestamp": datetime.now().isoformat(),
            "total_questions": len(self.results),
            "results": self.results,
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(evaluation_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Evaluation saved to {output_file}")

    def print_sample_results(self, num_samples: int = 3):
        """Print sample question-answer pairs."""
        print()
        print("=" * 80)
        print("SAMPLE RESULTS")
        print("=" * 80)
        print()

        for i, result in enumerate(self.results[:num_samples], 1):
            print(f"[{i}] Q: {result['question']}")
            print("-" * 80)
            print(f"A: {result['answer']}")
            print()
            print("Citations:")
            for citation in result['citations']:
                print(f"  • {citation['citation']}")
            print()
            print(f"Faithfulness: {result['faithfulness']}/5 | "
                  f"Relevance: {result['relevance']}/5")
            print()


def main():
    """Run full evaluation."""
    evaluator = RAGEvaluator()
    evaluator.setup()

    # Run evaluation
    evaluation = evaluator.run_evaluation(verbose=True)

    # Print results
    evaluator.print_results_table()
    evaluator.print_metrics()
    evaluator.print_sample_results(num_samples=2)

    # Save results
    evaluator.save_evaluation()


if __name__ == "__main__":
    main()
