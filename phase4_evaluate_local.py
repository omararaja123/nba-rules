"""
Phase 4: Evaluation with Local LLM (No API Key Required)
Test RAG system on 10 benchmark questions using local models.
"""

import json
from typing import List, Dict
from datetime import datetime

from phase4_rag_local import LocalRAGSystem


class LocalRAGEvaluator:
    """Evaluate RAG system using local LLM."""

    def __init__(self, model: str = "mistral", base_url: str = "http://localhost:11434"):
        """
        Initialize evaluator.

        Args:
            model: Local model name
            base_url: Local LLM server URL
        """
        self.rag = LocalRAGSystem(model=model, base_url=base_url)
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
                "question": "When is defensive goaltending called?",
                "expected_rule": "Rule 11",
            },
            {
                "id": 3,
                "question": "Which situations are reviewable using instant replay?",
                "expected_rule": "Rule 13",
            },
            {
                "id": 4,
                "question": "What behaviors can result in a technical foul?",
                "expected_rule": "Rule 12",
            },
            {
                "id": 5,
                "question": "How many timeouts does a team receive per game?",
                "expected_rule": "Rule 5",
            },
            {
                "id": 6,
                "question": "When does the shot clock reset to 14 seconds?",
                "expected_rule": "Rule 7",
            },
            {
                "id": 7,
                "question": "In what situations is a jump ball used?",
                "expected_rule": "Rule 6",
            },
            {
                "id": 8,
                "question": "What is the difference between Flagrant Foul 1 and 2?",
                "expected_rule": "Rule 12",
            },
            {
                "id": 9,
                "question": "When is a player considered out of bounds?",
                "expected_rule": "Rule 10",
            },
            {
                "id": 10,
                "question": "How many free throws for different personal fouls?",
                "expected_rule": "Rule 8",
            },
        ]

    def setup(self):
        """Setup RAG system."""
        print()
        return self.rag.setup()

    def run_evaluation(self, verbose: bool = True) -> Dict:
        """
        Run evaluation on all 10 questions.

        Args:
            verbose: Print progress

        Returns:
            Evaluation results
        """
        print("=" * 80)
        print("PHASE 4: LOCAL RAG EVALUATION (No API Key)")
        print("=" * 80)
        print()

        print(f"Testing {len(self.benchmark_questions)} questions...")
        print(f"Model: {self.rag.model}")
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
                **evaluation,
            }

            results.append(result)

            if verbose:
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
        print("EVALUATION RESULTS")
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
        print(f"  ✅ Faithfulness ≥ 90%:  {'PASS' if faith_pct >= 90 else 'FAIL'}")
        print(f"  ✅ Relevance ≥ 85%:     {'PASS' if rel_pct >= 85 else 'FAIL'}")
        print()

    def print_sample_results(self, num_samples: int = 2):
        """Print sample results."""
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
            if result['citations']:
                for citation in result['citations']:
                    print(f"  • {citation['citation']}")
            else:
                print("  (None)")
            print()
            print(f"Faithfulness: {result['faithfulness']}/5 | "
                  f"Relevance: {result['relevance']}/5")
            print()

    def save_evaluation(self, output_file: str = "data/evaluation_local_results.json"):
        """Save results."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "model": self.rag.model,
            "total_questions": len(self.results),
            "results": self.results,
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Evaluation saved to {output_file}")


def main():
    """Run evaluation."""
    evaluator = LocalRAGEvaluator(
        model="mistral",
        base_url="http://localhost:11434"
    )

    if not evaluator.setup():
        print()
        print("Could not connect to local LLM server.")
        print("Please start your server and try again.")
        return

    results = evaluator.run_evaluation(verbose=True)
    evaluator.print_results_table()
    evaluator.print_metrics()
    evaluator.print_sample_results(num_samples=2)
    evaluator.save_evaluation()


if __name__ == "__main__":
    main()
