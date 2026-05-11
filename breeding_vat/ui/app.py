import streamlit as st
import sqlite3
import json
import os
import torch
from breeding_vat.modules.merge.advisor import MergeAdvisor
from breeding_vat.modules.merge.evolution import EvolutionEngine
from breeding_vat.orchestrator.runner import TaskRunner

st.set_page_config(page_title="The Breeding Vat", layout="wide")

st.title("🧬 The Breeding Vat")
st.subheader("Model Evolution & Merging Lab")

# Initialize Runner
if 'runner' not in st.session_state:
    st.session_state.runner = TaskRunner()

# Sidebar for configuration
with st.sidebar:
    st.header("Control Levers")
    merge_methods = st.multiselect(
        "Merging Methods",
        ["SLERP", "TIES", "DARE", "RMM", "Core Space", "Latent Merging", "NegMerge"],
        default=["SLERP", "TIES"]
    )

    num_cycles = st.number_input("Evolution Cycles", min_value=1, max_value=100, value=3)
    culling_rate = st.slider("Culling Rate (%)", 0, 100, 50)

    st.divider()
    st.header("Advisor Settings")
    advisor_model = st.text_input("Advisor Model", "Qwen/Qwen2.5-0.5B-Instruct") # Using stable path as fallback
    use_thinking = st.checkbox("Enable Thinking Mode", value=True)

# Main tabs
tab1, tab2, tab3 = st.tabs(["Waterfall Pipeline", "Lineage Browser", "SAE Discoveries"])

with tab1:
    st.header("Pipeline Setup")
    goal = st.text_area("What is your goal?", "Make a model better than qwen 9b at long logic, final size < 9b.")

    col1, col2 = st.columns(2)
    with col1:
        base_models_input = st.text_input("Base Models (comma separated)", "Qwen/Qwen2.5-0.5B, Qwen/Qwen2.5-1.5B")
        base_models = [m.strip() for m in base_models_input.split(",")]

    if st.button("Consult Advisor"):
        with st.spinner("Querying Advisor..."):
            advisor = MergeAdvisor(model_id=advisor_model)
            try:
                recipe = advisor.generate_recipe(goal, base_models, merge_methods)
                st.write("**Advisor Recommendation:**")
                st.markdown(recipe)
            except Exception as e:
                st.error(f"Advisor failed: {e}")
            finally:
                # VRAM Management
                if hasattr(advisor, 'model'):
                    del advisor.model
                    del advisor.tokenizer
                torch.cuda.empty_cache()

    if st.button("RUN EVOLUTION", type="primary"):
        st.info("Evolution pipeline started. Check terminal for logs.")
        evo = EvolutionEngine(st.session_state.runner)
        best_model = evo.run_waterfall(base_models, goal, num_cycles, culling_rate)
        st.success(f"Evolution complete! Best mutant: {best_model['name']} (Score: {best_model['score']:.4f})")

with tab2:
    st.header("Model Lineage")
    conn = sqlite3.connect("breeding_vat/data/breeding.db")
    import pandas as pd
    df = pd.read_sql_query("SELECT id, name, status, created_at FROM models ORDER BY id DESC", conn)
    st.dataframe(df)
    conn.close()

with tab3:
    st.header("SAE Feature Map")
    st.write("Identified geometric shapes and high-importance features.")
