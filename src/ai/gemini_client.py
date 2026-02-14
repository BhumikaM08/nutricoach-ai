import os
from google import genai  # pip install google-genai
from google.genai import types
from dotenv import load_dotenv

class NutriCoachGeminiClient:
    def __init__(self, api_key: str | None = None, model_name: str = "gemini-2.5-flash"):
        load_dotenv()
        # API key is picked up from env by default, but allow override.
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required (set GEMINI_API_KEY env var in .env).")

        # v1 client (current google-genai style)
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name

    # --- Helpers -------------------------------------------------------------

    def _format_gene_summary(self, report: dict) -> str:
        """Format 'genes' list from report/plan into text."""
        lines = []
        for g in report.get("genes", []):
            name = g.get("name")
            trait = g.get("trait")
            result = g.get("result")
            if not name:
                continue
            line = f"{name}: trait = {trait}, result = {result}"
            lines.append(line)
        return "\n".join(lines) if lines else "No gene summaries available."

    def _format_recommendations(self, plan: dict, key: str) -> str:
        """Format nutrition/fitness/supplements sections from plan_dict."""
        items = plan.get(key, [])
        if not items:
            return f"No {key} recommendations found."

        lines = []
        for item in items:
            if isinstance(item, dict):
                title = item.get("title") or item.get("name") or "Untitled"
                desc = item.get("description", "")
                priority = item.get("priority", "N/A")
                genes = item.get("gene") or item.get("related_genes")
                if isinstance(genes, list):
                    genes = ", ".join(genes)
                lines.append(f"- {title} (Priority {priority}, Genes: {genes})\n  {desc}")
            else:
                lines.append(f"- {item}")
        return "\n".join(lines)

    # --- Public methods used by app.py --------------------------------------

    def generate_report(self, plan_dict: dict) -> str:
        """
        Main entry used by app.py:
        Takes plan_dict from Streamlit session and returns a human-readable report.
        """
        genes_text = self._format_gene_summary(plan_dict)
        nutrition_text = self._format_recommendations(plan_dict, "nutrition")
        fitness_text = self._format_recommendations(plan_dict, "fitness")
        supp_text = self._format_recommendations(plan_dict, "supplements")

        system_prompt = (
            "You are a nutrigenomics-focused nutrition coach. "
            "You receive structured data about genes and recommendations for one person. "
            "Based ONLY on this data, explain key tendencies and give practical diet, fitness, "
            "and lifestyle guidance. Avoid medical claims and do not mention specific diseases; "
            "talk in terms of tendencies and support."
        )

        user_prompt = (
            "Here is this person's genetics and plan summary.\n\n"
            f"GENE SUMMARY:\n{genes_text}\n\n"
            f"NUTRITION RECOMMENDATIONS:\n{nutrition_text}\n\n"
            f"FITNESS RECOMMENDATIONS:\n{fitness_text}\n\n"
            f"SUPPLEMENT RECOMMENDATIONS:\n{supp_text}\n\n"
            "Please:\n"
            "1) Briefly summarize their main nutrition-related tendencies.\n"
            "2) Give 6–10 clear, practical diet recommendations (foods to increase, foods to limit, habits).\n"
            "3) Add 3–5 key fitness/lifestyle recommendations.\n"
            "4) Where relevant, connect recommendations back to specific traits or genes.\n"
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_text(text=system_prompt),
                types.Part.from_text(text=user_prompt),
            ],
            config=types.GenerateContentConfig(
                temperature=0.7,
            ),
        )

        return response.text