"""
Create Enhanced Super Chunks with:
1. Traveling (Rule 4 IX + Rule 10 XIII)
2. Goaltending (Rule 11)
3. Fouls (Rule 12 - all types)
"""

import json

print("=" * 80)
print("CREATING ENHANCED SUPER CHUNKS (3 Consolidated Rules)")
print("=" * 80)
print()

# Load original chunks
with open('data/09_stable_chunks.json', 'r') as f:
    data = json.load(f)

chunks = data['chunks']
print(f"Loaded {len(chunks)} original chunks")
print()

# Extract traveling content
traveling_text = "TRAVELING VIOLATION - COMPREHENSIVE DEFINITION AND RULES\n\n"
traveling_sources = []

for chunk in chunks:
    meta = chunk['metadata']
    if meta['rule_number'] in [4, 10] and 'Traveling' in meta['section_title']:
        traveling_text += chunk['text'] + "\n\n"
        traveling_sources.append(
            f"Rule {meta['rule_number']}, Section {meta['section_number']}"
        )

print(f"✅ Traveling Super Chunk")
print(f"   Sources: {', '.join(traveling_sources)}")
print(f"   Size: {len(traveling_text)} characters")
print()

# Extract goaltending content
goaltending_text = "GOALTENDING - DEFENSIVE AND OFFENSIVE INTERFERENCE\n\n"
goaltending_sources = []

for chunk in chunks:
    meta = chunk['metadata']
    if meta['rule_number'] == 11:
        goaltending_text += chunk['text'] + "\n\n"
        goaltending_sources.append(
            f"Rule {meta['rule_number']}, Section {meta['section_number']}"
        )

print(f"✅ Goaltending Super Chunk")
print(f"   Sources: {', '.join(goaltending_sources)}")
print(f"   Size: {len(goaltending_text)} characters")
print()

# Extract fouls content (ALL of Rule 12)
fouls_text = "FOULS AND PENALTIES - COMPREHENSIVE GUIDE\n\nIncludes: Personal Fouls, Technical Fouls, Flagrant Fouls, Unsportsmanlike Fouls, Clear Path Fouls, Away-from-Play Fouls, Double Technical Fouls, and All Associated Penalties\n\n"
fouls_sources = []

for chunk in chunks:
    meta = chunk['metadata']
    if meta['rule_number'] == 12:
        fouls_text += chunk['text'] + "\n\n"
        fouls_sources.append(
            f"Rule {meta['rule_number']}, Section {meta['section_number']}"
        )

print(f"✅ Fouls Super Chunk")
print(f"   Sources: {len(fouls_sources)} sections")
print(f"   Size: {len(fouls_text)} characters")
print()

# Create super chunk objects
traveling_chunk = {
    "id": "suparchunk_traveling_001",
    "text": traveling_text,
    "metadata": {
        "rule_number": 4,
        "rule_title": "Player Movements",
        "section_number": "IX-XIII",
        "section_title": "Traveling (Comprehensive Definition + Violations)",
        "page_number": "14-31",
        "is_suparchunk": True,
    }
}

goaltending_chunk = {
    "id": "suparchunk_goaltending_001",
    "text": goaltending_text,
    "metadata": {
        "rule_number": 11,
        "rule_title": "Basket Interference",
        "section_number": "I",
        "section_title": "Goaltending (Comprehensive Definition)",
        "page_number": "43",
        "is_suparchunk": True,
    }
}

fouls_chunk = {
    "id": "suparchunk_fouls_001",
    "text": fouls_text,
    "metadata": {
        "rule_number": 12,
        "rule_title": "Fouls and Penalties",
        "section_number": "I-IX",
        "section_title": "Fouls and Penalties (Comprehensive Guide)",
        "page_number": "35-42",
        "is_suparchunk": True,
    }
}

# Remove old chunks for these rules
filtered_chunks = []
removed_count = 0

for chunk in chunks:
    meta = chunk['metadata']
    # Remove traveling chunks
    if meta['rule_number'] == 4 and 'Traveling' in meta['section_title']:
        removed_count += 1
        continue
    # Remove traveling violations chunks
    elif meta['rule_number'] == 10 and 'Traveling' in meta['section_title']:
        removed_count += 1
        continue
    # Remove goaltending chunks
    elif meta['rule_number'] == 11:
        removed_count += 1
        continue
    # Remove fouls chunks
    elif meta['rule_number'] == 12:
        removed_count += 1
        continue
    else:
        filtered_chunks.append(chunk)

print(f"Removed {removed_count} old chunks for consolidation")
print()

# Add super chunks at beginning
enhanced_chunks = [traveling_chunk, goaltending_chunk, fouls_chunk] + filtered_chunks

print(f"✅ Total chunks: {len(chunks)} → {len(enhanced_chunks)}")
print(f"   Added: 3 super chunks")
print(f"   Removed: {removed_count} specific chunks")
print(f"   Net change: {len(enhanced_chunks) - len(chunks)}")
print()

# Save enhanced chunks
output_data = {
    'version': '2.1',
    'format': 'json',
    'created_at': 'enhanced',
    'total_chunks': len(enhanced_chunks),
    'statistics': {
        'total_rules': 14,
        'super_chunks': 3,
        'consolidated_rules': [4, 11, 12],
    },
    'chunks': enhanced_chunks
}

with open('data/09_stable_chunks_enhanced.json', 'w') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"✅ Saved enhanced chunks to: data/09_stable_chunks_enhanced.json")
print()

# Summary
print("=" * 80)
print("ENHANCED SUPER CHUNKS SUMMARY")
print("=" * 80)
print()

super_chunk_names = [
    ("Traveling Violation", 4, len(traveling_text)),
    ("Goaltending", 11, len(goaltending_text)),
    ("Fouls and Penalties", 12, len(fouls_text)),
]

for name, rule, size in super_chunk_names:
    print(f"Rule {rule:2d}: {name:<30} {size:>6,} chars")

print()
print(f"Non-super chunks: {len(filtered_chunks)}")
print(f"Total: {len(enhanced_chunks)}")
print()
