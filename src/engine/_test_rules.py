from src.extraction.pdf_extractor import PDFExtractor
from src.engine.rule_engine import RuleEngine

def main():
    extractor = PDFExtractor("data/sample_reports/sample_report.pdf")
    extractor.load_pdf_text()
    genes = extractor.get_priority_genes_with_summary()

    engine = RuleEngine("data/rules.yml")
    advice_list = engine.apply_rules(genes)

    print(f"Got {len(advice_list)} rule-based recommendations:\n")
    for a in advice_list:
        d = a.to_dict()
        print(
            f"{d['gene']} ({d['risk']}, priority {d['priority']}): "
            f"{d['category']} → {d['action']}"
        )
        print(f"  Foods: {', '.join(d['foods'])}")
        if d["supplements"]:
            print(f"  Supplements: {[s['name'] for s in d['supplements']]}")
        if d["fitness_notes"]:
            print(f"  Fitness: {d['fitness_notes']}")
        print()

if __name__ == "__main__":
    main()