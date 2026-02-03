# src/engine/plan_generator.py

from __future__ import annotations

from typing import List

from rule_engine import GeneRuleAdvice
from models import (
    NutritionItem,
    FitnessItem,
    SupplementItem,
    LifestyleItem,
    ComprehensiveHealthPlan,
)


class PlanGenerator:
    """
    Takes rule-based gene advice and aggregates it into a structured health plan:
    nutrition, fitness, supplements, lifestyle.
    """

    def __init__(self) -> None:
        # Later you can inject food DB, exercise DB, etc. For now, it's simple.
        pass

    def generate_plan(self, advice_list: List[GeneRuleAdvice]) -> ComprehensiveHealthPlan:
        """
        Convert a list of GeneRuleAdvice into a ComprehensiveHealthPlan.
        """
        nutrition_items: List[NutritionItem] = []
        fitness_items: List[FitnessItem] = []
        supplement_items: List[SupplementItem] = []
        lifestyle_items: List[LifestyleItem] = []

        for advice in advice_list:
            gene_label = advice.gene

            # Nutrition (from foods + action/risk)
            if advice.foods:
                nutrition_items.append(
                    NutritionItem(
                        title=f"{gene_label}: {advice.category}",
                        description=advice.explanation or advice.action,
                        foods_to_focus=advice.foods,
                        foods_to_limit=[],
                        related_genes=[gene_label],
                        priority=advice.priority,
                    )
                )

            # Supplements
            if advice.supplements:
                for supp in advice.supplements:
                    name = supp.get("name") if isinstance(supp, dict) else str(supp)
                    note = supp.get("note") if isinstance(supp, dict) else ""
                    supplement_items.append(
                        SupplementItem(
                            name=name,
                            description=note or f"Suggested for {gene_label} ({advice.risk}).",
                            typical_dosage=None,
                            timing=None,
                            related_genes=[gene_label],
                            priority=advice.priority,
                        )
                    )

            # Fitness
            if advice.fitness_notes:
                fitness_items.append(
                    FitnessItem(
                        title=f"{gene_label}-driven training focus",
                        description=advice.fitness_notes,
                        focus=[],
                        frequency_per_week=None,
                        related_genes=[gene_label],
                        priority=advice.priority,
                    )
                )

            # Lifestyle
            if advice.lifestyle:
                lifestyle_items.append(
                    LifestyleItem(
                        title=f"{gene_label}: lifestyle focus",
                        description=advice.explanation or advice.action,
                        habits=advice.lifestyle,
                        related_genes=[gene_label],
                        priority=advice.priority,
                    )
                )

        # Optional: sort each section by priority (highest first)
        nutrition_items.sort(key=lambda x: x.priority, reverse=True)
        fitness_items.sort(key=lambda x: x.priority, reverse=True)
        supplement_items.sort(key=lambda x: x.priority, reverse=True)
        lifestyle_items.sort(key=lambda x: x.priority, reverse=True)

        return ComprehensiveHealthPlan(
            nutrition=nutrition_items,
            fitness=fitness_items,
            supplements=supplement_items,
            lifestyle=lifestyle_items,
            summary=None,
        )