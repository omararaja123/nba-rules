"""
Save chunks in stable, optimized JSON format for embeddings and metadata filtering.

This creates a production-ready chunks file with:
- Clean schema
- Separated text and metadata
- Optimized for embedding pipelines
- Easy metadata filtering
- JSONL format for streaming (optional)
"""

import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime


def normalize_chunk_ids(chunks: List[Dict]) -> List[Dict]:
    """Fix duplicate chunk IDs by adding global counter."""
    for i, chunk in enumerate(chunks, 1):
        rule = chunk["metadata"]["rule_number"]
        section = chunk["metadata"]["section_number"]
        chunk["metadata"]["chunk_id"] = f"rule_{rule:02d}_section_{section}_chunk_{i:03d}"
        chunk["metadata"]["global_chunk_index"] = i
    return chunks


def create_stable_format(chunks: List[Dict]) -> Dict:
    """Create optimized stable format for embeddings."""

    # Normalize IDs
    chunks = normalize_chunk_ids(chunks)

    # Create stable format
    stable_chunks = []

    for chunk in chunks:
        meta = chunk["metadata"]

        stable_chunk = {
            # Chunk identification
            "id": meta["chunk_id"],
            "global_index": meta["global_chunk_index"],

            # Content
            "text": chunk["text"],

            # Metadata for filtering
            "metadata": {
                # Rule & section info
                "rule_number": meta["rule_number"],
                "rule_title": meta["rule_title"],
                "section_number": meta["section_number"],
                "section_title": meta["section_title"],

                # Citation info
                "page_number": meta["page_number"],
                "source_file": meta["source_file"],

                # Technical info
                "token_count": meta["token_count"],
            },

            # For retrieval reranking
            "metadata_text": (
                f"Rule {meta['rule_number']}. {meta['rule_title']} - "
                f"Section {meta['section_number']}: {meta['section_title']}"
            ),
        }

        stable_chunks.append(stable_chunk)

    return {
        "version": "1.0",
        "format": "stable_chunks_for_embeddings",
        "created_at": datetime.now().isoformat(),
        "total_chunks": len(stable_chunks),
        "statistics": {
            "rules": len(set(c["metadata"]["rule_number"] for c in stable_chunks)),
            "sections": len(set(
                (c["metadata"]["rule_number"], c["metadata"]["section_number"])
                for c in stable_chunks
            )),
            "total_tokens": sum(c["metadata"]["token_count"] for c in stable_chunks),
            "avg_tokens": sum(c["metadata"]["token_count"] for c in stable_chunks) // len(stable_chunks),
        },
        "chunks": stable_chunks,
    }


def save_json(data: Dict, path: Path) -> None:
    """Save as formatted JSON."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved: {path}")


def save_jsonl(chunks: List[Dict], path: Path) -> None:
    """Save as JSONL (one JSON object per line) for streaming."""
    with open(path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    print(f"✅ Saved: {path}")


def save_csv(chunks: List[Dict], path: Path) -> None:
    """Save metadata as CSV for easy filtering/analysis."""
    import csv

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                'chunk_id',
                'rule_number',
                'rule_title',
                'section_number',
                'section_title',
                'page_number',
                'token_count',
            ]
        )
        writer.writeheader()

        for chunk in chunks:
            meta = chunk["metadata"]
            writer.writerow({
                'chunk_id': chunk["id"],
                'rule_number': meta["rule_number"],
                'rule_title': meta["rule_title"],
                'section_number': meta["section_number"],
                'section_title': meta["section_title"],
                'page_number': meta["page_number"],
                'token_count': meta["token_count"],
            })

    print(f"✅ Saved: {path}")


def main():
    """Generate stable chunk formats."""

    print("=" * 80)
    print("SAVING STABLE CHUNKS FOR EMBEDDINGS")
    print("=" * 80)
    print()

    # Load original chunks
    input_path = Path("data/04_chunked_text.json")
    with open(input_path) as f:
        data = json.load(f)

    original_chunks = data["chunks"]
    print(f"✅ Loaded {len(original_chunks)} chunks from {input_path}")
    print()

    # Create stable format
    print("Creating stable format...")
    stable_data = create_stable_format(original_chunks)
    stable_chunks = stable_data["chunks"]
    print(f"✅ Created stable format with {len(stable_chunks)} chunks")
    print()

    # Save formats
    output_dir = Path("data")

    print("Saving in multiple formats:")
    print()

    # 1. Main stable JSON
    save_json(
        stable_data,
        output_dir / "09_stable_chunks.json"
    )

    # 2. JSONL (for streaming)
    save_jsonl(
        stable_chunks,
        output_dir / "09_stable_chunks.jsonl"
    )

    # 3. CSV metadata (for filtering/analysis)
    save_csv(
        stable_chunks,
        output_dir / "09_stable_chunks_metadata.csv"
    )

    # 4. Index file (chunk IDs only, for quick lookups)
    index = {
        chunk["id"]: {
            "index": chunk["global_index"],
            "rule": chunk["metadata"]["rule_number"],
            "section": chunk["metadata"]["section_number"],
            "page": chunk["metadata"]["page_number"],
        }
        for chunk in stable_chunks
    }

    with open(output_dir / "09_chunks_index.json", 'w') as f:
        json.dump(index, f, indent=2)
    print(f"✅ Saved: {output_dir / '09_chunks_index.json'}")

    print()
    print("=" * 80)
    print("STATISTICS")
    print("=" * 80)
    print()

    print("Chunk Statistics:")
    print(f"  Total chunks: {len(stable_chunks)}")
    print(f"  Rules: {stable_data['statistics']['rules']}")
    print(f"  Sections: {stable_data['statistics']['sections']}")
    print(f"  Total tokens: {stable_data['statistics']['total_tokens']:,}")
    print(f"  Avg tokens/chunk: {stable_data['statistics']['avg_tokens']}")
    print()

    # Sample chunk
    print("Sample Chunk (ready for embedding):")
    print()
    sample = stable_chunks[0]
    print(f"ID: {sample['id']}")
    print(f"Rule: {sample['metadata']['rule_number']} - {sample['metadata']['rule_title']}")
    print(f"Section: {sample['metadata']['section_number']} - {sample['metadata']['section_title']}")
    print(f"Page: {sample['metadata']['page_number']}")
    print(f"Tokens: {sample['metadata']['token_count']}")
    print(f"Text: {sample['text'][:100]}...")
    print()

    print("=" * 80)
    print("FILES GENERATED")
    print("=" * 80)
    print()
    print("For Embedding Pipeline:")
    print("  1. 09_stable_chunks.json (main format, all data)")
    print("  2. 09_stable_chunks.jsonl (streaming format, one per line)")
    print()
    print("For Analysis & Filtering:")
    print("  3. 09_stable_chunks_metadata.csv (metadata only, for filters)")
    print("  4. 09_chunks_index.json (quick lookup index)")
    print()
    print("=" * 80)
    print()
    print("✅ Stable chunks ready for Phase 3 (Embedding)")
    print()
    print("Usage in Phase 3:")
    print("  # Load for embedding")
    print("  with open('data/09_stable_chunks.json') as f:")
    print("      data = json.load(f)")
    print("  chunks = data['chunks']")
    print()
    print("  # Embed all texts")
    print("  embeddings = [embed(c['text']) for c in chunks]")
    print()
    print("  # Filter by rule (e.g., Rule 4 only)")
    print("  rule_4_chunks = [c for c in chunks if c['metadata']['rule_number'] == 4]")
    print()


if __name__ == "__main__":
    main()
