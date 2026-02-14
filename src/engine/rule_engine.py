from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from extraction.pdf_extractor import GeneData
from .models import GeneRuleAdvice


class GeneRuleAdvice:
    """
    Structured rule-based recommendation for a single gene + risk level.
    """

    def __init__(
        self,
        gene: str,
        category: str,
        risk: str,
        action: str,
        foods: List[str],
        supplements: List[Dict[str, str]],
        fitness_notes: Optional[str],
        lifestyle: List[str],
        explanation: str,
        priority: int,
    ):
        self.gene = gene
        self.category = category
        self.risk = risk
        self.action = action
        self.foods = foods
        self.supplements = supplements
        self.fitness_notes = fitness_notes
        self.lifestyle = lifestyle
        self.explanation = explanation
        self.priority = priority

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gene": self.gene,
            "category": self.category,
            "risk": self.risk,
            "action": self.action,
            "foods": self.foods,
            "supplements": self.supplements,
            "fitness_notes": self.fitness_notes,
            "lifestyle": self.lifestyle,
            "explanation": self.explanation,
            "priority": self.priority,
        }


class RuleEngine:
    """
    Loads rules.yml and applies them to extracted genes.
    """

    def __init__(self, rules_path: str = "data/rules.yml"):
        self.rules_path = Path(rules_path)
        if not self.rules_path.exists():
            raise FileNotFoundError(f"Rules file not found: {self.rules_path}")

        with self.rules_path.open("r", encoding="utf-8") as f:
            self.rules_data: Dict[str, Any] = yaml.safe_load(f) or {}

    def _normalize_risk(self, result: Optional[str]) -> Optional[str]:
        """
        Map extracted result strings to keys used in YAML (e.g. 'High risk' -> 'High Risk').
        """
        if not result:
            return None

        r = result.strip().lower()
        if "high risk" in r:
            return "High Risk"
        if "typical" in r:
            return "Typical"
        if "enhanced" in r:
            return "Enhanced"
        if "risk" == r:
            return "Risk"
        return None  # unknown / not mapped
    
    def apply_rules(self, genes: List[GeneData | dict]) -> List[GeneRuleAdvice]:
        """
        For each GeneData OR dict, look up matching rule in rules.yml (if any)
        and return a list of GeneRuleAdvice objects.
        """
        advice_list: List[GeneRuleAdvice] = []

        for g in genes:
            # Handle both GeneData objects and dicts
            if isinstance(g, dict):
                gene_name = g["gene"].upper()
                risk_level = g["risk"]
            else:
                gene_name = g.name.upper()
                risk_level = g.result

            rule_entry = self.rules_data.get(gene_name)
            if not rule_entry:
                continue  # no rules for this gene yet

            risk_key = self._normalize_risk(risk_level)
            if not risk_key:
                continue  # cannot match YAML mapping

            mappings = rule_entry.get("mappings", {})
            mapping = mappings.get(risk_key)
            if not mapping:
                continue  # no mapping for this specific risk level

            category = rule_entry.get("category", "Unknown")
            action = mapping.get("action", "")
            foods = mapping.get("foods", []) or []
            supplements = mapping.get("supplements", []) or []
            fitness_notes = mapping.get("fitness_notes")
            lifestyle = mapping.get("lifestyle", []) or []
            explanation = mapping.get("explanation", "")
            priority = int(mapping.get("priority", 0))

            advice_list.append(
                GeneRuleAdvice(
                    gene=gene_name,
                    category=category,
                    risk=risk_key,
                    action=action,
                    foods=foods,
                    supplements=supplements,
                    fitness_notes=fitness_notes,
                    lifestyle=lifestyle,
                    explanation=explanation,
                    priority=priority,
                )
            )

        # Sort by priority (highest first)
        advice_list.sort(key=lambda a: a.priority, reverse=True)
        return advice_list