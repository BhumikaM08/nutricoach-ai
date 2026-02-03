#!/usr/bin/env python3
"""
NutriCoach AI - PRODUCTION READY
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.pdf_extractor import PDFExtractor
from src.engine.rule_engine import RuleEngine
from src.engine.plan_generator import PlanGenerator
from src.engine.models import ComprehensiveHealthPlan

def plan_to_dict(plan):
    """Convert plan with nested objects to JSON-serializable dict"""
    return {
        'nutrition': [item.dict() if hasattr(item, 'dict') else vars(item) for item in plan.nutrition],
        'fitness': [item.dict() if hasattr(item, 'dict') else vars(item) for item in plan.fitness],
        'supplements': [item.dict() if hasattr(item, 'dict') else vars(item) for item in plan.supplements],
        'lifestyle': [item.dict() if hasattr(item, 'dict') else vars(item) for item in plan.lifestyle]
    }

def main():
    parser = argparse.ArgumentParser(description="NutriCoach PDF→JSON")
    parser.add_argument("pdf_path")
    parser.add_argument("-o", "--output", default="nutricoach_plan.json")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--meals", action="store_true", help="Generate meal plan")
    parser.add_argument("--explain", action="store_true", help="Generate AI report")
    args = parser.parse_args()

    pdf_file = Path(args.pdf_path)
    if not pdf_file.exists():
        print(f"❌ {pdf_file} not found")
        sys.exit(1)

    print("1️⃣ Extracting genes...")
    extractor = PDFExtractor(str(pdf_file))
    extractor.load_pdf_text()
    genes = extractor.get_priority_genes_with_summary()
    print(f"   {len(genes)} genes found")

    print("2️⃣ Rule engine...")
    engine = RuleEngine("data/rules.yml")
    advice_list = engine.apply_rules(genes)
    print(f"   {len(advice_list)} rules matched")

    print("3️⃣ Generating plan...")
    generator = PlanGenerator()
    plan = generator.generate_plan(advice_list)

    print("\n📊 SUMMARY:")
    print(f"Nutrition: {len(plan.nutrition)}")
    print(f"Fitness: {len(plan.fitness)}")
    print(f"Supplements: {len(plan.supplements)}")
    print(f"Lifestyle: {len(plan.lifestyle)}")

    # Save JSON
    plan_dict = plan_to_dict(plan)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(plan_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ SUCCESS: {args.output} created!")

    # MEALS - inside main() function
    if args.meals:
        from src.planning.meal_generator import MealGenerator
        meal_gen = MealGenerator()
        menu = meal_gen.generate_daily_plan(plan_dict)
        
        with open("nutricoach_menu.md", "w", encoding="utf-8") as f:
            f.write("# 🧬 Your DNA-Optimized Meal Plan\n\n")
            for meal_time, foods in menu.items():
                f.write(f"## {meal_time.title()}\n\n")
                for food in foods:
                    f.write(f"- {food}\n")
                f.write("\n")
        
        print("🍽️  Meal plan: nutricoach_menu.md")

    # GEMINI EXPLAIN - inside main() function
    if args.explain:
        try:
            from src.ai.gemini_client import generate_report
            report = generate_report(plan_dict)
            with open("nutricoach_report.md", "w", encoding="utf-8") as f:
                f.write(report)
            print("🤖 AI Report: nutricoach_report.md")
        except Exception as e:
            print(f"⚠️  Gemini report failed: {e}")

if __name__ == "__main__":
    main()