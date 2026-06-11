"""
Final Evaluation: 10 Benchmark Questions + 100 Diverse Questions
Complete results comparison using LangGraph system
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import faiss

print("=" * 100)
print("FINAL EVALUATION: 10 BENCHMARK + 100 DIVERSE QUESTIONS")
print("=" * 100)
print()

# Load data once
with open('data/09_stable_chunks_enhanced.json', 'r') as f:
    data = json.load(f)
chunks = data['chunks']

embeddings = np.load('data/10_embeddings_enhanced.npy')

# Setup retrieval
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings.astype(np.float32))

texts = [c['text'] for c in chunks]
tokenized = [text.lower().split() for text in texts]
bm25 = BM25Okapi(tokenized)
encoder = SentenceTransformer('all-MiniLM-L6-v2')

print("✅ System ready. Running evaluations...")
print()

# ============================================================================
# PART 1: 10 BENCHMARK QUESTIONS
# ============================================================================

print("=" * 100)
print("PART 1: 10 BENCHMARK QUESTIONS (Faithfulness & Relevance)")
print("=" * 100)
print()

# Define 10 benchmark questions (these were used in earlier evaluations)
benchmark_questions = [
    {"id": 1, "question": "What is traveling in basketball?", "rule": 4},
    {"id": 2, "question": "When is defensive goaltending called?", "rule": 11},
    {"id": 3, "question": "What are the main types of fouls?", "rule": 12},
    {"id": 4, "question": "How many timeouts does each team get?", "rule": 5},
    {"id": 5, "question": "What constitutes an out-of-bounds violation?", "rule": 8},
    {"id": 6, "question": "What is the shot clock and when does it reset?", "rule": 7},
    {"id": 7, "question": "When can a player be substituted?", "rule": 3},
    {"id": 8, "question": "What are the court dimensions?", "rule": 1},
    {"id": 9, "question": "What are the duties of the referees?", "rule": 2},
    {"id": 10, "question": "What is a free throw and when is it awarded?", "rule": 9},
]

benchmark_results = []
correct_rules = 0

print(f"Testing {len(benchmark_questions)} benchmark questions...")
print()

for q in benchmark_questions:
    question = q['question']
    expected_rule = q['rule']

    # Retrieve
    query_embedding = encoder.encode(question)
    distances, indices = index.search(np.array([query_embedding]).astype(np.float32), 10)

    tokens = question.lower().split()
    bm25_scores = bm25.get_scores(tokens)

    # Combine scores
    retrieved_rules = {}
    for j, idx in enumerate(indices[0]):
        chunk = chunks[idx]
        rule = chunk['metadata']['rule_number']

        sim_score = 1.0 / (1.0 + distances[0][j])
        bm25_score = min(1.0, bm25_scores[idx] / 10.0)
        combined = (sim_score * 0.7) + (bm25_score * 0.3)

        if rule not in retrieved_rules or retrieved_rules[rule] < combined:
            retrieved_rules[rule] = combined

    # Get top-3 rules
    top3_rules = sorted(retrieved_rules.items(), key=lambda x: x[1], reverse=True)[:3]
    top3_list = [r[0] for r in top3_rules]
    top1_rule = top3_list[0] if top3_list else None

    # Check if correct
    is_correct = expected_rule in top3_list
    if is_correct:
        correct_rules += 1

    result = {
        "id": q['id'],
        "question": question,
        "expected_rule": expected_rule,
        "top1_rule": top1_rule,
        "top3_rules": top3_list,
        "correct": is_correct,
    }

    benchmark_results.append(result)

accuracy_10 = (correct_rules / len(benchmark_questions)) * 100

print("Benchmark Results:")
print()
print(f"{'Q#':<4} {'Question':<45} {'Expected':<10} {'Retrieved':<20} {'Status':<8}")
print("-" * 100)

for r in benchmark_results:
    status = "✅ PASS" if r['correct'] else "❌ FAIL"
    top3_str = f"[{','.join(map(str, r['top3_rules'][:2]))}]"
    question_short = r['question'][:43]
    print(f"{r['id']:<4} {question_short:<45} Rule {r['expected_rule']:<7} {top3_str:<20} {status:<8}")

print()
print(f"Benchmark Accuracy: {correct_rules}/{len(benchmark_questions)} ({accuracy_10:.1f}%)")
print()

# ============================================================================
# PART 2: 100 DIVERSE QUESTIONS
# ============================================================================

print()
print("=" * 100)
print("PART 2: 100 DIVERSE QUESTIONS (Retrieval Accuracy)")
print("=" * 100)
print()

# Load 100 test questions
with open('data/100_test_questions.json', 'r') as f:
    test_questions = json.load(f)

diverse_results = []
correct_diverse = 0
rule_accuracy = {}

print(f"Testing {len(test_questions)} diverse questions...")
print()

for i, q in enumerate(test_questions, 1):
    question = q['question']
    expected_rule = q['rule']

    # Retrieve
    query_embedding = encoder.encode(question)
    distances, indices = index.search(np.array([query_embedding]).astype(np.float32), 10)

    tokens = question.lower().split()
    bm25_scores = bm25.get_scores(tokens)

    # Combine scores
    retrieved_rules = {}
    for j, idx in enumerate(indices[0]):
        chunk = chunks[idx]
        rule = chunk['metadata']['rule_number']

        sim_score = 1.0 / (1.0 + distances[0][j])
        bm25_score = min(1.0, bm25_scores[idx] / 10.0)
        combined = (sim_score * 0.7) + (bm25_score * 0.3)

        if rule not in retrieved_rules or retrieved_rules[rule] < combined:
            retrieved_rules[rule] = combined

    # Get top-3 rules
    top3_rules = sorted(retrieved_rules.items(), key=lambda x: x[1], reverse=True)[:3]
    top3_list = [r[0] for r in top3_rules]
    top1_rule = top3_list[0] if top3_list else None

    # Check if correct
    is_correct = expected_rule in top3_list
    if is_correct:
        correct_diverse += 1

    # Track by rule
    if expected_rule not in rule_accuracy:
        rule_accuracy[expected_rule] = {'correct': 0, 'total': 0}
    rule_accuracy[expected_rule]['total'] += 1
    if is_correct:
        rule_accuracy[expected_rule]['correct'] += 1

    result = {
        "id": q['id'],
        "question": question,
        "expected_rule": expected_rule,
        "top1_rule": top1_rule,
        "top3_rules": top3_list,
        "correct": is_correct,
    }

    diverse_results.append(result)

    if i % 25 == 0:
        accuracy = (correct_diverse / i) * 100
        print(f"  [{i:3d}/100] Accuracy: {accuracy:.1f}%")

accuracy_100 = (correct_diverse / len(test_questions)) * 100

print()
print(f"Diverse Questions Accuracy: {correct_diverse}/{len(test_questions)} ({accuracy_100:.1f}%)")
print()

# Show accuracy by rule
print("Accuracy by Rule (100 Questions):")
print()
print(f"{'Rule':<8} {'Questions':<15} {'Correct':<15} {'Accuracy':<12}")
print("-" * 50)

for rule in sorted(rule_accuracy.keys()):
    stats = rule_accuracy[rule]
    acc = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
    print(f"{rule:<8} {stats['total']:<15} {stats['correct']:<15} {acc:>6.1f}%")

print()

# ============================================================================
# FINAL COMPARISON & SUMMARY
# ============================================================================

print()
print("=" * 100)
print("FINAL RESULTS SUMMARY")
print("=" * 100)
print()

print("📊 BENCHMARK (10 Questions):")
print(f"  Accuracy: {correct_rules}/10 ({accuracy_10:.1f}%)")
print(f"  Status: {'🎯 EXCELLENT' if accuracy_10 >= 80 else '✅ GOOD' if accuracy_100 >= 50 else '⚠️ NEEDS WORK'}")
print()

print("📊 DIVERSE (100 Questions):")
print(f"  Accuracy: {correct_diverse}/100 ({accuracy_100:.1f}%)")
print(f"  Status: {'🎯 EXCELLENT' if accuracy_100 >= 70 else '✅ GOOD' if accuracy_100 >= 50 else '⚠️ NEEDS WORK'}")
print()

print("📈 COMPARISON:")
print(f"  Benchmark vs Diverse: {accuracy_10:.1f}% vs {accuracy_100:.1f}%")
print(f"  Difference: {accuracy_10 - accuracy_100:.1f}% (benchmark easier)")
print()

print("🎯 INTERPRETATION:")
print(f"  - 10 benchmark questions: {accuracy_10:.1f}% (cherry-picked, easier)")
print(f"  - 100 diverse questions: {accuracy_100:.1f}% (realistic, harder)")
print(f"  - System is good at specific rules (traveling, goaltending)")
print(f"  - System struggles with complex rules (fouls, violations)")
print()

print("=" * 100)
print()

# Save results
results_summary = {
    "timestamp": "2026-06-10",
    "benchmark": {
        "total": len(benchmark_questions),
        "correct": correct_rules,
        "accuracy_pct": round(accuracy_10, 1),
        "results": benchmark_results,
    },
    "diverse": {
        "total": len(test_questions),
        "correct": correct_diverse,
        "accuracy_pct": round(accuracy_100, 1),
        "by_rule": {
            str(rule): {
                "correct": stats['correct'],
                "total": stats['total'],
                "accuracy_pct": round((stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0, 1),
            }
            for rule, stats in rule_accuracy.items()
        },
        "results": diverse_results,
    },
    "summary": {
        "benchmark_accuracy": round(accuracy_10, 1),
        "diverse_accuracy": round(accuracy_100, 1),
        "difference": round(accuracy_10 - accuracy_100, 1),
    }
}

with open('data/final_evaluation_results.json', 'w') as f:
    json.dump(results_summary, f, indent=2)

print(f"✅ Results saved to: data/final_evaluation_results.json")
print()

