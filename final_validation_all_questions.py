"""
FINAL VALIDATION: Test Light (0.2) Reranking on ALL questions
Original 100 + New 50 = 150 total questions
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
import faiss

print("=" * 100)
print("FINAL VALIDATION: HYBRID + LIGHT RERANKING (0.2)")
print("Testing on 100 Original + 50 New = 150 Total Questions")
print("=" * 100)
print()

# Load chunks and embeddings
with open('data/09_stable_chunks_aggressive_rebuild.json', 'r') as f:
    data = json.load(f)
chunks = data['chunks']

embeddings = np.load('data/10_embeddings_aggressive_rebuild.npy')

# Setup
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings.astype(np.float32))

texts = [c['text'] for c in chunks]
tokenized = [text.lower().split() for text in texts]
bm25 = BM25Okapi(tokenized)
encoder = SentenceTransformer('all-MiniLM-L6-v2')
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# Load both original and new test questions
with open('data/100_test_questions.json', 'r') as f:
    original_qs = json.load(f)

with open('data/50_additional_test_questions.json', 'r') as f:
    additional_data = json.load(f)
    additional_qs = additional_data['questions']

all_questions = original_qs + additional_qs

print(f"Loaded {len(original_qs)} original questions")
print(f"Loaded {len(additional_qs)} additional questions")
print(f"Total: {len(all_questions)} questions")
print()

# Test with Light (0.2) reranking
print("=" * 100)
print("TESTING WITH LIGHT RERANKING (0.2 weight)")
print("=" * 100)
print()

correct = 0
rule_accuracy = {}
set_breakdown = {'original': {'correct': 0, 'total': 0}, 'additional': {'correct': 0, 'total': 0}}

for i, q in enumerate(all_questions, 1):
    question = q['question']
    expected_rule = q['rule']
    is_original = q['id'] <= 100

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

        final_score = (hybrid_score * 0.8) + (rerank_norm * 0.2)  # Light: 0.2 weight
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

    if is_original:
        set_breakdown['original']['total'] += 1
        if is_correct:
            set_breakdown['original']['correct'] += 1
    else:
        set_breakdown['additional']['total'] += 1
        if is_correct:
            set_breakdown['additional']['correct'] += 1

    if expected_rule not in rule_accuracy:
        rule_accuracy[expected_rule] = {'correct': 0, 'total': 0}
    rule_accuracy[expected_rule]['total'] += 1
    if is_correct:
        rule_accuracy[expected_rule]['correct'] += 1

    if i % 50 == 0:
        accuracy = (correct / i) * 100
        print(f"  [{i:3d}/150] Accuracy: {accuracy:.1f}%")

accuracy = (correct / len(all_questions)) * 100

print()
print("=" * 100)
print("RESULTS: ALL 150 QUESTIONS")
print("=" * 100)
print()

print(f"Overall Accuracy: {correct}/150 ({accuracy:.1f}%)")
print()

# Breakdown by set
orig_acc = (set_breakdown['original']['correct'] / set_breakdown['original']['total']) * 100 if set_breakdown['original']['total'] > 0 else 0
add_acc = (set_breakdown['additional']['correct'] / set_breakdown['additional']['total']) * 100 if set_breakdown['additional']['total'] > 0 else 0

print("Performance by Question Set:")
print(f"  Original 100:     {set_breakdown['original']['correct']}/{set_breakdown['original']['total']} ({orig_acc:.1f}%)")
print(f"  Additional 50:    {set_breakdown['additional']['correct']}/{set_breakdown['additional']['total']} ({add_acc:.1f}%)")
print()

print("Rule-by-Rule Performance:")
print()
print(f"{'Rule':<8} {'Questions':<15} {'Correct':<15} {'Accuracy':<12} {'Status'}")
print("-" * 70)

for rule in sorted(rule_accuracy.keys()):
    stats = rule_accuracy[rule]
    acc = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0

    if acc == 100:
        status = "🎯 Perfect"
    elif acc >= 80:
        status = "✅ Excellent"
    elif acc >= 60:
        status = "✅ Good"
    elif acc >= 30:
        status = "⚠️ Fair"
    else:
        status = "❌ Poor"

    print(f"{rule:<8} {stats['total']:<15} {stats['correct']:<15} {acc:>6.1f}%{'':<5} {status}")

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)
print()

print("Hybrid + Light Reranking (0.2) Results:")
print(f"  Original 100 questions: {orig_acc:.1f}%")
print(f"  Additional 50 questions: {add_acc:.1f}%")
print(f"  Combined 150 questions: {accuracy:.1f}%")
print()

if accuracy >= 75:
    print(f"✅ EXCELLENT! System generalizes well at {accuracy:.1f}%")
elif accuracy >= 70:
    print(f"✅ GOOD! System at {accuracy:.1f}%")
else:
    print(f"⚠️ System at {accuracy:.1f}%")

print()

# Compare to original (no reranking)
print("=" * 100)
print("COMPARISON: WITH vs WITHOUT RERANKING")
print("=" * 100)
print()

print(f"Original 100 questions (no reranking): 76.0%")
print(f"Original 100 questions (light 0.2):   {orig_acc:.1f}%")
print(f"Difference:                            {orig_acc - 76.0:+.1f}%")
print()

print(f"Additional 50 questions (new):         {add_acc:.1f}%")
print()

print(f"All 150 questions (light 0.2):        {accuracy:.1f}%")
print()

if accuracy >= 75:
    print("✅ RECOMMENDATION: Use Light (0.2) Reranking - System generalizes well!")
else:
    print("⚠️ RECOMMENDATION: Review - Some generalization issues")

print()

