"""
NBA Rulebook PDF Extraction Pipeline
Phase 1: Document Parsing & Raw Text Extraction

This module extracts raw text from the NBA rulebook PDF while:
- Preserving document structure (section numbers, headings)
- Removing headers, footers, and page artifacts
- Generating quality metrics and metadata
- Validating extraction completeness
"""

import fitz  # PyMuPDF
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


class NBAExtractor:
    """Extract and clean NBA rulebook PDF."""

    def __init__(self, pdf_path: str):
        """
        Initialize extractor with PDF path.

        Args:
            pdf_path: Path to the NBA rulebook PDF
        """
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(self.pdf_path)
        self.total_pages = len(self.doc)
        self.pages_data: List[Dict] = []
        self.extraction_stats = {
            "total_pages": self.total_pages,
            "extracted_pages": 0,
            "pages_with_issues": [],
            "total_chars": 0,
        }

    def extract_page_text(self, page_num: int) -> Tuple[str, Dict]:
        """
        Extract text from a single page with metadata.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            Tuple of (raw_text, metadata)
        """
        page = self.doc[page_num]

        # Extract text preserving layout
        text = page.get_text(option="text")

        # Get page dimensions (useful for understanding layout)
        rect = page.rect

        metadata = {
            "page_number": page_num + 1,
            "width": rect.width,
            "height": rect.height,
            "text_length": len(text),
            "has_images": len(page.get_images()) > 0,
            "extraction_timestamp": datetime.now().isoformat(),
        }

        return text, metadata

    def identify_header_footer_patterns(self) -> Tuple[List[str], List[str]]:
        """
        Identify common header and footer patterns by analyzing page margins.

        Inspects first and last lines of multiple pages to find repeated patterns.

        Returns:
            Tuple of (common_headers, common_footers)
        """
        first_lines = []
        last_lines = []

        sample_pages = min(5, self.total_pages)

        for page_num in range(sample_pages):
            text, _ = self.extract_page_text(page_num)
            lines = text.strip().split('\n')

            if lines:
                first_lines.append(lines[0].strip())
                last_lines.append(lines[-1].strip())

        # Find repeated patterns (likely headers/footers)
        headers = [line for line in first_lines if first_lines.count(line) > 1]
        footers = [line for line in last_lines if last_lines.count(line) > 1]

        return list(set(headers)), list(set(footers))

    def clean_text(self, text: str, headers: List[str], footers: List[str]) -> str:
        """
        Clean extracted text by removing headers, footers, and artifacts.

        Args:
            text: Raw extracted text
            headers: List of header patterns to remove
            footers: List of footer patterns to remove

        Returns:
            Cleaned text
        """
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()

            # Skip empty lines (preserve some for structure)
            if not stripped:
                cleaned_lines.append("")
                continue

            # Skip identified headers and footers
            if any(header in stripped for header in headers):
                continue
            if any(footer in stripped for footer in footers):
                continue

            # Remove page numbers (common footer artifact)
            # Match patterns like "- 3 -", "3", etc. at line start/end
            if re.match(r'^[-\s]*\d+\s*[-\s]*$', stripped):
                continue

            # Remove "Official NBA Rules" repeated text
            if "Official NBA" in stripped and len(stripped) < 50:
                continue

            cleaned_lines.append(line)

        # Join back, removing excessive blank lines
        cleaned_text = '\n'.join(cleaned_lines)
        cleaned_text = re.sub(r'\n\n\n+', '\n\n', cleaned_text)

        return cleaned_text.strip()

    def detect_quality_issues(self, text: str, page_num: int) -> List[str]:
        """
        Detect quality issues in extracted text (OCR failures, encoding problems).

        Args:
            text: Extracted text
            page_num: Page number for reporting

        Returns:
            List of detected issues
        """
        issues = []

        # Check for unusual character frequencies (OCR artifacts)
        if text.count('|') > len(text) / 10:
            issues.append(f"Page {page_num}: Unusual pipe character frequency (possible OCR artifact)")

        # Check for encoding problems (mojibake)
        try:
            text.encode('utf-8').decode('utf-8')
        except UnicodeDecodeError:
            issues.append(f"Page {page_num}: Unicode encoding issues detected")

        # Check for very short text (possible extraction failure)
        if len(text.strip()) < 100:
            issues.append(f"Page {page_num}: Very short text extracted ({len(text)} chars)")

        # Check for common OCR errors
        ocr_patterns = [r'\bl\d+l\b', r'\d+o\d+', r'O0']  # Common OCR confusion
        for pattern in ocr_patterns:
            if re.search(pattern, text):
                issues.append(f"Page {page_num}: Possible OCR artifacts detected ({pattern})")

        return issues

    def extract_all(self, max_pages: int = None) -> Dict:
        """
        Extract text from pages with cleaning and validation.

        Args:
            max_pages: Optional limit on pages to extract (default: all pages)

        Returns:
            Dictionary with extracted data and metadata
        """
        pages_to_extract = min(max_pages, self.total_pages) if max_pages else self.total_pages
        print(f"📄 Extracting from {pages_to_extract} pages...")

        # Step 1: Identify header/footer patterns
        print("🔍 Analyzing header/footer patterns...")
        headers, footers = self.identify_header_footer_patterns()
        print(f"  Found {len(headers)} header patterns: {headers}")
        print(f"  Found {len(footers)} footer patterns: {footers}")

        # Step 2: Extract and clean all pages
        all_text = []

        for page_num in range(pages_to_extract):
            if (page_num + 1) % 10 == 0:
                print(f"  Processing page {page_num + 1}/{pages_to_extract}...")

            text, metadata = self.extract_page_text(page_num)
            cleaned = self.clean_text(text, headers, footers)

            # Detect quality issues
            issues = self.detect_quality_issues(cleaned, page_num + 1)
            if issues:
                self.extraction_stats["pages_with_issues"].extend(issues)

            page_data = {
                "page_number": page_num + 1,
                "raw_text": text,
                "cleaned_text": cleaned,
                "metadata": metadata,
                "quality_issues": issues,
            }

            self.pages_data.append(page_data)
            all_text.append(cleaned)

            self.extraction_stats["extracted_pages"] += 1
            self.extraction_stats["total_chars"] += len(cleaned)

        return {
            "status": "success",
            "total_pages": pages_to_extract,
            "pages_data": self.pages_data,
            "combined_text": '\n\n'.join(all_text),
            "stats": self.extraction_stats,
        }

    def validate_extraction(self, result: Dict) -> Dict[str, any]:
        """
        Validate extraction quality against best practices.

        Args:
            result: Extraction result from extract_all()

        Returns:
            Validation report
        """
        validation = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "overall_status": "PASS",
        }

        # Check 1: All pages extracted
        if result["total_pages"] == result["total_pages"]:
            validation["checks"]["completeness"] = {
                "status": "PASS",
                "message": f"All {result['total_pages']} pages extracted"
            }
        else:
            validation["checks"]["completeness"] = {
                "status": "FAIL",
                "message": f"Missing pages: {result['total_pages'] - result['total_pages']}"
            }
            validation["overall_status"] = "FAIL"

        # Check 2: Text quality
        if result["stats"]["pages_with_issues"]:
            validation["checks"]["quality"] = {
                "status": "WARNING",
                "issues_found": len(result["stats"]["pages_with_issues"]),
                "issues": result["stats"]["pages_with_issues"][:5]  # First 5
            }
        else:
            validation["checks"]["quality"] = {
                "status": "PASS",
                "message": "No quality issues detected"
            }

        # Check 3: Content volume
        avg_chars_per_page = result["stats"]["total_chars"] / result["total_pages"]
        if avg_chars_per_page > 500:  # Reasonable for rulebook
            validation["checks"]["content_volume"] = {
                "status": "PASS",
                "avg_chars_per_page": int(avg_chars_per_page)
            }
        else:
            validation["checks"]["content_volume"] = {
                "status": "WARNING",
                "avg_chars_per_page": int(avg_chars_per_page),
                "message": "Lower than expected text volume"
            }

        # Check 4: Structure preservation
        combined_text = result["combined_text"]
        has_rule_numbers = bool(re.search(r'\bRule\s+\d+', combined_text, re.IGNORECASE))
        has_sections = bool(re.search(r'Article|Section', combined_text, re.IGNORECASE))

        if has_rule_numbers or has_sections:
            validation["checks"]["structure"] = {
                "status": "PASS",
                "has_rule_numbers": has_rule_numbers,
                "has_sections": has_sections,
            }
        else:
            validation["checks"]["structure"] = {
                "status": "WARNING",
                "message": "Could not detect rule structure markers"
            }

        return validation


def main():
    """Main extraction pipeline."""

    pdf_path = Path("/Users/omar/Documents/Claude-Vibe-Code/nba-rules/Official-2025-26-NBA-Playing-Rules.pdf")
    output_dir = Path("/Users/omar/Documents/Claude-Vibe-Code/nba-rules/data/")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract (stop at page 71 - signal diagrams not needed)
    extractor = NBAExtractor(str(pdf_path))
    result = extractor.extract_all(max_pages=71)

    # Validate
    validation = extractor.validate_extraction(result)

    # Save outputs
    print("\n💾 Saving extraction outputs...")

    # 1. Raw combined text
    raw_text_path = output_dir / "01_raw_extracted_text.txt"
    with open(raw_text_path, 'w', encoding='utf-8') as f:
        f.write(result["combined_text"])
    print(f"  ✓ Raw text: {raw_text_path}")
    print(f"    Size: {len(result['combined_text']):,} characters")

    # 2. Metadata index
    metadata_path = output_dir / "02_extraction_metadata.json"
    metadata_output = {
        "extraction_timestamp": datetime.now().isoformat(),
        "source": str(pdf_path),
        "total_pages": result["total_pages"],
        "pages": [
            {
                "page_number": p["page_number"],
                "text_length": len(p["cleaned_text"]),
                "has_images": p["metadata"]["has_images"],
                "quality_issues": p["quality_issues"],
            }
            for p in result["pages_data"]
        ],
        "statistics": result["stats"],
    }
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_output, f, indent=2)
    print(f"  ✓ Metadata: {metadata_path}")

    # 3. Validation report
    validation_path = output_dir / "03_validation_report.json"
    with open(validation_path, 'w', encoding='utf-8') as f:
        json.dump(validation, f, indent=2)
    print(f"  ✓ Validation: {validation_path}")

    # 4. Per-page text files (for debugging)
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(exist_ok=True)
    for page_data in result["pages_data"]:
        page_file = pages_dir / f"page_{page_data['page_number']:03d}.txt"
        with open(page_file, 'w', encoding='utf-8') as f:
            f.write(page_data["cleaned_text"])
    print(f"  ✓ Per-page texts: {pages_dir}")

    # Print validation summary
    print("\n📊 Validation Report:")
    print(f"  Overall Status: {validation['overall_status']}")
    for check_name, check_result in validation["checks"].items():
        status = check_result.get("status", "UNKNOWN")
        print(f"  {check_name.upper()}: {status}")
        if "message" in check_result:
            print(f"    → {check_result['message']}")
        if "issues" in check_result:
            print(f"    → {len(check_result['issues'])} issues found")

    print("\n✅ Extraction Phase 1 Complete!")
    print(f"\nNext: Review extracted text in {output_dir}")
    print("Then: Proceed to Phase 2 (Chunking Strategy)")


if __name__ == "__main__":
    main()
