# src/engine/models.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional


RiskLevel = Literal["High Risk", "Moderate Risk", "Typical", "Enhanced"]
Category = Literal["nutrition", "fitness", "supplement", "lifestyle"]


@dataclass
class GeneResult:
    """
    Output from the PDF extractor step.
    Example: BCMO1 / High Risk, MCM6 / High Risk, ACTN3 / Enhanced.
    """
    gene: str
    trait: Optional[str] = None
    result: RiskLevel | str = "Typical"  # allow free text for now
    raw_text: Optional[str] = None


@dataclass
class GeneRuleAdvice:
    """
    One rule-based recommendation from the rule engine for a single gene.
    This matches what rule_engine.apply_rules returns.
    """
    gene: str
    risk_level: RiskLevel | str
    priority: int

    # Core recommendation
    title: str
    action_code: str  # e.g., "increase_preformed_vitamin_A", "avoid_or_limit_lactose"
    summary: str

    # Detailed guidance
    foods: List[str] = field(default_factory=list)
    supplements: List[str] = field(default_factory=list)
    fitness: List[str] = field(default_factory=list)
    lifestyle: List[str] = field(default_factory=list)

    # Optional AI explanation (filled by LLM layer later)
    explanation: Optional[str] = None

    # Optional category tags (nutrition, fitness, supplement, lifestyle)
    categories: List[Category] = field(default_factory=list)


# --------- Plan item models --------- #

@dataclass
class NutritionItem:
    """
    One concrete nutrition recommendation (can aggregate multiple genes).
    """
    title: str  # e.g., "Vitamin A from animal sources"
    description: str  # human-readable explanation
    foods_to_focus: List[str] = field(default_factory=list)
    foods_to_limit: List[str] = field(default_factory=list)
    related_genes: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10, higher = more important


@dataclass
class FitnessItem:
    """
    One concrete fitness recommendation.
    """
    title: str  # e.g., "Emphasize power training"
    description: str
    focus: List[str] = field(default_factory=list)  # e.g., ["resistance training", "sprints", "plyometrics"]
    frequency_per_week: Optional[int] = None
    related_genes: List[str] = field(default_factory=list)
    priority: int = 5


@dataclass
class SupplementItem:
    """
    One supplement recommendation (merged across genes if needed).
    """
    name: str  # e.g., "Vitamin A (retinol)"
    description: str
    typical_dosage: Optional[str] = None  # plain text, we won't hard-code doses now
    timing: Optional[str] = None  # e.g., "with meals", "before workout"
    related_genes: List[str] = field(default_factory=list)
    priority: int = 5


@dataclass
class LifestyleItem:
    """
    One lifestyle or habit recommendation.
    """
    title: str  # e.g., "Caffeine timing for better sleep"
    description: str
    habits: List[str] = field(default_factory=list)
    related_genes: List[str] = field(default_factory=list)
    priority: int = 5


# --------- Complete plan model --------- #

@dataclass
class ComprehensiveHealthPlan:
    """
    Aggregated output that planners will produce and the API/UI will consume.
    This becomes the core response object for each user.
    """
    nutrition: List[NutritionItem] = field(default_factory=list)
    fitness: List[FitnessItem] = field(default_factory=list)
    supplements: List[SupplementItem] = field(default_factory=list)
    lifestyle: List[LifestyleItem] = field(default_factory=list)

    # Optional high-level summary (can be added by LLM later)
    summary: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Helper for FastAPI/JSON responses.
        """
        from dataclasses import asdict

        return asdict(self)