"""
Diagnose why certain questions aren't retrieving the right chunks.
"""

from phase4_retrieval import RetrievalPipeline

# Initialize retrieval
retrieval = RetrievalPipeline()
retrieval.setup()

print()
print("=" * 80)
print("RETRIEVAL DIAGNOSTICS FOR FAILING QUESTIONS")
print("=" * 80)
print()

# Question 1: Traveling
print("Q1: What actions constitute a traveling violation?")
print("-" * 80)
print()

results = retrieval.retrieve("What actions constitute a traveling violation?", top_k=10, verbose=False)

print("Top 10 Retrieved Chunks:")
for i, result in enumerate(results, 1):
    print(f"{i}. Rule {result['rule_number']}, {result['citation']}")
    print(f"   Score: {result['similarity_score']:.3f}")
    print(f"   Text: {result['text'][:100]}...")
    print()

print("\n🔍 Analysis:")
print("Looking for: Rule 4, Section IX (Traveling)")
traveling_found = any(r['rule_number'] == 4 and 'traveling' in r['section_title'].lower() for r in results)
print(f"✅ Traveling section found: {traveling_found}")
if not traveling_found:
    print("❌ Traveling section NOT in top 10 - this is the problem!")
    print()
    print("💡 Why: The embedding for 'traveling violation' might be different")
    print("        from the actual 'Traveling' section title in the chunks.")

print()
print("=" * 80)
print()

# Question 2: Goaltending
print("Q2: When is defensive goaltending called?")
print("-" * 80)
print()

results = retrieval.retrieve("When is defensive goaltending called?", top_k=10, verbose=False)

print("Top 10 Retrieved Chunks:")
for i, result in enumerate(results, 1):
    print(f"{i}. Rule {result['rule_number']}, {result['citation']}")
    print(f"   Score: {result['similarity_score']:.3f}")
    print(f"   Text: {result['text'][:100]}...")
    print()

print("\n🔍 Analysis:")
print("Looking for: Rule 11, Section I (Goaltending)")
goaltending_found = any(r['rule_number'] == 11 for r in results)
print(f"✅ Goaltending section found: {goaltending_found}")
if not goaltending_found:
    print("❌ Goaltending section NOT in top 10 - this is the problem!")
    print()
    print("💡 Why: 'Goaltending' is a specific term but might not appear")
    print("        prominently in the chunk text, only in the title.")

print()
print("=" * 80)
print()

# Find the actual chunks
print("SOLUTION: Searching for Rule 4 and Rule 11 in all chunks...")
print()

rule_4_chunks = [c for c in retrieval.chunks if c['metadata']['rule_number'] == 4]
rule_11_chunks = [c for c in retrieval.chunks if c['metadata']['rule_number'] == 11]

print(f"Rule 4 (Traveling) has {len(rule_4_chunks)} chunks:")
for chunk in rule_4_chunks:
    print(f"  - Section {chunk['metadata']['section_number']}: {chunk['metadata']['section_title']}")

print()
print(f"Rule 11 (Goaltending) has {len(rule_11_chunks)} chunks:")
for chunk in rule_11_chunks:
    print(f"  - Section {chunk['metadata']['section_number']}: {chunk['metadata']['section_title']}")
    print(f"    Preview: {chunk['text'][:150]}...")

print()
print("=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print()
print("1. The chunks exist but aren't being retrieved well.")
print("2. This is a semantic search problem, not a chunking problem.")
print("3. Solutions:")
print("   - Fine-tune embeddings on NBA rule terminology")
print("   - Add rule-specific metadata (synonyms, alternative names)")
print("   - Use hybrid search (BM25 + semantic)")
print("   - Upgrade to Claude API (better semantic understanding)")
print()
