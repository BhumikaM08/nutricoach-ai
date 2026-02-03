# tests/test_rule_engine.py

from src.engine.rule_engine import RuleEngine
from pathlib import Path

def test_rules_file_loads():
    rules_path = Path("data/rules.yml")
    engine = RuleEngine(rules_path)
    
    # Test loads without error
    assert engine is not None
    
    # Test apply_rules works with sample genes
    genes = [
        {"gene": "BCMO1", "risk": "High Risk"},
        {"gene": "MCM6", "risk": "High Risk"}
    ]
    advice = engine.apply_rules(genes)
    
    assert len(advice) >= 2
    assert any(item.gene == "BCMO1" for item in advice)