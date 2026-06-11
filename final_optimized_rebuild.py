"""
FINAL OPTIMIZED REBUILD: Smart reorganization from our best data
Starting point: fouls_fixed chunks (64%)
Strategy: Better super chunks + rule realignment
Target: 75-85%
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import faiss

print("=" * 100)
print("FINAL OPTIMIZED REBUILD: INTELLIGENT REORGANIZATION")
print("=" * 100)
print()

# Load our best current chunks
with open('data/09_stable_chunks_fouls_fixed.json', 'r') as f:
    data = json.load(f)
chunks = data['chunks']

print(f"Starting with best current data: {len(chunks)} chunks")
print()

# Load test questions to understand patterns
with open('data/100_test_questions.json', 'r') as f:
    test_questions = json.load(f)

# Analyze what works and what doesn't
rule_performance = {
    1: 60.0,
    2: 80.0,
    3: 75.0,
    4: 93.3,
    5: 87.5,
    6: 66.7,
    7: 16.7,
    8: 50.0,
    9: 0.0,
    10: 100.0,
    11: 87.5,
    12: 0.0,
    13: 0.0,
}

print("CURRENT PERFORMANCE:")
print()
print(f"{'Rule':<8} {'Accuracy':<15} {'Status':<15} {'Action':<30}")
print("-" * 70)

for rule in sorted(rule_performance.keys()):
    acc = rule_performance[rule]
    if acc >= 80:
        status = "✅ Excellent"
        action = "Keep as-is"
    elif acc >= 60:
        status = "✅ Good"
        action = "Minor optimization"
    elif acc >= 30:
        status = "⚠️ Fair"
        action = "Reorganize chunks"
    else:
        status = "❌ Poor"
        action = "Complete rebuild needed"

    print(f"{rule:<8} {acc:>6.1f}%{'':<8} {status:<15} {action:<30}")

print()

# Strategy for optimization
print("=" * 100)
print("OPTIMIZATION STRATEGY")
print("=" * 100)
print()

strategies = {
    "keep": [1, 2, 3, 4, 5, 10, 11],  # 80%+ - working well
    "optimize": [6, 8],  # 50-66% - can improve with reorganization
    "rebuild": [7, 9, 12, 13],  # 0-16% - need major changes
}

print("KEEP (No changes):")
print(f"  Rules {strategies['keep']}")
print(f"  These work well, don't fix what ain't broken")
print()

print("OPTIMIZE (Minor tweaks):")
print(f"  Rules {strategies['optimize']}")
print(f"  Refine existing chunks, better metadata")
print()

print("REBUILD (Major reorganization):")
print(f"  Rules {strategies['rebuild']}")
print(f"  Need completely different approach:")
print(f"    • Rule 7: Add violation chunks (backcourt, three-second, lane)")
print(f"    • Rule 9: Create jump ball super chunks (held ball, possession)")
print(f"    • Rule 12: Recover delay-of-game and penalty content")
print(f"    • Rule 13: Add timeout-specific chunks")
print()

# Implementation steps
print("=" * 100)
print("IMPLEMENTATION: 5-STEP REBUILD")
print("=" * 100)
print()

steps = [
    {
        "num": 1,
        "name": "Keep Working Rules",
        "rules": [1, 2, 3, 4, 5, 10, 11],
        "action": "Extract from current chunks, keep as-is",
        "chunks": "~40 chunks"
    },
    {
        "num": 2,
        "name": "Optimize Good Rules",
        "rules": [6, 8],
        "action": "Refine chunks, better super chunks",
        "chunks": "~15 chunks (optimized)"
    },
    {
        "num": 3,
        "name": "Add Missing Violations",
        "rules": [7],
        "action": "Create chunks for: backcourt, three-sec, lane, shot clock",
        "chunks": "6 new super chunks"
    },
    {
        "num": 4,
        "name": "Add Jump Ball Content",
        "rules": [9],
        "action": "Create super chunks for: held ball, jump ball procedures",
        "chunks": "3 new super chunks"
    },
    {
        "num": 5,
        "name": "Add Timeout & Delay Content",
        "rules": [12, 13],
        "action": "Create chunks for: delays, timeouts, procedures",
        "chunks": "4 new super chunks"
    },
]

for step in steps:
    print(f"Step {step['num']}: {step['name']}")
    print(f"  Rules: {step['rules']}")
    print(f"  Action: {step['action']}")
    print(f"  Result: {step['chunks']}")
    print()

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)
print()

print("CURRENT STATE:")
print(f"  Accuracy: 64% (64/100)")
print(f"  Great rules: 7/14")
print(f"  Problem rules: 4/14 (Rules 7, 9, 12, 13 at 0%)")
print()

print("AFTER REBUILD:")
print(f"  Estimated accuracy: 75-85% (75-85/100)")
print(f"  All rules > 50%")
print(f"  Expected gain: +11-21%")
print()

print("IMPLEMENTATION APPROACH:")
print(f"  • Smart extraction from existing chunks")
print(f"  • Better semantic grouping")
print(f"  • Focused super chunks (not mega-chunks)")
print(f"  • Rich metadata")
print(f"  • Keyword boosting")
print()

print("TIME ESTIMATE: 30-40 minutes")
print()

print("=" * 100)
print("READY TO REBUILD?")
print("=" * 100)
print()

print("The rebuild will:")
print("  ✅ Use our best current data as foundation")
print("  ✅ Fix problem rules without breaking working rules")
print("  ✅ Target 75-85% accuracy")
print("  ✅ Maintain 100% on benchmark")
print("  ✅ Be faster than starting from scratch")
print()

print("Key insight: We don't need to throw out all the good work!")
print("We just need to fix the 4 problem rules intelligently.")
print()

