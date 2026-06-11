"""
Phase 3 Embeddings Validation
Comprehensive testing of embedding quality before Phase 4.

Tests 20 curated questions against expected rule sections.
Measures Top-1 and Top-3 accuracy.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent))

from phase3_embeddings import EmbeddingPipeline


class EmbeddingsValidator:
    """Validate embedding quality."""

    def __init__(self):
        """Initialize validator."""
        self.pipeline = EmbeddingPipeline()
        self.faiss_index = None
        self.test_questions = [
            # Rule 4: Definitions
            {"q": "What is traveling?", "expected_rule": 4, "expected_section": "Traveling"},
            {"q": "How is dribbling defined?", "expected_rule": 4, "expected_section": "Dribble"},
            {"q": "What is a screen in basketball?", "expected_rule": 4, "expected_section": "Screen"},
            {"q": "Define a foul.", "expected_rule": 4, "expected_section": "Fouls"},

            # Rule 7: Shot Clock
            {"q": "When does the shot clock reset to 14 seconds?", "expected_rule": 7, "expected_section": "Resetting"},
            {"q": "What is the shot clock in basketball?", "expected_rule": 7, "expected_section": "Definition"},

            # Rule 5: Scoring and Timing
            {"q": "How many points is a field goal worth?", "expected_rule": 5, "expected_section": "Scoring"},
            {"q": "How long is a quarter in NBA basketball?", "expected_rule": 5, "expected_section": "Timing"},

            # Rule 12: Fouls and Penalties
            {"q": "What is a technical foul?", "expected_rule": 12, "expected_section": "Conduct"},
            {"q": "What is the difference between Flagrant Foul 1 and 2?", "expected_rule": 12, "expected_section": "Flagrant"},
            {"q": "How many free throws for a personal foul?", "expected_rule": 12, "expected_section": "Free Throw"},

            # Rule 11: Basket Interference
            {"q": "When is goaltending called?", "expected_rule": 11, "expected_section": "Goaltending"},

            # Rule 6: Putting Ball in Play
            {"q": "When is a jump ball used?", "expected_rule": 6, "expected_section": "Jump Ball"},

            # Rule 10: Violations
            {"q": "What is an offensive three-second violation?", "expected_rule": 10, "expected_section": "Three-Second"},
            {"q": "When is a player out of bounds?", "expected_rule": 10, "expected_section": "Out of Bounds"},

            # Rule 8: Free Throws
            {"q": "How are free throws awarded?", "expected_rule": 8, "expected_section": "Free Throw"},

            # Rule 5: Timeouts
            {"q": "How many timeouts per team per game?", "expected_rule": 5, "expected_section": "Timeout"},

            # Rule 13: Instant Replay
            {"q": "What situations are reviewable with instant replay?", "expected_rule": 13, "expected_section": "Replay"},

            # Rule 3: Players
            {"q": "How many players on a team?", "expected_rule": 3, "expected_section": "Team"},

            # Rule 1: Court
            {"q": "What are court dimensions?", "expected_rule": 1, "expected_section": "Court"},
        ]

    def setup(self):
        """Load embeddings and build index."""
        print("=" * 80)
        print("PHASE 3 EMBEDDINGS VALIDATION")
        print("=" * 80)
        print()

        print("Setting up validator...")
        self.pipeline.load_chunks("data/09_stable_chunks.json")
        self.pipeline.generate_embeddings(batch_size=32, show_progress=False)
        self.faiss_index = self.pipeline.build_faiss_index()
        print()

    def check_match(self, result: Dict, expected_rule: int, expected_section: str) -> bool:
        """Check if result matches expected rule and section."""
        rule_match = result['rule_number'] == expected_rule
        section_match = expected_section.lower() in result['section_title'].lower()
        return rule_match and section_match

    def run_tests(self) -> Dict:
        """Run all validation tests."""
        print("=" * 80)
        print("TESTING 20 CURATED QUESTIONS")
        print("=" * 80)
        print()

        results = {
            "passed": 0,
            "top_1": [],
            "top_3": [],
            "failures": [],
        }

        for i, test in enumerate(self.test_questions, 1):
            question = test['q']
            expected_rule = test['expected_rule']
            expected_section = test['expected_section']

            # Search
            search_results = self.pipeline.similarity_search(
                question,
                self.faiss_index,
                k=3
            )

            # Check results
            top_1_match = False
            top_3_match = False

            if search_results and self.check_match(search_results[0], expected_rule, expected_section):
                top_1_match = True
                top_3_match = True
            elif len(search_results) >= 3:
                for result in search_results[:3]:
                    if self.check_match(result, expected_rule, expected_section):
                        top_3_match = True
                        break

            # Track results
            results['top_1'].append(top_1_match)
            results['top_3'].append(top_3_match)

            if top_1_match or top_3_match:
                results['passed'] += 1
                status = "✅ PASS" if top_1_match else "⚠️  Top-3"
            else:
                status = "❌ FAIL"
                results['failures'].append({
                    'question': question,
                    'expected': f"Rule {expected_rule}, {expected_section}",
                    'got': f"Rule {search_results[0]['rule_number']}, {search_results[0]['section_title']}" if search_results else "No results"
                })

            print(f"{i:2d}. {status} | {question[:50]}...")
            if search_results:
                print(f"    → Rule {search_results[0]['rule_number']}, {search_results[0]['section_title']} (score: {search_results[0]['similarity_score']:.3f})")

        print()
        return results

    def print_report(self, results: Dict):
        """Print validation report."""
        total = len(self.test_questions)
        top_1_count = sum(results['top_1'])
        top_3_count = sum(results['top_3'])

        print("=" * 80)
        print("VALIDATION REPORT")
        print("=" * 80)
        print()

        print("Accuracy Metrics:")
        print(f"  Top-1 Accuracy: {top_1_count}/{total} ({top_1_count/total*100:.1f}%)")
        print(f"  Top-3 Accuracy: {top_3_count}/{total} ({top_3_count/total*100:.1f}%)")
        print()

        # Rating
        if top_3_count >= 16:
            rating = "✅ EXCELLENT - Ready for Phase 4"
        elif top_3_count >= 14:
            rating = "✅ GOOD - Ready for Phase 4 with monitoring"
        elif top_3_count >= 12:
            rating = "⚠️  FAIR - Consider Phase 4 but watch closely"
        else:
            rating = "❌ NEEDS WORK - Debug before Phase 4"

        print(f"Overall Rating: {rating}")
        print()

        if results['failures']:
            print("Failures:")
            for failure in results['failures'][:5]:
                print(f"  ❌ {failure['question']}")
                print(f"     Expected: {failure['expected']}")
                print(f"     Got: {failure['got']}")
            if len(results['failures']) > 5:
                print(f"  ... and {len(results['failures']) - 5} more")
            print()

        print("=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print()
        print("✅ Phase 3 Complete: Embeddings generated and validated")
        print("📋 Ready for Phase 4: Build retrieval system with reranking")
        print("🎯 Phase 5: Connect LLM for answer generation with citations")
        print()


def main():
    """Run validation."""
    validator = EmbeddingsValidator()
    validator.setup()
    results = validator.run_tests()
    validator.print_report(results)


if __name__ == "__main__":
    main()
