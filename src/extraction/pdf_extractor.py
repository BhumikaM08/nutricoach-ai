import pdfplumber
import re
from pathlib import Path
from typing import List, Dict, Optional


class GeneData:
    """Container for one gene's info (Day 2 version)."""

    def __init__(self, name: str, page: int, context: str):
        self.name = name
        self.page = page  # 1-based index
        self.context = context  # small text snippet around gene

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "page": self.page,
            "context": self.context,
        }


class PDFExtractor:
    """
    Extract basic gene occurrences from the NutriDNA PDF.

    Day 2 goals:
    - Load PDF
    - Find priority gene names
    - Capture context snippets
    """

    PRIORITY_GENES = ["BCMO1", "MCM6", "FTO", "ADRB2", "ACTN3", "CYP1A2", "IL6", "ALDH2", "TCF7L2", "BDNF"]

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        self._pages_text: List[str] = []

    def load_pdf_text(self) -> None:
        """Load text from all pages."""
        self._pages_text = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                self._pages_text.append(text)

        if not self._pages_text:
            raise ValueError("No text extracted from PDF. Check the file.")

    def find_gene(self, gene_name: str) -> Optional[GeneData]:
        """Return first occurrence of a gene with context."""
        if not self._pages_text:
            self.load_pdf_text()

        pattern = re.compile(rf"\b{re.escape(gene_name)}\b", re.IGNORECASE)

        for page_idx, text in enumerate(self._pages_text):
            match = pattern.search(text)
            if not match:
                continue

            start = max(match.start() - 250, 0)
            end = min(match.end() + 250, len(text))
            snippet = text[start:end].replace("\n", " ")

            return GeneData(name=gene_name, page=page_idx + 1, context=snippet)

        return None

    def find_priority_genes(self) -> List[GeneData]:
        """Find all priority genes."""
        if not self._pages_text:
            self.load_pdf_text()

        results: List[GeneData] = []
        for gene in self.PRIORITY_GENES:
            data = self.find_gene(gene)
            if data:
                results.append(data)
        return results

    def to_dict(self) -> Dict:
        genes = [g.to_dict() for g in self.find_priority_genes()]
        return {
            "pdf_path": str(self.pdf_path),
            "total_pages": len(self._pages_text),
            "found_genes_count": len(genes),
            "genes": genes,
        }


def main():
    pdf_path = "data/sample_reports/sample_report.pdf"
    extractor = PDFExtractor(pdf_path)
    extractor.load_pdf_text()
    result = extractor.to_dict()

    print("\n=== PDF SUMMARY ===")
    print(f"PDF: {result['pdf_path']}")
    print(f"Pages: {result['total_pages']}")
    print(f"Priority genes found: {result['found_genes_count']}\n")

    for g in result["genes"]:
        print(f"Gene: {g['name']} (page {g['page']})")
        print(f"Context: {g['context'][:220]}...")
        print("-" * 80)


if __name__ == "__main__":
    main()