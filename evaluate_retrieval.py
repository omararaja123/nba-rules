"""
NBA Rules Retrieval Evaluation System
Benchmark retrieval quality using Top-1 and Top-3 accuracy metrics.
"""

import json
from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi
import re


class RetrievalEvaluator:
    """Evaluate retrieval system performance on benchmark questions."""

    def __init__(self, chunks_path: str):
        """Initialize evaluator with chunks."""
        with open(chunks_path) as f:
            data = json.load(f)

        self.chunks = data["chunks"]
        self.corpus = [c["text"] for c in self.chunks]

        # Tokenize corpus for BM25
        tokenized_corpus = [self._tokenize(text) for text in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

        print(f"✅ Loaded {len(self.chunks)} chunks")
        print(f"✅ Initialized BM25 retriever\n")

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        return text.lower().split()

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve top-k chunks for a query."""
        tokens = self._tokenize(query)
        scores = self.bm25.get_scores(tokens)

        # Get top-k indices
        ranked_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]

        results = []
        for idx in ranked_indices:
            results.append({
                "chunk": self.chunks[idx],
                "score": scores[idx],
                "rank": len(results) + 1,
            })

        return results

    def match_rule_section(self, expected: str, chunk: Dict) -> bool:
        """Check if chunk matches expected rule section."""
        section_title = chunk["metadata"].get("section_title", "").lower()
        rule_title = chunk["metadata"].get("rule_title", "").lower()

        # Direct match in section title
        if expected.lower() in section_title:
            return True

        # Match in rule title
        if expected.lower() in rule_title:
            return True

        # Match first meaningful word (e.g., "Traveling" in section title)
        words = expected.lower().split()
        if words and words[0] in section_title:
            return True

        return False

    def evaluate_question(self, question: Dict, top_k: int = 3) -> Dict:
        """Evaluate a single question."""
        query = question["question"]
        expected = question["expected"]

        # Retrieve
        results = self.retrieve(query, top_k=top_k)

        # Find if expected rule is in results
        top_1_match = False
        top_3_match = False
        correct_rank = None

        for result in results:
            if self.match_rule_section(expected, result["chunk"]):
                top_3_match = True
                correct_rank = result["rank"]

                if result["rank"] == 1:
                    top_1_match = True
                break

        return {
            "question": query,
            "expected": expected,
            "results": results,
            "top_1_match": top_1_match,
            "top_3_match": top_3_match,
            "correct_rank": correct_rank,
        }

    def print_question_result(
        self, eval_result: Dict, question_num: int
    ) -> None:
        """Print formatted result for a single question."""
        expected = eval_result["expected"]
        top_1 = "✅" if eval_result["top_1_match"] else "❌"
        top_3 = "✅" if eval_result["top_3_match"] else "❌"
        rank = (
            eval_result["correct_rank"]
            if eval_result["correct_rank"]
            else "Not found"
        )

        retrieved_sections = " → ".join(
            [f"{r['chunk']['metadata']['section_title']}" for r in eval_result["results"]]
        )

        print(f"{question_num}. {eval_result['question'][:60]}...")
        print(f"   Expected: {expected}")
        print(f"   Top 1: {top_1}  |  Top 3: {top_3}  |  Rank: {rank}")
        print(f"   Retrieved: {retrieved_sections}")
        print()

    def print_failure_analysis(self, eval_result: Dict) -> None:
        """Print detailed failure analysis."""
        if eval_result["top_3_match"]:
            return  # Not a failure

        print("\n" + "=" * 80)
        print("FAILURE ANALYSIS")
        print("=" * 80)
        print(f"\nQuestion: {eval_result['question']}")
        print(f"Expected: {eval_result['expected']}")
        print()

        print("Retrieved Chunks (Top 3):")
        print("-" * 80)

        for result in eval_result["results"]:
            chunk = result["chunk"]
            meta = chunk["metadata"]

            print(f"\nRank #{result['rank']} | Score: {result['score']:.2f}")
            print(
                f"Rule {meta['rule_number']}, Section {meta['section_number']} ({meta['section_title']}), p. {meta['page_number']}"
            )
            print(f"Tokens: {meta['token_count']}")
            print(f"Text preview: {chunk['text'][:200]}...")

        print("\n" + "-" * 80)
        print("Analysis:")
        print("-" * 80)

        # Analyze why retrieval failed
        analyses = []

        # Check if all chunks are from completely different rules
        retrieved_rules = set(r["chunk"]["metadata"]["rule_number"] for r in eval_result["results"])
        analyses.append(
            f"- Retrieved from Rule(s): {sorted(retrieved_rules)}"
        )

        # Check token counts
        token_counts = [r["chunk"]["metadata"]["token_count"] for r in eval_result["results"]]
        analyses.append(
            f"- Token counts: min={min(token_counts)}, max={max(token_counts)}, avg={sum(token_counts) // len(token_counts)}"
        )

        # Check BM25 scores
        scores = [r["score"] for r in eval_result["results"]]
        analyses.append(
            f"- BM25 scores: {[f'{s:.2f}' for s in scores]}"
        )

        # Keyword analysis
        query_words = set(eval_result["question"].lower().split())
        expected_words = set(eval_result["expected"].lower().split())
        analyses.append(
            f"- Expected keyword(s): {expected_words}"
        )
        analyses.append(
            f"- Query contains expected keywords: {expected_words & query_words}"
        )

        for analysis in analyses:
            print(analysis)

        print("\nSuggested fixes:")
        print("  - Improve query expansion (synonyms, related terms)")
        print("  - Enhance metadata with searchable keywords")
        print("  - Consider semantic search (Phase 3 embedding)")
        print("  - Review chunk boundaries for this rule section")

        print("\n" + "=" * 80)

    def run_evaluation(self, questions: List[Dict]) -> Dict:
        """Run full evaluation on all questions."""
        print("=" * 80)
        print("RETRIEVAL SYSTEM EVALUATION")
        print("=" * 80)
        print()

        results = []

        for i, question in enumerate(questions, 1):
            result = self.evaluate_question(question)
            results.append(result)

            self.print_question_result(result, i)

        # Print failure analyses
        for i, result in enumerate(results, 1):
            if not result["top_3_match"]:
                self.print_failure_analysis(result)

        # Calculate metrics
        top_1_count = sum(1 for r in results if r["top_1_match"])
        top_3_count = sum(1 for r in results if r["top_3_match"])
        total = len(results)

        print("\n" + "=" * 80)
        print("EVALUATION SUMMARY")
        print("=" * 80)
        print()

        # Results table
        print("Per-Question Results:")
        print()
        print(
            "# | Question | Expected | Top 1 | Top 3 | Rank | Notes"
        )
        print("-" * 100)

        for i, result in enumerate(results, 1):
            question_short = result["question"][:30]
            expected = result["expected"]
            top_1 = "✅" if result["top_1_match"] else "❌"
            top_3 = "✅" if result["top_3_match"] else "❌"
            rank = (
                str(result["correct_rank"])
                if result["correct_rank"]
                else "N/A"
            )
            notes = (
                "✓ Correct"
                if result["top_3_match"]
                else "⚠️  Not in Top 3"
            )

            print(
                f"{i:2d} | {question_short:30s} | {expected:15s} | {top_1} | {top_3} | {rank:3s} | {notes}"
            )

        print()
        print("Metrics:")
        print(f"  Correct in Top 1:     {top_1_count}/{total}")
        print(f"  Correct in Top 3:     {top_3_count}/{total}")
        print(f"  Top-1 Accuracy:       {top_1_count/total*100:.1f}%")
        print(f"  Top-3 Accuracy:       {top_3_count/total*100:.1f}%")
        print()

        # Rating
        if top_3_count >= 9 and top_1_count >= 7:
            rating = "Excellent"
        elif top_3_count >= 8:
            rating = "Good"
        else:
            rating = "Needs Rework"

        print(f"Overall Rating: {rating}")
        print()

        # Strengths and weaknesses
        print("Strengths:")
        if top_1_count >= 6:
            print(f"  ✅ Strong Top-1 performance ({top_1_count}/10)")
        if top_3_count >= 9:
            print(f"  ✅ Excellent Top-3 coverage ({top_3_count}/10)")
        if top_3_count >= 8:
            print(f"  ✅ Good overall retrieval quality")

        print()
        print("Weaknesses:")
        if top_3_count < 8:
            print(
                f"  ❌ Low Top-3 accuracy ({top_3_count}/10 - need {8-top_3_count} more)"
            )
        if top_1_count < 6:
            print(
                f"  ❌ Moderate Top-1 accuracy ({top_1_count}/10)"
            )

        print()
        print("=" * 80)

        return {
            "results": results,
            "top_1_accuracy": top_1_count / total,
            "top_3_accuracy": top_3_count / total,
            "rating": rating,
        }


def main():
    """Run evaluation."""
    # Test questions
    questions = [
        {
            "question": "What actions constitute a traveling violation under NBA rules?",
            "expected": "Traveling",
        },
        {
            "question": "When is defensive goaltending called and what happens after the violation?",
            "expected": "Goaltending",
        },
        {
            "question": "Which situations are reviewable using instant replay?",
            "expected": "Instant Replay",
        },
        {
            "question": "What behaviors can result in a technical foul being assessed?",
            "expected": "Technical",
        },
        {
            "question": "How many timeouts does a team receive during a regulation NBA game?",
            "expected": "Timeout",
        },
        {
            "question": "When does the shot clock reset to 14 seconds instead of 24 seconds?",
            "expected": "Shot Clock",
        },
        {
            "question": "In what situations is a jump ball used to resume play?",
            "expected": "Jump Ball",
        },
        {
            "question": "What is the difference between a Flagrant Foul Penalty 1 and Penalty 2?",
            "expected": "Flagrant",
        },
        {
            "question": "When is a player considered out of bounds?",
            "expected": "Out of Bounds",
        },
        {
            "question": "How many free throws are awarded for different types of personal fouls?",
            "expected": "Free Throw",
        },
    ]

    # Run evaluation
    evaluator = RetrievalEvaluator("data/04_chunked_text.json")
    results = evaluator.run_evaluation(questions)

    # Print final recommendations
    print("\nRECOMMENDATIONS FOR IMPROVEMENT")
    print("=" * 80)
    print()
    print("Top 3 Changes to Improve Top-3 Retrieval Accuracy:")
    print()
    print("1. IMPLEMENT SEMANTIC SEARCH (Phase 3: Embedding)")
    print("   - BM25 keyword matching has limitations")
    print("   - Semantic embeddings understand meaning, not just keywords")
    print("   - Expected improvement: +2-3 accuracy points")
    print()
    print("2. ENHANCE QUERY EXPANSION")
    print("   - Add synonyms and related terms to queries")
    print("   - Map 'goaltending' → 'basket interference'")
    print("   - Map 'traveling' → 'movement with ball'")
    print("   - Expected improvement: +1-2 accuracy points")
    print()
    print("3. ADD SEARCHABLE METADATA")
    print("   - Extend metadata with keywords and synonyms")
    print("   - Include related rule numbers in searchable fields")
    print("   - Expected improvement: +1 accuracy point")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
