"""
Phase 2 (Enhanced): Re-chunking with Super Chunks
Creates dedicated super chunks for Traveling and Goaltending.
"""

import json
from pathlib import Path

def create_superchunks():
    """Create super chunks for traveling and goaltending."""

    # Load original chunks
    with open('data/09_stable_chunks.json', 'r') as f:
        data = json.load(f)

    # Extract chunks from the nested structure
    chunks = data['chunks']
    metadata = {
        'version': data.get('version'),
        'format': data.get('format'),
        'created_at': data.get('created_at'),
    }

    print("=" * 80)
    print("CREATING SUPER CHUNKS")
    print("=" * 80)
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

    print(f"✅ Traveling Super Chunk Created")
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

    print(f"✅ Goaltending Super Chunk Created")
    print(f"   Sources: {', '.join(goaltending_sources)}")
    print(f"   Size: {len(goaltending_text)} characters")
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
            "source_chunks": traveling_sources,
            "is_suparchunk": True,
        }
    }

    goaltending_chunk = {
        "id": "suparchunk_goaltending_001",
        "text": goaltending_text,
        "metadata": {
            "rule_number": 11,
            "rule_title": "Fouls and Penalties",
            "section_number": "I",
            "section_title": "Goaltending (Comprehensive Definition)",
            "page_number": "43",
            "source_chunks": goaltending_sources,
            "is_suparchunk": True,
        }
    }

    # Remove old traveling and goaltending chunks
    filtered_chunks = []
    removed_count = 0

    for chunk in chunks:
        meta = chunk['metadata']
        # Remove Rule 4 Section IX (traveling definition)
        if meta['rule_number'] == 4 and 'Traveling' in meta['section_title']:
            removed_count += 1
            continue
        # Remove Rule 10 Section XIII (traveling violations)
        elif meta['rule_number'] == 10 and 'Traveling' in meta['section_title']:
            removed_count += 1
            continue
        # Remove Rule 11 (goaltending)
        elif meta['rule_number'] == 11:
            removed_count += 1
            continue
        else:
            filtered_chunks.append(chunk)

    print(f"Removed {removed_count} old chunks")
    print()

    # Add super chunks at the beginning (higher priority)
    enhanced_chunks = [traveling_chunk, goaltending_chunk] + filtered_chunks

    print(f"✅ Total chunks after enhancement: {len(enhanced_chunks)}")
    print(f"   (was {len(chunks)}, removed {removed_count}, added 2 super chunks)")
    print()

    # Create output structure with same format
    output_data = {
        'version': metadata.get('version', '1.0'),
        'format': metadata.get('format', 'json'),
        'created_at': metadata.get('created_at', 'enhanced'),
        'total_chunks': len(enhanced_chunks),
        'statistics': {
            'total_rules': 14,
            'total_sections': 95,  # Reduced by removed sections, added by super chunks
            'total_tokens': 'TBD',
            'avg_chunk_size': 'TBD',
        },
        'chunks': enhanced_chunks
    }

    # Save enhanced chunks
    with open('data/09_stable_chunks_with_superchunks.json', 'w') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved enhanced chunks to: data/09_stable_chunks_with_superchunks.json")
    print()

    return enhanced_chunks


if __name__ == "__main__":
    chunks = create_superchunks()
