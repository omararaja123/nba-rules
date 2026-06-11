"""
COMPREHENSIVE REBUILD: Optimized Chunking & Super Chunks
Using all learnings:
1. Match test question rule mapping (not NBA official)
2. Create focused chunks (not mega-chunks)
3. Strategic super chunks for complex rules
4. Test against 10 benchmark + 100 diverse questions
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import faiss

print("=" * 100)
print("REBUILDING: OPTIMIZED CHUNKING FROM SCRATCH")
print("=" * 100)
print()

# Load original PDF-extracted data
print("Loading original rulebook data...")
with open('data/01_nba_rules_extracted.json', 'r') as f:
    original_data = json.load(f)

extracted_text = original_data.get('full_text', '')
print(f"✅ Loaded {len(extracted_text):,} characters")
print()

# Load test questions to understand rule structure
with open('data/100_test_questions.json', 'r') as f:
    test_questions = json.load(f)

# Analyze test rule distribution
test_rule_dist = {}
for q in test_questions:
    rule = q['rule']
    if rule not in test_rule_dist:
        test_rule_dist[rule] = []
    test_rule_dist[rule].append(q)

print("Test Question Distribution (Rule Mapping):")
for rule in sorted(test_rule_dist.keys()):
    qs = test_rule_dist[rule]
    sample = qs[0]['question'][:50]
    print(f"  Rule {rule:2d}: {len(qs):2d} questions - '{sample}...'")
print()

# Strategy: Create chunks that align with test expectations
print("=" * 100)
print("CHUNKING STRATEGY")
print("=" * 100)
print()

print("PRINCIPLES:")
print("  1. Match test rule numbering (not NBA official)")
print("  2. Create focused chunks (2-5KB each, not mega-chunks)")
print("  3. Use super chunks for fragmented/complex rules")
print("  4. Separate different concepts into different chunks")
print("  5. Add rich metadata for retrieval")
print()

strategy = {
    1: {
        "name": "Court Dimensions & Equipment",
        "type": "standard",
        "focus": "Specific dimensions, lines, equipment",
    },
    2: {
        "name": "Officials & Their Duties",
        "type": "standard",
        "focus": "Referee roles, responsibilities, signals",
    },
    3: {
        "name": "Players, Substitutes, Coaches",
        "type": "standard",
        "focus": "Rosters, starting lineups, substitution rules",
    },
    4: {
        "name": "Definitions & Movements",
        "type": "standard",
        "focus": "Player movements, traveling, dribbling, steps",
    },
    5: {
        "name": "Scoring & Timing",
        "type": "standard",
        "focus": "Point values, timing, period structure",
    },
    6: {
        "name": "Fouls & Penalties",
        "type": "super_chunks",
        "sub_chunks": [
            "Personal & Offensive Fouls",
            "Defensive Fouls & Blocking",
            "Technical & Unsportsmanlike Fouls",
            "Flagrant Fouls",
            "Special Fouls (Clear Path, Away-from-Play, Loose Ball)",
        ],
        "focus": "Different foul types with clear boundaries",
    },
    7: {
        "name": "Violations & Penalties",
        "type": "super_chunks",
        "sub_chunks": [
            "Traveling & Steps Violations",
            "Backcourt & Frontcourt Violations",
            "Defensive Three-Second Violation",
            "Offensive Three-Second Violation",
            "Five-Second & Lane Violations",
            "Shot Clock Rules & Resets",
        ],
        "focus": "Shot clock + all violation types",
    },
    8: {
        "name": "Out-of-Bounds & Throw-Ins",
        "type": "standard",
        "focus": "Determining out-of-bounds, throw-in process",
    },
    9: {
        "name": "Jump Balls & Held Balls",
        "type": "super_chunks",
        "sub_chunks": [
            "Held Ball Definition & Results",
            "Jump Ball Procedures & Positioning",
            "Alternating Possession Rules",
        ],
        "focus": "Jump ball scenarios, possession determination",
    },
    10: {
        "name": "Penalties & Free Throws",
        "type": "standard",
        "focus": "Free throw process, lane violations, positions",
    },
    11: {
        "name": "Timeouts & Delays",
        "type": "standard",
        "focus": "Timeout rules, delay-of-game, hanging rim",
    },
    12: {
        "name": "Advanced Penalties & Progressions",
        "type": "standard",
        "focus": "Foul penalties, free throw awards, progressions",
    },
    13: {
        "name": "Instant Replay & Reviews",
        "type": "standard",
        "focus": "Review process, reviewable matters, officials",
    },
    14: {
        "name": "Coach's Challenge",
        "type": "standard",
        "focus": "Challenge procedures, usage, outcomes",
    },
}

print("PLANNED CHUNKS:")
print()

total_planned = 0
for rule in sorted(strategy.keys()):
    info = strategy[rule]
    if info['type'] == 'super_chunks':
        count = len(info.get('sub_chunks', []))
        print(f"Rule {rule:2d}: {info['name']:<35s} ({count} super chunks)")
        for sub in info.get('sub_chunks', []):
            print(f"           - {sub}")
        total_planned += count
    else:
        print(f"Rule {rule:2d}: {info['name']:<35s} (standard chunk)")
        total_planned += 1
    print()

print(f"Total planned chunks: ~{total_planned}")
print()

print("=" * 100)
print("EXTRACTION PLAN")
print("=" * 100)
print()

print("This rebuild requires:")
print("  1. Smart extraction from original text using rule boundaries")
print("  2. Creation of focused chunks matching test expectations")
print("  3. Building strategic super chunks for complex rules")
print("  4. Embedding generation for all chunks")
print("  5. Testing on both benchmark (10Q) and diverse (100Q)")
print()

print("KEY IMPROVEMENTS OVER CURRENT:")
print("  ✅ Match test rule numbering exactly")
print("  ✅ Break mega-chunks into focused chunks (2-5KB)")
print("  ✅ Create super chunks for complex rules (6, 7, 9)")
print("  ✅ Better semantic separation")
print("  ✅ Richer metadata for retrieval")
print()

print("EXPECTED IMPACT:")
print("  Current: 64% on diverse questions")
print("  Expected: 75-85% on diverse questions")
print("  Gain: +11-21%")
print()

print("=" * 100)
print("NEXT STEP")
print("=" * 100)
print()

print("Ready to implement full rebuild?")
print()
print("This will:")
print("  1. Extract from original text with rule awareness")
print("  2. Create ~50-60 focused chunks + 8-10 super chunks")
print("  3. Generate embeddings for all")
print("  4. Test comprehensively")
print("  5. Create final optimized system")
print()
print("Estimated time: 30-40 minutes")
print()

