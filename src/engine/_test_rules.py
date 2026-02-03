import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from extraction.pdf_extractor import PDFExtractor
from rule_engine import RuleEngine
from plan_generator import PlanGenerator
from models import ComprehensiveHealthPlan

def main():
    extractor = PDFExtractor("../../data/sample_reports/sample_report.pdf")
    extractor.load_pdf_text()
    genes = extractor.get_priority_genes_with_summary()

    engine = RuleEngine("../../data/rules.yml")  # ← fixed path
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

    # Test full chain: rules → plan
    print("\n=== FULL PLAN TEST ===")
    generator = PlanGenerator()
    plan = generator.generate_plan(advice_list)

    print(f"Nutrition items: {len(plan.nutrition)}")
    print(f"Fitness items: {len(plan.fitness)}")
    print(f"Supplements: {len(plan.supplements)}")
    print(f"Lifestyle: {len(plan.lifestyle)}")

    if plan.nutrition:
        print(f"Top nutrition: {plan.nutrition[0].title}")

if __name__ == "__main__":
    main()