"""
Phase 2: Semantic Chunking for NBA Rulebook
Rule-based hierarchical chunking with metadata attachment.

Approach:
  - Parse rules hierarchically (Rule → Section → Subsection)
  - Tokenize with tiktoken (GPT-compatible)
  - Create ~512-token chunks with 10-15% overlap
  - Attach comprehensive metadata for citation
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import tiktoken
except ImportError:
    print("Installing tiktoken...")
    import subprocess
    subprocess.check_call(["python3", "-m", "pip", "install", "-q", "tiktoken"])
    import tiktoken


@dataclass
class ChunkMetadata:
    """Metadata for a single chunk."""
    chunk_id: str
    rule_number: int
    rule_title: str
    section_number: str
    section_title: str
    subsection: str = None
    page_number: int = None
    source_file: str = "Official-2025-26-NBA-Playing-Rules.pdf"
    start_char_offset: int = 0
    end_char_offset: int = 0
    token_count: int = 0
    has_overlap: bool = False
    overlap_tokens: int = 0
    is_complete: bool = True
    content_type: str = "rule_content"


@dataclass
class Chunk:
    """A single text chunk with metadata."""
    text: str
    metadata: ChunkMetadata


class NBAChunker:
    """Chunk NBA rulebook hierarchically by rule and section."""

    def __init__(self, raw_text_path: str, encoding_name: str = "cl100k_base"):
        """
        Initialize chunker.

        Args:
            raw_text_path: Path to raw extracted text
            encoding_name: tiktoken encoding (default: GPT-4 compatible)
        """
        self.raw_text_path = Path(raw_text_path)
        self.encoder = tiktoken.get_encoding(encoding_name)
        self.encoding_name = encoding_name

        # Load raw text
        with open(self.raw_text_path, 'r', encoding='utf-8') as f:
            self.raw_text = f.read()

        self.chunks: List[Chunk] = []
        self.statistics = {
            "total_rules": 0,
            "total_sections": 0,
            "total_chunks": 0,
            "total_tokens": 0,
            "avg_tokens_per_chunk": 0,
            "min_tokens": float('inf'),
            "max_tokens": 0,
            "chunks_with_overlap": 0,
        }

    def tokenize(self, text: str) -> List[int]:
        """Tokenize text using tiktoken."""
        return self.encoder.encode(text)

    def detokenize(self, tokens: List[int]) -> str:
        """Convert tokens back to text."""
        return self.encoder.decode(tokens)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenize(text))

    def extract_rules(self) -> List[Tuple[int, str, int, int]]:
        """
        Extract rules from raw text.

        Returns:
            List of (rule_number, rule_title, start_offset, end_offset)
        """
        rule_pattern = r'RULE\s+NO\.\s*(\d+)—(.+?)(?=RULE\s+NO|$)'
        rules = []

        for match in re.finditer(rule_pattern, self.raw_text, re.DOTALL):
            rule_number = int(match.group(1))
            rule_title = match.group(2).strip().split('\n')[0]  # First line is title
            start_offset = match.start()

            rules.append((rule_number, rule_title, start_offset))

        # Set end offsets
        rules_with_offsets = []
        for i, (rule_num, rule_title, start) in enumerate(rules):
            # Get the match object to find the actual end
            pattern = r'RULE\s+NO\.\s*(\d+)—(.+?)(?=RULE\s+NO|$)'
            matches = list(re.finditer(pattern, self.raw_text, re.DOTALL))
            if i < len(matches):
                end = matches[i].end()
            else:
                end = len(self.raw_text)
            rules_with_offsets.append((rule_num, rule_title, start, end))

        return rules_with_offsets

    def extract_sections(self, rule_text: str) -> List[Tuple[str, str, int, int]]:
        """
        Extract sections from rule text.

        Returns:
            List of (section_number, section_title, start_offset, end_offset)
        """
        section_pattern = r'Section\s+([IVX]+)\s*(?:–|—)\s*([^\n]+)'
        sections = []

        for match in re.finditer(section_pattern, rule_text):
            section_number = match.group(1)
            section_title = match.group(2).strip()
            start_offset = match.start()

            sections.append((section_number, section_title, start_offset))

        # Set end offsets
        sections_with_offsets = []
        for i, (sec_num, sec_title, start) in enumerate(sections):
            end = sections[i + 1][2] if i + 1 < len(sections) else len(rule_text)
            sections_with_offsets.append((sec_num, sec_title, start, end))

        return sections_with_offsets

    def chunk_section(
        self,
        section_text: str,
        rule_number: int,
        rule_title: str,
        section_number: str,
        section_title: str,
        page_number: int,
        text_offset: int,
        target_tokens: int = 512,
        overlap_fraction: float = 0.125,
    ) -> List[Chunk]:
        """
        Break a section into chunks with overlap.

        Args:
            section_text: Text of the section
            rule_number: Rule number
            rule_title: Rule title
            section_number: Section number (I, II, III, etc.)
            section_title: Section title
            page_number: Starting page number
            text_offset: Character offset in raw text
            target_tokens: Target tokens per chunk
            overlap_fraction: Overlap as fraction of chunk size

        Returns:
            List of chunks
        """
        chunks = []
        tokens = self.tokenize(section_text)
        overlap_size = int(target_tokens * overlap_fraction)

        if len(tokens) <= target_tokens:
            # Section fits in one chunk
            chunk_text = section_text
            chunk_tokens = len(tokens)

            metadata = ChunkMetadata(
                chunk_id=f"rule_{rule_number}_section_{section_number}_chunk_1",
                rule_number=rule_number,
                rule_title=rule_title,
                section_number=section_number,
                section_title=section_title,
                page_number=page_number,
                start_char_offset=text_offset,
                end_char_offset=text_offset + len(chunk_text),
                token_count=chunk_tokens,
                has_overlap=False,
            )

            chunks.append(Chunk(text=chunk_text, metadata=metadata))

        else:
            # Break into multiple chunks with overlap
            chunk_idx = 1
            current_offset = 0
            previous_overlap_text = ""

            while current_offset < len(tokens):
                # Define chunk boundaries
                chunk_start = max(0, current_offset - (len(previous_overlap_text) // 4))
                chunk_end = min(len(tokens), current_offset + target_tokens)

                # Extract chunk tokens and convert back to text
                chunk_tokens_list = tokens[chunk_start:chunk_end]
                chunk_text = self.detokenize(chunk_tokens_list)

                # Handle overlap
                has_overlap = chunk_idx > 1
                overlap_tokens = 0
                if has_overlap and previous_overlap_text:
                    # Ensure overlap is preserved
                    if not chunk_text.startswith(previous_overlap_text[:50]):
                        chunk_text = previous_overlap_text + " " + chunk_text

                    overlap_tokens = len(self.tokenize(previous_overlap_text))

                metadata = ChunkMetadata(
                    chunk_id=f"rule_{rule_number}_section_{section_number}_chunk_{chunk_idx}",
                    rule_number=rule_number,
                    rule_title=rule_title,
                    section_number=section_number,
                    section_title=section_title,
                    page_number=page_number,
                    start_char_offset=text_offset + current_offset,
                    end_char_offset=text_offset + current_offset + len(chunk_text),
                    token_count=len(chunk_tokens_list),
                    has_overlap=has_overlap,
                    overlap_tokens=overlap_tokens,
                )

                chunks.append(Chunk(text=chunk_text, metadata=metadata))

                # Prepare overlap for next chunk
                overlap_start = max(0, chunk_end - overlap_size)
                previous_overlap_text = self.detokenize(tokens[overlap_start:chunk_end])

                current_offset = chunk_end
                chunk_idx += 1

        return chunks

    def chunk_all(self, target_tokens: int = 512, overlap_fraction: float = 0.125) -> List[Chunk]:
        """
        Chunk entire rulebook hierarchically.

        Args:
            target_tokens: Target tokens per chunk
            overlap_fraction: Overlap fraction (default 12.5% = 1/8)

        Returns:
            List of all chunks
        """
        print("📖 Chunking NBA rulebook...")
        print(f"  Target: ~{target_tokens} tokens per chunk")
        print(f"  Overlap: {overlap_fraction*100:.1f}%\n")

        rules = self.extract_rules()
        self.statistics["total_rules"] = len(rules)

        all_chunks = []

        for rule_idx, (rule_number, rule_title, rule_start, rule_end) in enumerate(rules):
            if (rule_idx + 1) % 5 == 0:
                print(f"  Processing rule {rule_idx + 1}/{len(rules)}...")

            rule_text = self.raw_text[rule_start:rule_end]
            sections = self.extract_sections(rule_text)

            for section_number, section_title, section_start, section_end in sections:
                section_text = rule_text[section_start:section_end]
                section_offset = rule_start + section_start

                # Estimate page number (rough approximation)
                char_per_page = 2976  # From Phase 1 stats
                page_number = section_offset // char_per_page + 1

                # Chunk the section
                section_chunks = self.chunk_section(
                    section_text=section_text,
                    rule_number=rule_number,
                    rule_title=rule_title,
                    section_number=section_number,
                    section_title=section_title,
                    page_number=int(page_number),
                    text_offset=section_offset,
                    target_tokens=target_tokens,
                    overlap_fraction=overlap_fraction,
                )

                all_chunks.extend(section_chunks)

            self.statistics["total_sections"] += len(sections)

        self.chunks = all_chunks

        # Calculate statistics
        self.statistics["total_chunks"] = len(all_chunks)
        if all_chunks:
            token_counts = [c.metadata.token_count for c in all_chunks]
            self.statistics["total_tokens"] = sum(token_counts)
            self.statistics["avg_tokens_per_chunk"] = int(
                self.statistics["total_tokens"] / len(all_chunks)
            )
            self.statistics["min_tokens"] = min(token_counts)
            self.statistics["max_tokens"] = max(token_counts)
            self.statistics["chunks_with_overlap"] = sum(
                1 for c in all_chunks if c.metadata.has_overlap
            )

        print(f"\n✅ Chunking complete!")
        print(f"  Rules: {self.statistics['total_rules']}")
        print(f"  Sections: {self.statistics['total_sections']}")
        print(f"  Chunks: {self.statistics['total_chunks']}")
        print(f"  Avg tokens/chunk: {self.statistics['avg_tokens_per_chunk']}")
        print(f"  Range: {self.statistics['min_tokens']}-{self.statistics['max_tokens']} tokens")

        return all_chunks

    def save_chunks(self, output_dir: str = "data") -> None:
        """
        Save chunks to JSON and individual files.

        Args:
            output_dir: Directory to save outputs
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        # Save all chunks to single JSON
        chunks_json = {
            "extraction_timestamp": datetime.now().isoformat(),
            "encoding": self.encoding_name,
            "target_tokens": 512,
            "total_chunks": len(self.chunks),
            "statistics": self.statistics,
            "chunks": [
                {
                    "text": chunk.text,
                    "metadata": asdict(chunk.metadata),
                }
                for chunk in self.chunks
            ],
        }

        chunks_file = output_dir / "04_chunked_text.json"
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_json, f, indent=2)

        print(f"\n💾 Saved chunks: {chunks_file}")

        # Save statistics
        stats_file = output_dir / "05_chunk_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.statistics, f, indent=2)

        print(f"💾 Saved statistics: {stats_file}")

        # Save individual chunk files
        chunks_dir = output_dir / "chunks"
        chunks_dir.mkdir(exist_ok=True)

        for chunk in self.chunks:
            chunk_file = chunks_dir / f"{chunk.metadata.chunk_id}.txt"
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(f"# {chunk.metadata.chunk_id}\n")
                f.write(f"# Rule {chunk.metadata.rule_number}: {chunk.metadata.rule_title}\n")
                f.write(f"# Section {chunk.metadata.section_number}: {chunk.metadata.section_title}\n")
                f.write(f"# Page {chunk.metadata.page_number}, Tokens: {chunk.metadata.token_count}\n\n")
                f.write(chunk.text)

        print(f"💾 Saved {len(self.chunks)} individual chunk files to {chunks_dir}")

    def validate(self) -> Dict[str, any]:
        """
        Validate chunking quality.

        Returns:
            Validation report
        """
        print("\n🔍 Validating chunks...")

        validation = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
        }

        # Check 1: All chunks have metadata
        complete_metadata = all(
            chunk.metadata.chunk_id and chunk.metadata.rule_number
            for chunk in self.chunks
        )
        validation["checks"]["metadata_complete"] = {
            "status": "PASS" if complete_metadata else "FAIL",
            "message": f"All {len(self.chunks)} chunks have complete metadata"
            if complete_metadata
            else "Some chunks missing metadata",
        }

        # Check 2: Token count validation
        avg_tokens = self.statistics["avg_tokens_per_chunk"]
        target = 512
        token_variance = abs(avg_tokens - target) / target
        token_ok = token_variance < 0.15  # Within 15% of target

        validation["checks"]["token_count"] = {
            "status": "PASS" if token_ok else "WARNING",
            "avg_tokens": avg_tokens,
            "target_tokens": target,
            "variance": f"{token_variance*100:.1f}%",
        }

        # Check 3: Overlap validation
        overlapped = self.statistics["chunks_with_overlap"]
        total = self.statistics["total_chunks"]
        overlap_fraction = overlapped / total if total > 0 else 0

        validation["checks"]["overlap"] = {
            "status": "PASS",
            "chunks_with_overlap": overlapped,
            "total_chunks": total,
            "overlap_fraction": f"{overlap_fraction*100:.1f}%",
        }

        # Check 4: Citation readiness
        citation_ready = all(
            chunk.metadata.rule_number and chunk.metadata.page_number
            for chunk in self.chunks
        )

        validation["checks"]["citation_ready"] = {
            "status": "PASS" if citation_ready else "FAIL",
            "message": "All chunks traceable to rule/page"
            if citation_ready
            else "Some chunks missing citation info",
        }

        # Summary
        all_pass = all(
            check.get("status") == "PASS" for check in validation["checks"].values()
        )
        validation["overall_status"] = "PASS" if all_pass else "WARNING"

        print(f"\n📊 Validation Results:")
        for check_name, check_result in validation["checks"].items():
            status = check_result.get("status", "UNKNOWN")
            print(f"  {check_name.upper()}: {status}")

        return validation

    def save_validation(self, validation: Dict, output_dir: str = "data") -> None:
        """Save validation report."""
        output_dir = Path(output_dir)
        validation_file = output_dir / "06_chunk_validation_report.json"

        with open(validation_file, 'w', encoding='utf-8') as f:
            json.dump(validation, f, indent=2)

        print(f"💾 Saved validation: {validation_file}")


def main():
    """Main chunking pipeline."""
    raw_text_path = Path("data/01_raw_extracted_text.txt")

    if not raw_text_path.exists():
        print(f"❌ Error: {raw_text_path} not found")
        print("   Run 'python3 extract_pdf.py' first")
        return

    # Initialize chunker
    chunker = NBAChunker(str(raw_text_path))

    # Chunk rulebook
    chunks = chunker.chunk_all(target_tokens=512, overlap_fraction=0.125)

    # Validate
    validation = chunker.validate()

    # Save outputs
    chunker.save_chunks()
    chunker.save_validation(validation)

    print("\n✅ Phase 2 Complete!")
    print(f"   {len(chunks)} chunks created")
    print(f"   Files saved to data/")


if __name__ == "__main__":
    main()
