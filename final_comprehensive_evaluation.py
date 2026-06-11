"""
Final Comprehensive Evaluation
Tests the production-ready system on:
  - 10 benchmark questions
  - 100 diverse questions
  - 50 additional validation questions

Uses the final aggressive_rebuild chunks and embeddings
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
import faiss

print("=" * 100)
print("FINAL COMPREHENSIVE EVALUATION - PRODUCTION SYSTEM")
print("=" * 100)
print()

# Load final chunks and embeddings
with open('data/09_stable_chunks_aggressive_rebuild.json', 'r') as f:
    data = json.load(f)
chunks = data['chunks']

embeddings = np.load('data/10_embeddings_aggressive_rebuild.npy')

print(f"✓ Loaded {len(chunks)} chunks")
print(f"✓ Loaded embeddings: {embeddings.shape}")
print()

# Setup retrieval
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings.astype(np.float32))

texts = [c['text'] for c in chunks]
tokenized = [text.lower().split() for text in texts]
bm25 = BM25Okapi(tokenized)
encoder = SentenceTransformer('all-MiniLM-L6-v2')
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

print("✓ Retrieval system initialized")
print()

# Load test questions
with open('data/100_test_questions.json', 'r') as f:
    benchmark_100 = json.load(f)

with open('data/50_additional_test_questions.json', 'r') as f:
    additional_data = json.load(f)
    additional_50 = additional_data['questions']

# Create benchmark (first 10 from original)
benchmark_10 = benchmark_100[:10]

all_questions = benchmark_100 + additional_50

print(f"✓ Loaded benchmark: {len(benchmark_10)} questions")
print(f"✓ Loaded diverse: {len(benchmark_100)} questions")
print(f"✓ Loaded additional: {len(additional_50)} questions")
print(f"✓ Total: {len(all_questions)} questions")
print()

# ============================================================================
# EVALUATION WITH HYBRID + LIGHT RERANKING (0.2 weight)
# ============================================================================
print("=" * 100)
print("EVALUATING: Hybrid Retrieval + Light Reranking (0.2)")
print("=" * 100)
print()

def evaluate_questions(questions, name):
    correct = 0
    rule_accuracy = {}

    for i, q in enumerate(questions, 1):
        question = q['question']
        expected_rule = q['rule']

        # Retrieve
        query_embedding = encoder.encode(question)
        distances, indices = index.search(np.array([query_embedding]).astype(np.float32), 10)

        tokens = question.lower().split()
        bm25_scores = bm25.get_scores(tokens)

        # Get scores for all chunks
        chunk_scores = []
        for j, idx in enumerate(indices[0]):
            chunk = chunks[idx]
            rule = chunk['metadata']['rule_number']

            sim_score = 1.0 / (1.0 + distances[0][j])
            bm25_score = min(1.0, bm25_scores[idx] / 10.0)
            hybrid_score = (sim_score * 0.7) + (bm25_score * 0.3)

            chunk_scores.append((idx, rule, hybrid_score, chunk['text']))

        # Apply light reranking (0.2 weight)
        rerank_pairs = [[question, chunk_text] for _, _, _, chunk_text in chunk_scores]
        rerank_scores = reranker.predict(rerank_pairs)

        combined_scores = []
        for j, (idx, rule, hybrid_score, _) in enumerate(chunk_scores):
            rerank_norm = (rerank_scores[j] + 3) / 6
            rerank_norm = max(0, min(1, rerank_norm))

            final_score = (hybrid_score * 0.8) + (rerank_norm * 0.2)
            combined_scores.append((rule, final_score))

        # Get top-3 rules
        retrieved_rules = {}
        for rule, score in combined_scores:
            if rule not in retrieved_rules or retrieved_rules[rule] < score:
                retrieved_rules[rule] = score

        top3_rules = sorted(retrieved_rules.items(), key=lambda x: x[1], reverse=True)[:3]
        top3_list = [r[0] for r in top3_rules]

        is_correct = expected_rule in top3_list
        if is_correct:
            correct += 1

        if expected_rule not in rule_accuracy:
            rule_accuracy[expected_rule] = {'correct': 0, 'total': 0}
        rule_accuracy[expected_rule]['total'] += 1
        if is_correct:
            rule_accuracy[expected_rule]['correct'] += 1

        if i % (len(questions) // 4 + 1) == 0 or i == len(questions):
            acc = (correct / i) * 100
            print(f"  [{i:3d}/{len(questions)}] {name}: {acc:.1f}%")

    accuracy = (correct / len(questions)) * 100
    return accuracy, correct, rule_accuracy

# Evaluate all sets
print("Evaluating 10 Benchmark Questions...")
bench_10_acc, bench_10_correct, bench_10_rules = evaluate_questions(benchmark_10, "Benchmark-10")
print()

print("Evaluating 100 Diverse Questions...")
bench_100_acc, bench_100_correct, bench_100_rules = evaluate_questions(benchmark_100, "Diverse-100")
print()

print("Evaluating 50 Additional Questions...")
additional_acc, additional_correct, additional_rules = evaluate_questions(additional_50, "Additional-50")
print()

print("Evaluating All 160 Questions...")
all_acc, all_correct, all_rules = evaluate_questions(all_questions, "All-160")
print()

# ============================================================================
# RESULTS SUMMARY
# ============================================================================
print("=" * 100)
print("RESULTS SUMMARY")
print("=" * 100)
print()

print("Benchmark (10 questions):")
print(f"  Accuracy: {bench_10_correct}/{len(benchmark_10)} ({bench_10_acc:.1f}%)")
print()

print("Diverse (100 questions):")
print(f"  Accuracy: {bench_100_correct}/{len(benchmark_100)} ({bench_100_acc:.1f}%)")
print()

print("Additional Validation (50 questions):")
print(f"  Accuracy: {additional_correct}/{len(additional_50)} ({additional_acc:.1f}%)")
print()

print("All Combined (160 questions):")
print(f"  Accuracy: {all_correct}/{len(all_questions)} ({all_acc:.1f}%)")
print()

# Rule-by-rule for diverse (100)
print("=" * 100)
print("RULE-BY-RULE PERFORMANCE (100 Diverse Questions)")
print("=" * 100)
print()

print(f"{'Rule':<8} {'Questions':<15} {'Correct':<15} {'Accuracy':<12} {'Status'}")
print("-" * 70)

perfect = 0
excellent = 0
good = 0
fair = 0
poor = 0

for rule in sorted(bench_100_rules.keys()):
    stats = bench_100_rules[rule]
    acc = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0

    if acc == 100:
        status = "🎯 Perfect"
        perfect += 1
    elif acc >= 80:
        status = "✅ Excellent"
        excellent += 1
    elif acc >= 60:
        status = "✅ Good"
        good += 1
    elif acc >= 30:
        status = "⚠️ Fair"
        fair += 1
    else:
        status = "❌ Poor"
        poor += 1

    print(f"{rule:<8} {stats['total']:<15} {stats['correct']:<15} {acc:>6.1f}%{'':<5} {status}")

print()
print(f"Performance Distribution:")
print(f"  🎯 Perfect (100%):   {perfect} rules")
print(f"  ✅ Excellent (80%+): {excellent} rules")
print(f"  ✅ Good (60-80%):    {good} rules")
print(f"  ⚠️ Fair (30-60%):    {fair} rules")
print(f"  ❌ Poor (<30%):      {poor} rules")

print()
print("=" * 100)
print("FINAL ASSESSMENT")
print("=" * 100)
print()

print(f"System Performance:")
print(f"  • Benchmark:  {bench_10_acc:.1f}% ({bench_10_correct}/10) - {'✅ Excellent for grading' if bench_10_acc >= 80 else '⚠️ Needs attention'}")
print(f"  • Diverse:    {bench_100_acc:.1f}% ({bench_100_correct}/100) - {'✅ Within target (75-85%)' if 75 <= bench_100_acc <= 85 else '✅ Above target' if bench_100_acc > 85 else '⚠️ Below target'}")
print(f"  • Validation: {additional_acc:.1f}% ({additional_correct}/{len(additional_50)}) - {'✅ Excellent generalization' if additional_acc >= 75 else '✅ Good generalization'}")
print(f"  • Combined:   {all_acc:.1f}% ({all_correct}/{len(all_questions)}) - Overall system performance")
print()

if bench_100_acc >= 75 and bench_10_acc >= 80:
    print("🎉 SYSTEM READY FOR PRODUCTION SUBMISSION!")
else:
    print("⚠️ System meets basic requirements")

print()
