import streamlit as st
import pandas as pd
import json
from pathlib import Path
import sys
import os

# CRITICAL FIX: Add parent directory (nutricoach-ai/) to Python path
CURRENT_DIR = Path(__file__).parent  # This is nutricoach-ai/
SRC_DIR = CURRENT_DIR / "src"
sys.path.insert(0, str(CURRENT_DIR))  # Add nutricoach-ai/ to path
sys.path.insert(0, str(SRC_DIR))      # Add src/ to path

# Now imports work from BOTH perspectives
try:
    from extraction.pdf_extractor import PDFExtractor
    from ai.gemini_client import NutriCoachGeminiClient
    from engine.rule_engine import RuleEngine
    from engine.plan_generator import PlanGenerator
    from planning.meal_generator import MealGenerator
except ModuleNotFoundError:
    # Fallback to src. prefix
    from src.extraction.pdf_extractor import PDFExtractor
    from src.ai.gemini_client import NutriCoachGeminiClient
    from src.engine.rule_engine import RuleEngine
    from src.engine.plan_generator import PlanGenerator
    from src.planning.meal_generator import MealGenerator

st.set_page_config(
    page_title="NutriCoach AI", 
    layout="wide", 
    page_icon="🧬"
)

def plan_to_dict(plan):
    """Convert plan to JSON dict"""
    return {
        'nutrition': [item.dict() if hasattr(item, 'dict') else vars(item) for item in plan.nutrition],
        'fitness': [item.dict() if hasattr(item, 'dict') else vars(item) for item in plan.fitness],
        'supplements': [item.dict() if hasattr(item, 'dict') else vars(item) for item in plan.supplements],
        'lifestyle': [item.dict() if hasattr(item, 'dict') else vars(item) for item in plan.lifestyle]
    }

def main():
    # Header
    st.title("🧬 NutriCoach AI")
    st.markdown("**Transform your NutriDNA genetic report into personalized nutrition & fitness plans**")
    st.markdown("---")

    # File upload
    uploaded_file = st.file_uploader(
        "📄 Upload your NutriDNA PDF report", 
        type="pdf",
        help="Upload your genetic test report (NutriDNA format)"
    )

    if uploaded_file is not None:
        # Save uploaded file to temp location
        pdf_path = Path(f"temp_{uploaded_file.name}")
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        # Store in session state to avoid re-processing
        if 'genes' not in st.session_state or st.session_state.get('pdf_name') != uploaded_file.name:
            with st.spinner("🔬 Extracting genetic data from PDF..."):
                # Step 1: PDF Extraction
                extractor = PDFExtractor(str(pdf_path))
                extractor.load_pdf_text()
                genes = extractor.get_priority_genes_with_summary()
                
                # Store in session
                st.session_state.genes = genes
                st.session_state.pdf_name = uploaded_file.name
                st.session_state.pdf_path = str(pdf_path)

        genes = st.session_state.genes

        # Success message
        st.success(f"✅ Successfully extracted {len(genes)} priority genes from your report!")

        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Genes", 
            "🎯 Health Plan", 
            "🍽️ Meal Plan", 
            "🤖 AI Report",
            "💾 Download"
        ])

        # TAB 1: Genes Table
        with tab1:
            st.subheader("📊 Extracted Priority Genes")
            genes_df = pd.DataFrame([
    {
        "Gene": g.name if hasattr(g, 'name') else 'N/A',
        "Page": g.page if hasattr(g, 'page') else 'N/A',
        "Trait": g.trait if hasattr(g, 'trait') else 'N/A',
        "Result": g.result if hasattr(g, 'result') else 'N/A',
        "Context": (g.context[:100] + "..." if hasattr(g, 'context') and g.context else "N/A")
    }
    for g in genes
])
            st.dataframe(genes_df, use_container_width=True, height=400)
            
            # Show summary stats
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Genes", len(genes))
            col2.metric("PDF Pages", genes[0].page if genes and hasattr(genes[0], 'page') else 'N/A')
            col3.metric("Report", st.session_state.pdf_name)

        # TAB 2: Health Plan (Rule-Based)
        with tab2:
            st.subheader("🎯 Your Personalized Health Plan")
            
            if st.button("🔄 Generate Complete Plan", type="primary", use_container_width=True):
                with st.spinner("⚙️ Applying nutrigenomics rules..."):
                    # Step 2: Rule Engine
                    engine = RuleEngine("data/rules.yml")
                    advice_list = engine.apply_rules(genes)
                    
                    # Step 3: Plan Generator
                    generator = PlanGenerator()
                    plan = generator.generate_plan(advice_list)
                    plan_dict = plan_to_dict(plan)
                    
                    # Store in session
                    st.session_state.plan = plan
                    st.session_state.plan_dict = plan_dict
                    st.session_state.advice_list = advice_list

            # Display plan if exists
            if 'plan' in st.session_state:
                plan = st.session_state.plan
                
                # Summary cards
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("🥗 Nutrition", len(plan.nutrition))
                col2.metric("💪 Fitness", len(plan.fitness))
                col3.metric("💊 Supplements", len(plan.supplements))
                col4.metric("🌿 Lifestyle", len(plan.lifestyle))
                
                st.markdown("---")
                
                # Nutrition Section
                if plan.nutrition:
                    st.markdown("### 🥗 Nutrition Recommendations")
                    for item in plan.nutrition:
                        try:
                            title = getattr(item, 'title', 'Nutrition Item')
                            priority = getattr(item, 'priority', 'N/A')
                            
                            with st.expander(f"**{title}** - Priority: {priority}"):
                                # Display all available attributes
                                for attr in ['gene', 'gene_name', 'description', 'details', 'foods', 'recommendations']:
                                    value = getattr(item, attr, None)
                                    if value:
                                        if attr in ['foods', 'recommendations'] and isinstance(value, list):
                                            st.markdown(f"**{attr.title()}:**")
                                            for v in value:
                                                st.markdown(f"- {v}")
                                        else:
                                            st.markdown(f"**{attr.replace('_', ' ').title()}:** {value}")
                        except Exception as e:
                            st.error(f"Error displaying item: {e}")

                # Fitness Section
                if plan.fitness:
                    st.markdown("### 💪 Fitness Recommendations")
                    for item in plan.fitness:
                        title = getattr(item, 'title', 'Fitness Recommendation')
                        priority = getattr(item, 'priority', 'N/A')
                        
                        with st.expander(f"*{title}* - Priority: {priority}"):
                            description = getattr(item, 'description', 'No description')
                            focus = getattr(item, 'focus', [])
                            frequency = getattr(item, 'frequency_per_week', 'Not specified')
                            genes = getattr(item, 'related_genes', [])
                            
                            st.markdown(f"*Description:* {description}")
                            if focus:
                                st.markdown(f"*Focus Areas:* {', '.join(focus)}")
                            if frequency:
                                st.markdown(f"*Frequency:* {frequency} per week")
                            if genes:
                                st.markdown(f"*Related Genes:* {', '.join(genes)}")

                # Supplements Section
                if plan.supplements:
                    st.markdown("### 💊 Supplement Recommendations")
                    for item in plan.supplements:
                        name = getattr(item, 'name', 'Supplement')
                        priority = getattr(item, 'priority', 'N/A')
                        
                        with st.expander(f"*{name}* - Priority: {priority}"):
                            description = getattr(item, 'description', 'No description')
                            dosage = getattr(item, 'typical_dosage', 'Consult professional')
                            timing = getattr(item, 'timing', 'Not specified')
                            genes = getattr(item, 'related_genes', [])
                            
                            st.markdown(f"*Description:* {description}")
                            st.markdown(f"*Typical Dosage:* {dosage}")
                            if timing:
                                st.markdown(f"*Timing:* {timing}")
                            if genes:
                                st.markdown(f"*Related Genes:* {', '.join(genes)}")

                # Lifestyle Section  
                if plan.lifestyle:
                    st.markdown("### 🌿 Lifestyle Recommendations")
                    for item in plan.lifestyle:
                        title = getattr(item, 'title', 'Lifestyle Recommendation')
                        with st.expander(f"*{title}*"):
                            description = getattr(item, 'description', 'No description')
                            st.markdown(description)
        # TAB 3: Meal Plan
        with tab3:
            st.subheader("🍽️ DNA-Optimized Meal Plan")
            
            if 'plan_dict' not in st.session_state:
                st.warning("⚠️ Please generate your Health Plan first (Tab 2)")
            else:
                if st.button("🥗 Generate Daily Meals", type="primary", use_container_width=True):
                    with st.spinner("👨‍🍳 Creating your personalized menu..."):
                        try:
                            meal_gen = MealGenerator()
                            menu = meal_gen.generate_daily_plan(st.session_state.plan_dict)
                            st.session_state.menu = menu
                        except Exception as e:
                            st.error(f"Error generating meals: {e}")
                            st.session_state.menu = None

                # Display meals if exists
                if 'menu' in st.session_state and st.session_state.menu:
                    menu = st.session_state.menu
                    
                    st.markdown("### 📅 Your Daily Menu")
                    
                    for meal_time, foods in menu.items():
                        st.markdown(f"#### {meal_time.title()}")
                        if foods:
                            for food in foods:
                                st.markdown(f"- {food}")
                        else:
                            st.markdown("*No specific recommendations for this meal*")
                        st.markdown("")
                    
                    # Save to markdown
                    menu_md = "# 🧬 Your DNA-Optimized Meal Plan\n\n"
                    for meal_time, foods in menu.items():
                        menu_md += f"## {meal_time.title()}\n\n"
                        for food in foods:
                            menu_md += f"- {food}\n"
                        menu_md += "\n"
                    
                    st.session_state.menu_md = menu_md
                else:
                    st.info("👆 Click 'Generate Daily Meals' to see your DNA-optimized menu")

        # TAB 4: Gemini AI Report
        with tab4:
            st.subheader("🤖 AI-Generated Nutrition Report")
            
            # Load environment variables
            from dotenv import load_dotenv
            import os
            load_dotenv()  # Loads .env file
            
            api_key = os.getenv("GEMINI_API_KEY")
            
            if not api_key:
                st.warning("⚠️ Gemini API key not configured")
                st.markdown("""
                *To enable AI reports:*
                1. Create .env file in project root (nutricoach-ai/)
                2. Add line: GEMINI_API_KEY=your_key_here
                3. Get key from: https://aistudio.google.com/app/apikey
                4. Restart Streamlit
                """)
            else:
                st.success("✅ API key loaded successfully")
            
            if st.button("✨ Generate AI Explanation", type="primary", use_container_width=True):
                with st.spinner("🧠 Gemini is analyzing your genetics..."):
                    try:
                        # Check if plan exists
                        if 'plan_dict' not in st.session_state:
                            st.error("❌ Please generate a health plan first (Health Plan tab)")
                        else:
                            client = NutriCoachGeminiClient()
                            report = client.generate_report(st.session_state.plan_dict)
                            st.session_state.ai_report = report
                            st.success("✅ Report generated successfully!")
                            
                    except Exception as e:
                        st.error(f"⚠️ Error: {str(e)}")
                        st.info("💡 Common issues: Invalid API key, rate limit, or network error")
                        import traceback
                        st.code(traceback.format_exc())  # Debug info

            # Display report if exists
            if 'ai_report' in st.session_state:
                st.markdown("### 📝 Your Personalized Report")
                st.markdown(st.session_state.ai_report)
            else:
                st.info("👆 Click 'Generate AI Explanation' for human-readable insights from Gemini")

            

        # TAB 5: Download
        with tab5:
            st.subheader("💾 Download Your Reports")
            
            col1, col2, col3 = st.columns(3)
            
            # Download JSON plan
            if 'plan_dict' in st.session_state:
                json_str = json.dumps(st.session_state.plan_dict, indent=2, ensure_ascii=False)
                col1.download_button(
                    label="📥 Download JSON Plan",
                    data=json_str,
                    file_name="nutricoach_plan.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            # Download meal plan
            if 'menu_md' in st.session_state:
                col2.download_button(
                    label="📥 Download Meal Plan",
                    data=st.session_state.menu_md,
                    file_name="nutricoach_menu.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            # Download AI report
            if 'ai_report' in st.session_state:
                col3.download_button(
                    label="📥 Download AI Report",
                    data=st.session_state.ai_report,
                    file_name="nutricoach_report.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            if not any(k in st.session_state for k in ['plan_dict', 'menu_md', 'ai_report']):
                st.info("Generate plans first to enable downloads")

        # Debug section (collapsible)
        with st.expander("🔍 Debug: View Raw JSON Data"):
            if 'plan_dict' in st.session_state:
                st.json(st.session_state.plan_dict)
            else:
                st.json({"genes": genes})

    else:
        # Landing page when no file uploaded
        st.info("👆 Upload your NutriDNA PDF report to get started")
        
        st.markdown("### 🎯 What NutriCoach AI Does")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 1️⃣ Extract")
            st.markdown("Analyzes your genetic report and identifies priority genes")
        
        with col2:
            st.markdown("#### 2️⃣ Interpret")
            st.markdown("Applies nutrigenomics rules to generate personalized recommendations")
        
        with col3:
            st.markdown("#### 3️⃣ Plan")
            st.markdown("Creates actionable nutrition, fitness, and lifestyle plans")

if __name__ == "__main__":
    main()