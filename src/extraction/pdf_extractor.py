import pdfplumber
import re
from pathlib import Path
from typing import List, Dict, Optional


class GeneData:
    """Container for one gene's info (Day 3 version)."""

    def __init__(
        self,
        name: str,
        page: int,
        context: str,
        trait: Optional[str] = None,
        result: Optional[str] = None,
    ):
        self.name = name
        self.page = page  # 1-based index
        self.context = context  # small text snippet around gene
        self.trait = trait
        self.result = result

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "page": self.page,
            "context": self.context,
            "trait": self.trait,
            "result": self.result,
        }


class PDFExtractor:
    """
    Extract genetic information from the NutriDNA PDF.

    - Day 2: find genes + context
    - Day 3: parse Summary of Results tables (trait, gene, result)
    """

    PRIORITY_GENES = [
        "BCMO1",
        "MCM6",
        "FTO",
        "ADRB2",
        "ACTN3",
        "CYP1A2",
        "IL6",
        "ALDH2",
        "TCF7L2",
        "BDNF",
    ]

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        self._pages_text: List[str] = []
        self._summary_rows: List[Dict] = []

    # ---------- text loading ----------

    def load_pdf_text(self) -> None:
        """Load text from all pages."""
        self._pages_text = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                self._pages_text.append(text)

        if not self._pages_text:
            raise ValueError("No text extracted from PDF. Check the file.")

    # ---------- Day 2: gene + context ----------

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
        for gene in self.PRIMARY_GENES:
            data = self.find_gene(gene)
            if data:
                results.append(data)
        return results

    # ---------- Day 3: Summary table parsing ----------

    def parse_summary_tables(self) -> List[Dict]:
        """
        Parse 'Summary of Results' tables (pages 2–5) into
        rows of {trait, gene, result}.
        """
        rows: List[Dict] = []

        with pdfplumber.open(self.pdf_path) as pdf:
            # In the abridged report, summary tables are on pages 2–5 (1-based).
            summary_page_indexes = [1, 2, 3, 4]  # zero-based: 1–4

            for idx in summary_page_indexes:
                if idx >= len(pdf.pages):
                    continue
                page = pdf.pages[idx]

                # Extract the largest table on the page. [web:60][web:63]
                table = page.extract_table()
                if not table:
                    continue

                # First row is the header: ["Trait", "Genes", "Result"]
                header = [h.strip() if h else "" for h in table[0]]
                body = table[1:]

                # Find indices for important columns, defensively.
                try:
                    trait_col = header.index("Trait")
                    genes_col = header.index("Genes")
                    result_col = header.index("Result")
                except ValueError:
                    # Unexpected header – skip this page
                    continue

                for raw_row in body:
                    if not raw_row:
                        continue
                    # Normalize row to same length as header
                    row = list(raw_row) + [""] * (len(header) - len(raw_row))

                    trait = (row[trait_col] or "").strip()
                    genes = (row[genes_col] or "").strip()
                    result = (row[result_col] or "").strip()

                    if not trait or not genes or not result:
                        continue

                    # Some rows have multiple genes separated by commas
                    gene_list = [g.strip() for g in genes.split(",") if g.strip()]

                    for gene in gene_list:
                        rows.append(
                            {
                                "trait": trait,
                                "gene": gene,
                                "result": result,
                                "page": idx + 1,  # 1-based
                            }
                        )

        self._summary_rows = rows
        # DEBUG: print how many summary rows we got
        #print(f"[DEBUG] Parsed {len(rows)} summary rows from tables")
        return rows

    def get_gene_summary(self, gene_name: str) -> Optional[Dict]:
        """Return first summary-row dict for a given gene."""
        if not self._summary_rows:
            self.parse_summary_tables()

        for row in self._summary_rows:
            if row["gene"].upper() == gene_name.upper():
                return row
        return None

    # ---------- combined view ----------

    def get_priority_genes_with_summary(self) -> List[GeneData]:
        """
        Combine:
        - location + context (Day 2)
        - trait + result from summary table (Day 3)
        """
        if not self._pages_text:
            self.load_pdf_text()
        if not self._summary_rows:
            self.parse_summary_tables()

        genes: List[GeneData] = []

        for gene_name in self.PRIORITY_GENES:
            base = self.find_gene(gene_name)
            summary = self.get_gene_summary(gene_name)

            if not base and not summary:
                continue

            trait = summary["trait"] if summary else None
            result = summary["result"] if summary else None

            if base:
                base.trait = trait
                base.result = result
                genes.append(base)
            else:
                # Fallback if we only have summary-row
                genes.append(
                    GeneData(
                        name=gene_name,
                        page=summary["page"],
                        context="(no context – found only in summary table)",
                        trait=trait,
                        result=result,
                    )
                )

        return genes

    def to_dict(self) -> Dict:
        genes = [g.to_dict() for g in self.get_priority_genes_with_summary()]
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
    extractor.parse_summary_tables()
    result = extractor.to_dict()

    print("\n=== PDF SUMMARY + TABLE PARSE ===")
    print(f"PDF: {result['pdf_path']}")
    print(f"Pages: {result['total_pages']}")
    print(f"Priority genes found: {result['found_genes_count']}\n")

    for g in result["genes"]:
        print(f"Gene: {g['name']} (page {g['page']})")
        print(f"Trait: {g['trait']}")
        print(f"Result: {g['result']}")
        print(f"Context: {g['context'][:220]}...")
        print("-" * 80)


if __name__ == "__main__":
    main()