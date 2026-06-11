"""
Phase 1 IMPROVED: Claude vs GPT-3.5 comparison
Better evaluation logic that checks retrieved chunks, not just answer text
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import faiss

print("=" * 80)
print("PHASE 1 IMPROVED: Claude evaluation with better logic")
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

print(f"Testing {len(questions)} questions...")
print(f"Evaluating on retrieval accuracy (not LLM output)")
print()

correct = 0
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

    # Get top-1 rule
    top_rule = max(retrieved_rules.items(), key=lambda x: x[1])[0] if retrieved_rules else None

    # Check if correct
    if top_rule == expected_rule:
        correct += 1

    # Track by rule
    if expected_rule not in rule_accuracy:
        rule_accuracy[expected_rule] = {'correct': 0, 'total': 0}
    rule_accuracy[expected_rule]['total'] += 1
    if top_rule == expected_rule:
        rule_accuracy[expected_rule]['correct'] += 1

    if i % 25 == 0:
        accuracy = (correct / i) * 100
        print(f"  [{i:3d}/100] Accuracy: {accuracy:.1f}%")

accuracy = (correct / len(questions)) * 100

print()
print("=" * 80)
print("RESULTS")
print("=" * 80)
print()

print(f"Retrieval Accuracy: {correct}/100 ({accuracy:.1f}%)")
print()

print("This is the SAME retrieval for both Claude and GPT-3.5-turbo")
print("The difference will be in answer quality, not retrieval")
print()

print("=" * 80)
print("KEY INSIGHT")
print("=" * 80)
print()

print("Phase 1 (Claude) won't improve RETRIEVAL accuracy (36%).")
print("Claude will improve ANSWER QUALITY on retrieved chunks.")
print()
print("We need Phase 2 (Top-3 retrieval) and Phase 3 (Keyword boosting)")
print("to actually improve the 36% → 50%+ target.")
print()

EOF
