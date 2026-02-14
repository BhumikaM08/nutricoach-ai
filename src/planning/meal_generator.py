from pathlib import Path
import yaml

class MealGenerator:
    def __init__(self, meals_path: str = "data/meals.yml"):
        path = Path(meals_path)
        if not path.exists():
            raise FileNotFoundError(f"Meals file not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            self.meals = yaml.safe_load(f) or {}

    def _extract_genes_from_plan(self, plan_dict: dict) -> list:
        """Collect all gene names mentioned in the nutrition plan."""
        genes = set()

        if not plan_dict or "nutrition" not in plan_dict:
            return []

        for item in plan_dict["nutrition"]:
            # item is dict from plan_to_dict()
            if isinstance(item, dict):
                if "gene" in item and item["gene"]:
                    genes.add(str(item["gene"]).upper())
                if "related_genes" in item and item["related_genes"]:
                    for g in item["related_genes"]:
                        genes.add(str(g).upper())
        return list(genes)

    def generate_daily_plan(self, plan_dict: dict) -> dict:
        """
        Generate a daily menu:
        breakfast / lunch / dinner / snacks
        based on genes present in the nutrition plan.
        """
        menu = {
            "breakfast": [],
            "lunch": [],
            "dinner": [],
            "snacks": [],
        }

        genes_found = self._extract_genes_from_plan(plan_dict)

        for gene in genes_found:
            if gene not in self.meals:
                continue

            gene_meals = self.meals[gene]

            # gene_meals example for BCMO1:
            # { "vitamin_a": { "breakfast": [...], "lunch": [...], "dinner": [...] } }
            for _, meal_times in gene_meals.items():
                for meal_time, foods in meal_times.items():
                    if not foods:
                        continue

                    if meal_time == "all_meals":
                        # apply to all 4 slots
                        for key in menu.keys():
                            menu[key].extend(foods)
                    elif meal_time in menu:
                        menu[meal_time].extend(foods)
                    # e.g. ACTN3 "post_workout" is ignored for now,
                    # you can later add a separate Post‑workout section.

        # If still empty, add generic fallback
        if not any(menu.values()):
            menu["breakfast"] = ["Balanced breakfast with protein, whole grains, and fruit"]
            menu["lunch"] = ["Lean protein with vegetables and complex carbs"]
            menu["dinner"] = ["Light dinner, avoid heavy late-night meals"]
            menu["snacks"] = ["Nuts, fruits, or yogurt"]

        # Remove duplicates while preserving order
        for key in menu:
            seen = set()
            unique = []
            for food in menu[key]:
                if food not in seen:
                    unique.append(food)
                    seen.add(food)
            menu[key] = unique

        return menu