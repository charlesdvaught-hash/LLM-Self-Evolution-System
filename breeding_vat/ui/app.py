import streamlit as st
import sqlite3
import json
import os

st.set_page_config(page_title="The Breeding Vat", layout="wide")

st.title("🧬 The Breeding Vat")
st.subheader("Model Evolution & Merging Lab")

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
    advisor_model = st.text_input("Advisor Model", "Qwen/Qwen3.5-0.8B-Instruct")
    use_thinking = st.checkbox("Enable Thinking Mode", value=True)

# Main tabs
tab1, tab2, tab3 = st.tabs(["Waterfall Pipeline", "Lineage Browser", "SAE Discoveries"])

with tab1:
    st.header("Pipeline Setup")
    goal = st.text_area("What is your goal?", "Make a model better than qwen 9b at long logic, final size < 9b.")

    col1, col2 = st.columns(2)
    with col1:
        base_models = st.text_input("Base Models (comma separated)", "Qwen/Qwen2.5-7B, deepseek-ai/DeepSeek-V2-Lite")

    if st.button("Consult Advisor"):
        st.info("Querying Qwen 3.5 0.8B for a recipe plan...")
        # Placeholder for advisor logic
        st.write("**Advisor Recommendation:**")
        st.markdown("""
        1. **Phase 1**: Perform SLERP between Qwen 2.5 and DeepSeek on logic layers (layers 12-24).
        2. **Phase 2**: Apply NegMerge to prune redundant conversational weights.
        3. **Phase 3**: Use Core Space Merging to align LoRA adapters for logic-specific datasets.
        """)

    if st.button("RUN EVOLUTION", type="primary"):
        st.warning("Evolution pipeline started. Monitoring logs...")

with tab2:
    st.header("Model Lineage")
    # Placeholder for database view
    st.write("Lineage tree will appear here.")

with tab3:
    st.header("SAE Feature Map")
    st.write("Identified geometric shapes and high-importance features.")
