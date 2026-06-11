"""
Phase 1: Top-3 Rule Retrieval
Instead of returning top-1 rule, return top-3 rules to LLM.
Expected improvement: +5-10% (36% → 41-46%)
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import faiss

print("=" * 80)
print("PHASE 1: TOP-3 RULE RETRIEVAL")
print("=" * 80)
print()

# Load data
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

# Load test questions
with open('data/100_test_questions.json', 'r') as f:
    questions = json.load(f)

print(f"Testing {len(questions)} questions with TOP-3 retrieval...")
print()

correct_top1 = 0
correct_top3 = 0
rule_accuracy = {}

for i, q in enumerate(questions, 1):
    question = q['question']
    expected_rule = q['rule']

    # Retrieve chunks
    query_embedding = encoder.encode(question)
    distances, indices = index.search(np.array([query_embedding]).astype(np.float32), 10)

    tokens = question.lower().split()
    bm25_scores = bm25.get_scores(tokens)

    # Combine scores to get top rules
    retrieved_rules = {}
    for j, idx in enumerate(indices[0]):
        chunk = chunks[idx]
        rule = chunk['metadata']['rule_number']

        sim_score = 1.0 / (1.0 + distances[0][j])
        bm25_score = min(1.0, bm25_scores[idx] / 10.0)
        combined = (sim_score * 0.7) + (bm25_score * 0.3)

        if rule not in retrieved_rules or retrieved_rules[rule] < combined:
            retrieved_rules[rule] = combined

    # Get top-3 rules (sorted by score)
    top3_rules = sorted(retrieved_rules.items(), key=lambda x: x[1], reverse=True)[:3]
    top3_rule_nums = [r[0] for r in top3_rules]

    # Get top-1 rule
    top1_rule = top3_rules[0][0] if top3_rules else None

    # Check if correct (TOP-1)
    if top1_rule == expected_rule:
        correct_top1 += 1

    # Check if correct (TOP-3) - expected rule in any of top 3
    if expected_rule in top3_rule_nums:
        correct_top3 += 1

    # Track by rule
    if expected_rule not in rule_accuracy:
        rule_accuracy[expected_rule] = {'correct': 0, 'total': 0}
    rule_accuracy[expected_rule]['total'] += 1
    if expected_rule in top3_rule_nums:
        rule_accuracy[expected_rule]['correct'] += 1

    if i % 25 == 0:
        accuracy_top1 = (correct_top1 / i) * 100
        accuracy_top3 = (correct_top3 / i) * 100
        print(f"  [{i:3d}/100] Top-1: {accuracy_top1:.1f}% | Top-3: {accuracy_top3:.1f}%")

accuracy_top1 = (correct_top1 / len(questions)) * 100
accuracy_top3 = (correct_top3 / len(questions)) * 100

print()
print("=" * 80)
print("RESULTS: TOP-3 RETRIEVAL vs TOP-1")
print("=" * 80)
print()

print(f"Top-1 Only:    {correct_top1}/100 ({accuracy_top1:.1f}%) - Current baseline")
print(f"Top-3 (ANY):   {correct_top3}/100 ({accuracy_top3:.1f}%) - With LLM decision")
print()

improvement = accuracy_top3 - accuracy_top1
print(f"Potential Improvement: +{improvement:.1f}%")
print(f"Target: +5-10% improvement")
print()

if improvement >= 5:
    print(f"✅ SUCCESS! Top-3 gives +{improvement:.1f}% improvement")
    print(f"   When LLM gets top-3 rules, expected accuracy: ~{accuracy_top1 + improvement:.1f}%")
else:
    print(f"⚠️  Only +{improvement:.1f}% improvement (expected 5-10%)")

print()
print("=" * 80)
print("WHAT THIS MEANS FOR PHASE 2+")
print("=" * 80)
print()

print("With Top-3 retrieval, LLM sees 3 rule options per question.")
print("This lets the LLM pick the best one based on semantic understanding.")
print()

print("Phase 2 will then add keyword boosting for problem rules (6, 9, 13).")
print("This should push those 0% rules up significantly.")
print()

print("Expected final: 36% → 50-63% with all 4 phases")
print()

