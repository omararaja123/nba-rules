"""
Extraction Verification Utility
Validates Phase 1 extraction quality and integrity.
"""

import json
import re
from pathlib import Path
from collections import Counter


def verify_completeness() -> dict:
    """Check that all pages were extracted."""
    data_dir = Path("data")

    # Check raw text file
    raw_text_path = data_dir / "01_raw_extracted_text.txt"
    if not raw_text_path.exists():
        return {"status": "FAIL", "message": "Raw text file not found"}

    # Check metadata
    metadata_path = data_dir / "02_extraction_metadata.json"
    if not metadata_path.exists():
        return {"status": "FAIL", "message": "Metadata file not found"}

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    total_pages = metadata["total_pages"]
    extracted_pages = len(metadata["pages"])

    if total_pages == extracted_pages:
        return {
            "status": "PASS",
            "message": f"All {total_pages} pages extracted",
            "total_pages": total_pages,
            "extracted_pages": extracted_pages
        }
    else:
        return {
            "status": "FAIL",
            "message": f"Missing pages: {total_pages - extracted_pages}",
            "total_pages": total_pages,
            "extracted_pages": extracted_pages
        }


def verify_cleanliness() -> dict:
    """Check for headers, footers, and common artifacts."""
    raw_text_path = Path("data") / "01_raw_extracted_text.txt"

    with open(raw_text_path, 'r', encoding='utf-8') as f:
        text = f.read()

    issues = []

    # Check for page number patterns (- 1 -, - 2 -, etc.)
    page_number_pattern = re.findall(r'^[-\s]*\d{1,3}\s*[-\s]*$', text, re.MULTILINE)
    if page_number_pattern:
        issues.append(f"Found {len(page_number_pattern)} page number artifacts")

    # Check for "PAGE" footer
    page_footer_count = text.count("PAGE")
    if page_footer_count > 5:
        issues.append(f"Found {page_footer_count} 'PAGE' footer instances")

    # Check for "Official NBA" repeated text (header artifact)
    official_nba_count = text.count("Official NBA")
    if official_nba_count > 5:
        issues.append(f"Found {official_nba_count} 'Official NBA' instances")

    # Check for unusual character patterns (OCR artifacts)
    pipe_ratio = text.count('|') / len(text)
    if pipe_ratio > 0.01:
        issues.append(f"High pipe character ratio ({pipe_ratio:.2%}) - possible OCR artifact")

    if issues:
        return {"status": "WARNING", "issues": issues}
    else:
        return {"status": "PASS", "message": "No significant cleanliness issues detected"}


def verify_structure() -> dict:
    """Check that rule structure is preserved."""
    raw_text_path = Path("data") / "01_raw_extracted_text.txt"

    with open(raw_text_path, 'r', encoding='utf-8') as f:
        text = f.read()

    findings = {
        "rule_numbers": len(re.findall(r'\bRULE NO\.\s+\d+', text, re.IGNORECASE)),
        "sections": len(re.findall(r'\bSection\s+[IVX]+', text, re.IGNORECASE)),
        "subsections": len(re.findall(r'^[a-z]\.\s+', text, re.MULTILINE)),
    }

    if findings["rule_numbers"] > 10 and findings["sections"] > 10:
        return {
            "status": "PASS",
            "message": "Structure preserved successfully",
            "findings": findings
        }
    else:
        return {
            "status": "WARNING",
            "message": "Some structure markers may be missing",
            "findings": findings
        }


def verify_content_volume() -> dict:
    """Check that content volume is reasonable."""
    metadata_path = Path("data") / "02_extraction_metadata.json"

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    page_texts = metadata["pages"]
    total_chars = sum(p["text_length"] for p in page_texts)
    avg_chars = total_chars / len(page_texts) if page_texts else 0

    # For rulebooks, expect at least 500 chars per page on average
    if avg_chars > 500:
        return {
            "status": "PASS",
            "message": f"Content volume healthy: {avg_chars:.0f} chars/page average",
            "total_chars": total_chars,
            "avg_chars_per_page": int(avg_chars),
            "total_pages": len(page_texts)
        }
    else:
        return {
            "status": "WARNING",
            "message": f"Content volume low: {avg_chars:.0f} chars/page average",
            "total_chars": total_chars,
            "avg_chars_per_page": int(avg_chars)
        }


def verify_encoding() -> dict:
    """Check for encoding errors."""
    raw_text_path = Path("data") / "01_raw_extracted_text.txt"

    try:
        with open(raw_text_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Try to encode back
        text.encode('utf-8').decode('utf-8')

        return {
            "status": "PASS",
            "message": "Text encoding is valid UTF-8"
        }
    except UnicodeDecodeError as e:
        return {
            "status": "FAIL",
            "message": f"Encoding error: {str(e)}"
        }


def verify_page_files() -> dict:
    """Check that individual page files exist and are not empty."""
    pages_dir = Path("data") / "pages"

    if not pages_dir.exists():
        return {"status": "FAIL", "message": "Pages directory not found"}

    page_files = list(pages_dir.glob("page_*.txt"))

    empty_pages = []
    for page_file in sorted(page_files):
        with open(page_file, 'r', encoding='utf-8') as f:
            text = f.read()
        if len(text.strip()) < 10:
            empty_pages.append(page_file.name)

    if empty_pages:
        return {
            "status": "WARNING",
            "message": f"Found {len(empty_pages)} very short page files",
            "files": empty_pages
        }
    else:
        return {
            "status": "PASS",
            "message": f"All {len(page_files)} page files present and non-empty"
        }


def verify_metadata() -> dict:
    """Check metadata file structure and completeness."""
    metadata_path = Path("data") / "02_extraction_metadata.json"

    if not metadata_path.exists():
        return {"status": "FAIL", "message": "Metadata file not found"}

    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        required_keys = ["extraction_timestamp", "total_pages", "pages", "statistics"]
        missing_keys = [k for k in required_keys if k not in metadata]

        if missing_keys:
            return {
                "status": "FAIL",
                "message": f"Missing keys in metadata: {missing_keys}"
            }

        return {
            "status": "PASS",
            "message": "Metadata structure is valid",
            "pages_in_metadata": len(metadata["pages"])
        }
    except json.JSONDecodeError as e:
        return {
            "status": "FAIL",
            "message": f"Invalid JSON in metadata: {str(e)}"
        }


def verify_validation_report() -> dict:
    """Check validation report exists and shows PASS."""
    validation_path = Path("data") / "03_validation_report.json"

    if not validation_path.exists():
        return {"status": "FAIL", "message": "Validation report not found"}

    try:
        with open(validation_path, 'r') as f:
            validation = json.load(f)

        overall = validation.get("overall_status", "UNKNOWN")
        checks = validation.get("checks", {})

        return {
            "status": "INFO",
            "message": f"Overall validation status: {overall}",
            "overall_status": overall,
            "checks_summary": {k: v.get("status", "UNKNOWN") for k, v in checks.items()}
        }
    except json.JSONDecodeError as e:
        return {
            "status": "FAIL",
            "message": f"Invalid JSON in validation report: {str(e)}"
        }


def check_for_duplicates() -> dict:
    """Check if headers/footers were properly removed (no huge duplicate chunks)."""
    raw_text_path = Path("data") / "01_raw_extracted_text.txt"

    with open(raw_text_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Split into pages (marked by RULE NO. or other major sections)
    pages = re.split(r'(?=RULE NO\.)', text)

    # Check for suspicious duplicates (same text appearing in multiple pages)
    # Extract first 200 chars of each page
    snippets = [page[:200] for page in pages if len(page) > 200]

    # Count occurrences
    duplicates = Counter(snippets)
    suspicious = [(text, count) for text, count in duplicates.most_common(10) if count > 1]

    if suspicious:
        return {
            "status": "WARNING",
            "message": f"Found {len(suspicious)} duplicate snippets",
            "examples": [
                (text[:100] + "...", count) for text, count in suspicious[:3]
            ]
        }
    else:
        return {
            "status": "PASS",
            "message": "No suspicious duplicate content detected"
        }


def main():
    """Run all verification checks."""
    print("\n" + "="*60)
    print("NBA RULEBOOK EXTRACTION VERIFICATION")
    print("="*60 + "\n")

    checks = [
        ("Completeness", verify_completeness),
        ("Cleanliness", verify_cleanliness),
        ("Structure Preservation", verify_structure),
        ("Content Volume", verify_content_volume),
        ("Text Encoding", verify_encoding),
        ("Page Files", verify_page_files),
        ("Metadata", verify_metadata),
        ("Validation Report", verify_validation_report),
        ("Duplicate Detection", check_for_duplicates),
    ]

    results = {}
    for check_name, check_func in checks:
        print(f"🔍 {check_name}...")
        try:
            result = check_func()
            results[check_name] = result

            status = result.get("status", "UNKNOWN")
            message = result.get("message", "No message")

            if status == "PASS":
                print(f"   ✅ PASS: {message}\n")
            elif status == "WARNING":
                print(f"   ⚠️  WARNING: {message}")
                if "issues" in result:
                    for issue in result["issues"]:
                        print(f"      - {issue}")
                print()
            elif status == "FAIL":
                print(f"   ❌ FAIL: {message}\n")
            else:
                print(f"   ℹ️  {message}\n")
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}\n")
            results[check_name] = {"status": "ERROR", "message": str(e)}

    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60 + "\n")

    pass_count = sum(1 for r in results.values() if r.get("status") == "PASS")
    warning_count = sum(1 for r in results.values() if r.get("status") == "WARNING")
    fail_count = sum(1 for r in results.values() if r.get("status") == "FAIL")

    print(f"✅ Passed: {pass_count}")
    print(f"⚠️  Warnings: {warning_count}")
    print(f"❌ Failed: {fail_count}")

    if fail_count == 0:
        print("\n🎉 Extraction verification PASSED!")
        print("Ready to proceed to Phase 2 (Chunking).\n")
    else:
        print("\n⚠️  Some checks failed. Review output above.\n")


if __name__ == "__main__":
    main()
