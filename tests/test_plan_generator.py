# tests/test_plan_generator.py

from pathlib import Path

from src.engine.rule_engine import RuleEngine
from src.engine.plan_generator import PlanGenerator


def test_plan_generator_creates_sections():
    # Use the real rules.yml and rule engine
    rules_path = Path("data/rules.yml")
    engine = RuleEngine(rules_path)

    genes = [
        {"gene": "BCMO1", "risk": "High Risk"},
        {"gene": "ACTN3", "risk": "Enhanced"},
    ]

    advice_list = engine.apply_rules(genes)
    assert len(advice_list) >= 1  # sanity check

    generator = PlanGenerator()
    plan = generator.generate_plan(advice_list)

    # At least some nutrition or supplement guidance should exist
    assert plan is not None
    assert len(plan.nutrition) >= 1 or len(plan.supplements) >= 1