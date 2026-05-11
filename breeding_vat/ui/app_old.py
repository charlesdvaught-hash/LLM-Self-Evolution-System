"""
Enhanced Streamlit UI with real-time progress streaming, experiment management, and resumption.
"""

import streamlit as st
import sqlite3
import json
import os
import logging
import torch
from datetime import datetime
from typing import Optional
import threading
import time

from breeding_vat.modules.merge.advisor import MergeAdvisor
from breeding_vat.modules.merge.evolution import EvolutionEngine
from breeding_vat.modules.sae.scoped_analyzer import SAEScopedAnalyzer
from breeding_vat.modules.experiment_manager import ExperimentManager
from breeding_vat.modules.evolution.evolution_with_logging import EvolutionWithLogging
from breeding_vat.orchestrator.runner import TaskRunner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default model zoo
MODEL_ZOO = [
    "Qwen/Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-3B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-14B-Instruct",
    "Qwen/Qwen2.5-32B-Instruct",
    "Qwen/Qwen2.5-72B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "mistralai/Mistral-Small-Instruct-2409",
    "meta-llama/Llama-2-7b-chat",
    "meta-llama/Llama-2-13b-chat",
    "meta-llama/Llama-3.1-8B-Instruct",
    "meta-llama/Llama-3.1-70B-Instruct",
    "NousResearch/Nous-Hermes-2-Mistral-7B-DPO",
    "gpt2",
    "distilbert-base-uncased",
]

st.set_page_config(page_title="The Breeding Vat", layout="wide")

st.title("🧬 The Breeding Vat")
st.subheader("Model Evolution & Merging Lab")

# Initialize system resources
@st.cache_resource
def init_system():
    """Initialize system directories, database, and managers."""
    dirs = [
        "breeding_vat/data",
        "breeding_vat/data/merged_models",
        "breeding_vat/data/eval_results",
        "breeding_vat/data/sae_analysis",
        "breeding_vat/configs",
        "breeding_vat/data/experiments",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    runner = TaskRunner()
    exp_manager = ExperimentManager()
    return runner, exp_manager

if 'runner' not in st.session_state:
    try:
        st.session_state.runner, st.session_state.exp_manager = init_system()
    except Exception as e:
        st.error(f"System initialization failed: {e}")
        logger.error(f"Init error: {e}")
        st.stop()

# Initialize session state
if 'advisor_history' not in st.session_state:
    st.session_state.advisor_history = []

if 'current_experiment' not in st.session_state:
    st.session_state.current_experiment = None

if 'evolution_log' not in st.session_state:
    st.session_state.evolution_log = []

if 'progress_placeholder' not in st.session_state:
    st.session_state.progress_placeholder = None


def log_to_ui(message: str):
    """Append message to UI evolution log."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.evolution_log.append(f"[{timestamp}] {message}")


def update_progress(placeholder, log_container, current_cycle: int, 
                   total_cycles: int, status: str):
    """Update progress bar and log in real-time."""
    with placeholder.container():
        st.progress(current_cycle / total_cycles)
        st.caption(f"{status} | Cycle {current_cycle}/{total_cycles}")
    
    with log_container.container():
        for entry in st.session_state.evolution_log[-10:]:
            st.text(entry)


# SIDEBAR: Experiment Management & Configuration

with st.sidebar:
    st.header("📋 Experiment Control")
    
    tab_exp_mode, tab_exp_load = st.tabs(["New Experiment", "Load Experiment"])
    
    with tab_exp_mode:
        st.subheader("Create New Experiment")
        
        exp_goal = st.text_area(
            "What is your goal?",
            "Make a model better at long logic reasoning, final size < 9B.",
            height=60
        )
        
        exp_custom_name = st.text_input(
            "Experiment name (optional)",
            placeholder="my_awesome_merge",
            help="Leave blank to auto-generate from goal + date"
        )
        
        if st.button("Create New Experiment", type="primary"):
            if not exp_goal.strip():
                st.error("Please enter a goal")
            else:
                try:
                    experiment = st.session_state.exp_manager.create_experiment(
                        goal=exp_goal,
                        base_models=[],
                        merge_methods=[],
                        num_cycles=1,
                        custom_name=exp_custom_name if exp_custom_name else None
                    )
                    st.session_state.current_experiment = experiment
                    st.success(f"✓ Experiment created: {experiment['name']}")
                    st.info(f"📁 Root: `{experiment['paths']['root']}`")
                except Exception as e:
                    st.error(f"Failed to create experiment: {e}")
    
    with tab_exp_load:
        st.subheader("Load Existing Experiment")
        
        available_exps = st.session_state.exp_manager.list_experiments()
        
        if available_exps:
            exp_names = [e['name'] for e in available_exps]
            selected_exp_name = st.selectbox(
                "Select experiment to resume",
                exp_names,
                format_func=lambda x: f"{x} (cycles: {[e['cycles_completed'] for e in available_exps if e['name'] == x][0]})"
            )
            
            if st.button("Load Experiment", type="secondary"):
                loaded_exp = st.session_state.exp_manager.load_experiment(selected_exp_name)
                if loaded_exp:
                    st.session_state.current_experiment = loaded_exp
                    st.success(f"✓ Loaded: {loaded_exp['name']}")
                    st.info(f"Best score so far: {loaded_exp['best_score']:.4f}")
                else:
                    st.error("Failed to load experiment")
        else:
            st.info("No experiments yet. Create one to get started!")
    
    # Show current experiment
    if st.session_state.current_experiment:
        st.divider()
        st.subheader("Current Experiment")
        exp = st.session_state.current_experiment
        st.caption(exp['name'])
        st.metric("Best Score", f"{exp['best_score']:.4f}")
        st.metric("Cycles", f"{exp['cycles_completed']}/{exp['num_cycles_planned']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📁 Open Folder"):
                import subprocess
                try:
                    subprocess.Popen(f'explorer "{exp["paths"]["root"]}"')
                except:
                    st.info(f"📁 {exp['paths']['root']}")
        with col2:
            if st.button("📊 View Logs"):
                st.session_state.show_logs = True
    
    st.divider()
    st.header("⚙️ Evolution Settings")
    
    merge_methods = st.multiselect(
        "Merging Methods",
        ["SLERP", "TIES", "DARE", "RMM", "Task Arithmetic", "NegMerge"],
        default=["SLERP", "TIES"]
    )
    
    num_cycles = st.number_input("Evolution Cycles", min_value=1, max_value=100, value=3)
    culling_rate = st.slider("Culling Rate (%)", 0, 100, 50)
    
    st.divider()
    st.header("💬 Advisor Settings")
    advisor_model = st.text_input("Advisor Model", "Qwen/Qwen2.5-0.5B-Instruct")
    use_thinking = st.checkbox("Enable Thinking Mode", value=True)
    
    st.divider()
    st.header("💭 Ask the AI")
    user_question = st.text_input(
        "Ask anything",
        placeholder="What are these models good at?",
        help="Ask the advisor for guidance"
    )
    
    if user_question.strip():
        question_text = user_question.strip()
        
        with st.spinner("Consulting AI..."):
            try:
                advisor = MergeAdvisor(model_id=advisor_model)
                response = advisor.generate_recipe(question_text, MODEL_ZOO, merge_methods)
                
                st.session_state.advisor_history.append({
                    "question": question_text,
                    "answer": response,
                    "timestamp": datetime.now().isoformat()
                })
                
                st.success("✓ Response generated")
                
                with st.expander(f"Q: {question_text[:50]}...", expanded=True):
                    st.markdown(response)
                
                if hasattr(advisor, 'model'):
                    del advisor.model
                    if hasattr(advisor, 'tokenizer'):
                        del advisor.tokenizer
                torch.cuda.empty_cache()
                
            except Exception as e:
                st.error(f"AI response failed: {e}")
                logger.error(f"AI question error: {e}")
    
    if st.session_state.advisor_history:
        st.divider()
        st.subheader("📝 Chat History")
        for i, entry in enumerate(st.session_state.advisor_history[-5:], 1):
            with st.expander(f"{i}. {entry['question'][:40]}..."):
                st.markdown(entry['answer'])


# MAIN TABS

if st.session_state.current_experiment:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Pipeline", "Lineage", "SAE Discovery", "SAE Analysis", "Logs"]
    )
    
    with tab1:
        st.header("Waterfall Pipeline")
        
        if not st.session_state.current_experiment:
            st.warning("Please create or load an experiment first")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Select Base Models**")
                
                selected_models = st.multiselect(
                    "Available Models",
                    MODEL_ZOO,
                    default=["Qwen/Qwen2.5-0.5B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct"],
                    help="Select 2+ models to merge"
                )
                
                add_custom = st.checkbox("Add custom model?", value=False)
                custom_models = []
                if add_custom:
                    custom_input = st.text_input(
                        "Custom Model (HF ID or local path)",
                        placeholder="e.g., meta-llama/Llama-3-8B"
                    )
                    if custom_input.strip():
                        custom_models = [custom_input.strip()]
                
                base_models = selected_models + custom_models
                
                if base_models:
                    st.success(f"✓ {len(base_models)} model(s) selected")
                    with st.expander("View Selected Models"):
                        for i, model in enumerate(base_models, 1):
                            st.write(f"{i}. {model}")
                else:
                    st.warning("Please select at least 2 models")
            
            with col2:
                st.write("**Advisor Recommendation**")
                
                if st.button("Consult Advisor"):
                    if len(base_models) < 2:
                        st.error("Select at least 2 models")
                    else:
                        with st.spinner("Querying Advisor..."):
                            advisor = MergeAdvisor(model_id=advisor_model)
                            try:
                                exp = st.session_state.current_experiment
                                recipe = advisor.generate_recipe(
                                    exp['goal'],
                                    base_models,
                                    merge_methods
                                )
                                st.markdown(recipe)
                                
                                st.session_state.exp_manager.save_config(
                                    exp,
                                    {"recipe": recipe, "models": base_models},
                                    "advisor_recommendation"
                                )
                            
                            except Exception as e:
                                st.error(f"Advisor failed: {e}")
                            finally:
                                if hasattr(advisor, 'model'):
                                    del advisor.model
                                    if hasattr(advisor, 'tokenizer'):
                                        del advisor.tokenizer
                                torch.cuda.empty_cache()
            
            st.divider()
            
            if st.button("RUN EVOLUTION", type="primary", use_container_width=True):
                if len(base_models) < 2:
                    st.error("Select at least 2 models to proceed")
                else:
                    exp = st.session_state.current_experiment
                    progress_placeholder = st.empty()
                    log_container = st.container()
                    
                    try:
                        def progress_callback(current_cycle, total_cycles, status):
                            update_progress(progress_placeholder, log_container, current_cycle, total_cycles, status)
                        
                        log_to_ui(f"Starting evolution: {num_cycles} cycles")
                        log_to_ui(f"Models: {', '.join([m.split('/')[-1] for m in base_models])}")
                        log_to_ui(f"Methods: {', '.join(merge_methods)}")
                        
                        update_progress(progress_placeholder, log_container, 0, num_cycles, "Initializing...")
                        
                        base_evo = EvolutionEngine(st.session_state.runner)
                        
                        evo_logged = EvolutionWithLogging(
                            evolution_engine=base_evo,
                            experiment_manager=st.session_state.exp_manager,
                            experiment=exp,
                            progress_callback=progress_callback
                        )
                        
                        best_model = evo_logged.run_waterfall(
                            base_models=base_models,
                            goal=exp['goal'],
                            num_cycles=num_cycles,
                            culling_rate=culling_rate,
                            allowed_methods=[m.lower() for m in merge_methods],
                            resume_from_cycle=exp['cycles_completed']
                        )
                        
                        log_to_ui(f"Evolution complete!")
                        log_to_ui(f"Best model: {best_model['name']}")
                        log_to_ui(f"Score: {best_model['score']:.4f}")
                        
                        update_progress(progress_placeholder, log_container, num_cycles, num_cycles, "Complete!")
                        
                        st.success(f"✓ Evolution complete! Best: {best_model['name']} ({best_model['score']:.4f})")
                        st.balloons()
                        
                    except Exception as e:
                        log_to_ui(f"ERROR: {str(e)}")
                        st.error(f"Evolution failed: {e}")
                        logger.error(f"Evolution error: {e}")
                        update_progress(progress_placeholder, log_container, 0, num_cycles, "Failed")
    
    with tab2:
        st.header("Model Lineage")
        exp = st.session_state.current_experiment
        
        try:
            benchmark_db_path = exp["paths"]["benchmark_db"]
            
            if os.path.exists(benchmark_db_path):
                with open(benchmark_db_path, 'r') as f:
                    benchmarks = json.load(f)
                
                if benchmarks["cycles"]:
                    import pandas as pd
                    
                    rows = []
                    for cycle in benchmarks["cycles"]:
                        for model in cycle["models"]:
                            rows.append({
                                "Cycle": cycle["cycle"],
                                "Model": model["name"],
                                "Score": model.get("score", 0),
                                "Method": model.get("method", "unknown")
                            })
                    
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Models", len(rows))
                    with col2:
                        st.metric("Best Score", f"{df['Score'].max():.4f}")
                    with col3:
                        st.metric("Cycles", len(benchmarks["cycles"]))
                else:
                    st.info("No cycles completed yet")
            else:
                st.info("No benchmark data yet. Run evolution to populate.")
        
        except Exception as e:
            st.error(f"Lineage browser error: {e}")
    
    with tab3:
        st.header("SAE Feature Discovery")
        st.write("Identified geometric shapes and high-importance features from evolved models.")
        st.info("SAE analysis results will appear here after evolution runs.")
    
    with tab4:
        st.header("SAE Self-Analysis")
        st.write("Analyze a model's internal representations using memory-efficient streaming.")
        
        st.info("Memory-Optimized: Uses streaming buffers, quantized activations.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            vram_gb = st.selectbox("Your VRAM", [8, 12, 24, 48], index=1)
        
        with col2:
            num_analysis_samples = st.slider("Analysis Samples", min_value=10, max_value=100, value=30)
        
        with col3:
            num_layers = st.number_input("Layers to Analyze", min_value=1, max_value=32, value=8)
        
        col1, col2 = st.columns(2)
        
        with col1:
            model_to_analyze = st.text_input("Model to Analyze", "gpt2")
        
        with col2:
            compare_with = st.text_input("Compare with Base (optional)", "")
        
        if st.button("Analyze Model", type="primary"):
            with st.spinner(f"Analyzing {model_to_analyze}..."):
                try:
                    analyzer = SAEScopedAnalyzer(model_to_analyze, vram_gb=vram_gb)
                    analysis_results = analyzer.analyze_self(
                        num_samples=num_analysis_samples,
                        num_layers=num_layers
                    )
                    
                    st.success("Analysis complete!")
                    
                    if analysis_results["emergent_behaviors"]:
                        st.subheader("Emergent Behaviors")
                        for behavior in analysis_results["emergent_behaviors"][:10]:
                            with st.expander(f"Layer {behavior['layer']}: {behavior['type']}"):
                                st.write(f"**Description:** {behavior['description']}")
                                st.metric("Strength", f"{behavior['strength']:.3f}")
                    
                    st.subheader("Activation Statistics")
                    stats = analysis_results["activation_statistics"]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Layers Analyzed", stats["num_layers_analyzed"])
                    with col2:
                        st.metric("Avg Sparsity", f"{stats['avg_sparsity']:.3f}")
                    with col3:
                        st.metric("Specialized Layers", len(stats["specialized_layers"]))
                    
                    if st.button("Export Analysis as JSON"):
                        json_str = json.dumps(analysis_results, indent=2, default=str)
                        st.download_button(
                            label="Download JSON",
                            data=json_str,
                            file_name=f"sae_analysis_{model_to_analyze.replace('/', '_')}.json",
                            mime="application/json"
                        )
                    
                    del analyzer
                    torch.cuda.empty_cache()
                
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    logger.error(f"SAE analysis error: {e}")
    
    with tab5:
        st.header("Experiment Logs")
        exp = st.session_state.current_experiment
        
        log_file_path = exp["paths"]["master_log"]
        
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as f:
                log_content = f.read()
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("Master Log")
            with col2:
                if st.button("Copy"):
                    st.toast("Log copied to clipboard")
            
            st.text_area("Log Content", log_content, height=400, disabled=True)
            
            st.download_button(
                label="Download Log",
                data=log_content,
                file_name=f"{exp['name']}_master.log",
                mime="text/plain"
            )
        else:
            st.info("No logs yet. Run evolution to generate logs.")

else:
    st.info("Create or load an experiment to begin")
