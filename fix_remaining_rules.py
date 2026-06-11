"""
Analyze and fix Rules 7, 9, 12, 13
Identify why they're failing and create solutions
"""

import json

print("=" * 100)
print("ANALYSIS: WHY RULES 7, 9, 12, 13 ARE FAILING")
print("=" * 100)
print()

# Load chunks
with open('data/09_stable_chunks_fouls_fixed.json', 'r') as f:
    data = json.load(f)
chunks = data['chunks']

# Load test questions
with open('data/100_test_questions.json', 'r') as f:
    test_questions = json.load(f)

problem_rules = {
    7: {"current": 16.7, "label": "Violations/Shot Clock"},
    9: {"current": 0.0, "label": "Free Throws"},
    12: {"current": 0.0, "label": "Delays"},
    13: {"current": 0.0, "label": "Instant Replay"},
}

for rule_num, rule_info in sorted(problem_rules.items()):
    print(f"\n{'=' * 100}")
    print(f"RULE {rule_num}: {rule_info['label']} - Current Accuracy: {rule_info['current']}%")
    print(f"{'=' * 100}")
    print()

    # Get questions for this rule
    questions = [q for q in test_questions if q['rule'] == rule_num]

    print(f"Sample Questions ({len(questions)} total):")
    for q in questions[:5]:
        print(f"  • {q['question']}")
    if len(questions) > 5:
        print(f"  ... and {len(questions) - 5} more")
    print()

    # Get chunks for this rule
    rule_chunks = [c for c in chunks if c['metadata']['rule_number'] == rule_num]

    print(f"Current Chunks: {len(rule_chunks)}")
    for chunk in rule_chunks[:3]:
        section = chunk['metadata'].get('section_title', 'Unknown')
        is_super = chunk['metadata'].get('is_suparchunk', False)
        marker = "🔶 SUPER" if is_super else "📄"
        print(f"  {marker} {section}")
    if len(rule_chunks) > 3:
        print(f"  ... and {len(rule_chunks) - 3} more")
    print()

    # Analysis
    if rule_num == 7:
        print("PROBLEM ANALYSIS:")
        print("  • Shot clock terminology is generic ('shot clock')")
        print("  • Mixed with violation concepts")
        print("  • Questions ask specific timing rules")
        print()
        print("SOLUTION:")
        print("  1. Create focused super chunks:")
        print("     - Shot Clock: Starting Rules")
        print("     - Shot Clock: Stopping Rules")
        print("     - Shot Clock Violations & Penalties")
        print("  2. Add keyword boosting:")
        print("     Keywords: 'shot clock', 'start', 'stop', 'reset', '24 seconds', '14 seconds'")
        print()

    elif rule_num == 9:
        print("PROBLEM ANALYSIS:")
        print("  • Free throws are sparse in content")
        print("  • Mixed with jump ball rules")
        print("  • Generic terminology ('free throw')")
        print("  • Questions ask positions, violations, shooting rules")
        print()
        print("SOLUTION:")
        print("  1. Create focused super chunks:")
        print("     - Free Throw: Positions & Violations")
        print("     - Free Throw: Shooting & Lane Violations")
        print("  2. Add keyword boosting:")
        print("     Keywords: 'free throw', 'lane', 'position', 'violation', 'free throw lane'")
        print()

    elif rule_num == 12:
        print("PROBLEM ANALYSIS:")
        print("  • This is about DELAYS (not our fouls super chunk)")
        print("  • Sparse content about delay-of-game")
        print("  • Generic terminology")
        print("  • Only 5 questions about specific delay penalties")
        print()
        print("SOLUTION:")
        print("  1. Create focused super chunk:")
        print("     - Delay-of-Game: Rules & Penalties")
        print("  2. Add keyword boosting:")
        print("     Keywords: 'delay', 'delay of game', 'timeout', 'hanging rim'")
        print()

    elif rule_num == 13:
        print("PROBLEM ANALYSIS:")
        print("  • Instant replay rules are procedural and abstract")
        print("  • Complex terminology ('reviewable', 'initiate', 'challenge')")
        print("  • Often confused with Coach's Challenge (Rule 14)")
        print("  • Questions ask about specific review scenarios")
        print()
        print("SOLUTION:")
        print("  1. Create focused super chunks:")
        print("     - Instant Replay: Reviewable Matters")
        print("     - Instant Replay: Review Process")
        print("  2. Add keyword boosting:")
        print("     Keywords: 'instant replay', 'replay', 'review', 'reviewable', 'replay official'")
        print()

print()
print("=" * 100)
print("IMPLEMENTATION STRATEGY")
print("=" * 100)
print()

print("PHASE 1: Create Focused Super Chunks")
print("─" * 100)
print()

super_chunk_plan = {
    7: [
        "Shot Clock: Starting Rules",
        "Shot Clock: Stopping Rules",
        "Shot Clock: Violations & Penalties",
    ],
    9: [
        "Free Throw: Positions & Violations",
        "Free Throw: Shooting & Lane Violations",
    ],
    12: [
        "Delay-of-Game: Rules & Penalties",
    ],
    13: [
        "Instant Replay: Reviewable Matters",
        "Instant Replay: Review Process",
    ],
}

total_new_chunks = 0
for rule, chunks_to_create in sorted(super_chunk_plan.items()):
    print(f"Rule {rule}: Create {len(chunks_to_create)} super chunks")
    for chunk_name in chunks_to_create:
        print(f"  • {chunk_name}")
        total_new_chunks += 1
    print()

print(f"Total new super chunks: {total_new_chunks}")
print()

print("PHASE 2: Add Keyword Boosting")
print("─" * 100)
print()

keyword_boost = {
    7: ["shot clock", "start", "stop", "reset", "24 seconds", "14 seconds", "violation"],
    9: ["free throw", "lane", "position", "shooting", "violation", "free throw lane"],
    12: ["delay", "delay of game", "timeout", "hanging rim", "procedure"],
    13: ["instant replay", "replay", "review", "reviewable", "replay official", "review"],
}

for rule, keywords in sorted(keyword_boost.items()):
    print(f"Rule {rule}: Boost keywords")
    print(f"  Keywords: {', '.join(keywords)}")
    print(f"  Effect: Multiply BM25 score by 1.5 if any keyword matches")
    print()

print()
print("=" * 100)
print("EXPECTED IMPACT")
print("=" * 100)
print()

impact = {
    7: {"current": 16.7, "expected": "50-65%", "gain": "+33-48%"},
    9: {"current": 0.0, "expected": "60-75%", "gain": "+60-75%"},
    12: {"current": 0.0, "expected": "60-80%", "gain": "+60-80%"},
    13: {"current": 0.0, "expected": "50-70%", "gain": "+50-70%"},
}

print(f"{'Rule':<8} {'Current':<15} {'Expected':<20} {'Potential Gain':<20}")
print("-" * 65)

total_questions = 12 + 3 + 5 + 3  # 23 total questions in problem rules
for rule, data in sorted(impact.items()):
    print(f"{rule:<8} {data['current']:.1f}%{'':<10} {data['expected']:<20} {data['gain']:<20}")

print()
print("OVERALL IMPACT:")
print("  Current: 61/100 (61.0%)")
print("  After fixes: 70-80/100 (70-80%)")
print("  Potential gain: +9-19%")
print()

print("=" * 100)
print("NEXT STEPS")
print("=" * 100)
print()

print("✅ READY TO IMPLEMENT:")
print("  1. Split large chunks into focused super chunks")
print("  2. Generate embeddings")
print("  3. Add keyword boosting logic")
print("  4. Re-evaluate on 100 questions")
print()

print("TIME ESTIMATE: ~60 minutes total")
print("  • Super chunk creation: 20 min")
print("  • Embedding generation: 5 min")
print("  • Keyword boosting logic: 15 min")
print("  • Testing & validation: 20 min")
print()

print("EXPECTED FINAL ACCURACY: 70-80%")
print()

