import streamlit as st
import pandas as pd
import json
from pathlib import Path

from src.extraction.pdf_extractor import PDFExtractor
from src.ai.gemini_client import NutriCoachGeminiClient


st.set_page_config(page_title="NutriCoach AI", layout="wide")


def main():
    st.title("🧬 NutriCoach AI")
    st.markdown("**Upload a NutriDNA PDF report to get personalized nutrition insights**")

    # File upload
    uploaded_file = st.file_uploader("Choose a PDF report...", type="pdf")

    if uploaded_file is not None:
        # Save uploaded file
        pdf_path = Path("temp_uploaded_report.pdf")
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        with st.spinner("Extracting genes..."):
            extractor = PDFExtractor(str(pdf_path))
            extractor.load_pdf_text()
            extractor.parse_summary_tables()
            genes = extractor.get_priority_genes_with_summary()
            json_data = extractor.to_dict()

        # Show genes table
        st.subheader("📊 Extracted Priority Genes")
        genes_df = pd.DataFrame([
            {
                "Gene": g.name,
                "Page": g.page,
                "Trait": g.trait or "N/A",
                "Result": g.result or "N/A",
            }
            for g in genes
        ])
        st.dataframe(genes_df, use_container_width=True)

        # Nutrition plan button
        if st.button("✨ Get Personalized Nutrition Plan", type="primary"):
            with st.spinner("Generating plan with Gemini..."):
                client = NutriCoachGeminiClient()
                plan = client.get_nutrition_plan()
                st.markdown("### 🎯 Your Nutrition Plan")
                st.markdown(plan)

        # Show JSON (for debugging)
        with st.expander("🔍 View raw JSON"):
            st.json(json_data)


if __name__ == "__main__":
    main()