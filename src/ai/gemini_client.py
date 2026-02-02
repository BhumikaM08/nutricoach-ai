import json
import os
from pathlib import Path

from google import genai  # pip install google-genai
from google.genai import types


class NutriCoachGeminiClient:
    def __init__(self, api_key: str | None = None, model_name: str = "gemini-2.5-flash"):
        # API key is picked up from env by default, but allow override.
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required (set GEMINI_API_KEY env var).")

        # v1 client (default as per current docs)
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name

    def load_report(self, json_path: str = "nutricoach_report.json") -> dict:
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON report not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _format_gene_summary(self, report: dict) -> str:
        lines = []
        for g in report.get("genes", []):
            name = g.get("name")
            trait = g.get("trait")
            result = g.get("result")
            if not name:
                continue
            line = f"{name}: trait = {trait}, result = {result}"
            lines.append(line)
        return "\n".join(lines)

    def get_nutrition_plan(self, report_json_path: str = "nutricoach_report.json") -> str:
        report = self.load_report(report_json_path)
        genes_text = self._format_gene_summary(report)

        system_prompt = (
            "You are a nutrigenomics-focused nutrition coach. "
            "You receive a list of gene-trait-risk summaries for one person. "
            "Based ONLY on these genes, explain key tendencies and give practical diet and lifestyle guidance. "
            "Avoid medical claims and do not mention specific diseases; talk in terms of tendencies and support."
        )

        user_prompt = (
            "Here is this person's genetics summary (gene: trait, result):\n\n"
            f"{genes_text}\n\n"
            "1) Briefly summarize their main nutrition-related tendencies.\n"
            "2) Give 6–10 clear, practical diet recommendations (foods to increase, foods to limit, habits).\n"
            "3) Where relevant, connect recommendations back to specific traits "
            "(e.g., Vitamin A Requirement, Caffeine Metabolism, Alcohol Sensitivity).\n"
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_text(text=system_prompt),
                types.Part.from_text(text=user_prompt),
            ],
            # Optional: make output deterministic-ish
            config=types.GenerateContentConfig(
                temperature=0.7,
            ),
        )

        return response.text


def main():
    client = NutriCoachGeminiClient()
    plan = client.get_nutrition_plan("nutricoach_report.json")

    print("\n=== NUTRICOACH GEMINI PLAN ===\n")
    print(plan)


if __name__ == "__main__":
    main()