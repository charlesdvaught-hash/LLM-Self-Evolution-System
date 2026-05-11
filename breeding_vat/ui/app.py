"""
Enhanced Streamlit UI - Technical, Polished, Exciting
Real-time evolution with personality that responds to actual progress.
Integrated with FusionBench (15+ merging methods) + MergeKit (SLERP/TIES/DARE/MOE)
"""

import streamlit as st
import sqlite3
import json
import os
import logging
import torch
from datetime import datetime
from typing import Optional, Dict
import threading
import time
import math

from breeding_vat.utils.hardware import get_hardware_stats, predict_resources, get_risk_assessment
from breeding_vat.modules.merge.advisor import MergeAdvisor
from breeding_vat.modules.merge.evolution import EvolutionEngine
from breeding_vat.modules.merge.merger import AdvancedMerger
from breeding_vat.modules.sae.scoped_analyzer import SAEScopedAnalyzer
from breeding_vat.modules.experiment_manager import ExperimentManager
from breeding_vat.modules.evolution.evolution_with_logging import EvolutionWithLogging
from breeding_vat.modules.model_transfer import ModelTransfer
from breeding_vat.orchestrator.runner import TaskRunner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

st.set_page_config(
    page_title="The Breeding Vat",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for technical polish
st.markdown("""
<style>
    /* Typography & spacing */
    body { font-family: 'Courier New', monospace; }
    h1 { letter-spacing: 2px; font-weight: 700; }
    h2 { letter-spacing: 1px; margin-top: 1.5em; }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 1rem;
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    }
    
    /* Status indicators */
    .status-success { color: #3fb950; font-weight: bold; }
    .status-warning { color: #d29922; font-weight: bold; }
    .status-error { color: #f85149; font-weight: bold; }
    .status-info { color: #58a6ff; font-weight: bold; }
    
    /* Code blocks */
    code { 
        background-color: #0d1117;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.85em;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧬 The Breeding Vat")
st.markdown("**Autonomous Model Evolution Engine** • FusionBench + MergeKit • 20+ Merging Methods")

# Initialize
@st.cache_resource
def init_system():
    dirs = [
        "breeding_vat/data",
        "breeding_vat/data/model_zoo",
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
    merger = AdvancedMerger(runner)
    model_transfer = ModelTransfer()
    return runner, exp_manager, merger, model_transfer

if 'runner' not in st.session_state:
    try:
        st.session_state.runner, st.session_state.exp_manager, st.session_state.merger, st.session_state.model_transfer = init_system()
    except Exception as e:
        st.error(f"System initialization failed: {e}")
        st.stop()

if 'advisor_history' not in st.session_state:
    st.session_state.advisor_history = []

if 'current_experiment' not in st.session_state:
    st.session_state.current_experiment = None

if 'evolution_log' not in st.session_state:
    st.session_state.evolution_log = []

if 'cycle_stats' not in st.session_state:
    st.session_state.cycle_stats = {"total_cycles": 0, "best_score": 0.0, "best_model": None}

# Get all available merging methods
@st.cache_resource
def get_merging_methods():
    merger = st.session_state.merger
    return merger.get_available_methods()

MERGING_METHODS = get_merging_methods()

# Excitement reactions
def get_excitement(score_improvement: float, is_new_best: bool = False) -> str:
    """Return excitement level based on performance."""
    if is_new_best and score_improvement > 0.1:
        return "🔥 NEW BEST — breakthrough discovery!"
    elif is_new_best and score_improvement > 0.05:
        return "✨ New peak — solid progress"
    elif score_improvement > 0.03:
        return "📈 Improving — heading in right direction"
    elif score_improvement > 0.0:
        return "➡️ Marginal gain — still exploring"
    elif score_improvement == 0.0:
        return "⚪ Neutral — no improvement"
    else:
        return "📉 Declined — pruning"

def format_benchmark_result(score: float, previous_best: float) -> str:
    """Format benchmark result with excitement."""
    improvement = ((score - previous_best) / previous_best * 100) if previous_best > 0 else 0
    emoji = "🎯" if score > 0.7 else "📊" if score > 0.5 else "🔨"
    
    if improvement > 0:
        return f"{emoji} {score:.4f} (+{improvement:.1f}%)"
    elif improvement < 0:
        return f"{emoji} {score:.4f} ({improvement:.1f}%)"
    else:
        return f"{emoji} {score:.4f}"

def log_to_ui(message: str, level: str = "info"):
    """Log to UI with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "debug": "🔍"
    }.get(level, "•")
    
    st.session_state.evolution_log.append(f"[{timestamp}] {prefix} {message}")

def update_progress(placeholder, log_container, metrics_container, 
                   current_cycle: int, total_cycles: int, status: str, 
                   current_score: float = None, best_score: float = None):
    """Update progress UI with real-time metrics."""
    progress_ratio = current_cycle / total_cycles
    
    with placeholder.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.progress(progress_ratio)
        with col2:
            st.caption(f"{current_cycle}/{total_cycles} cycles")
        
        # Status line with pulse effect
        status_symbol = "▶️" if "Merging" in status else "📊" if "Evaluating" in status else "✓" if "Complete" in status else "⏸"
        st.markdown(f"**{status_symbol} {status}**")
    
    with log_container.container():
        st.markdown("**Recent Activity**")
        for entry in st.session_state.evolution_log[-8:]:
            st.code(entry, language=None)
    
    with metrics_container.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Progress", f"{progress_ratio*100:.0f}%")
        with col2:
            if current_score is not None:
                st.metric("Current Score", f"{current_score:.4f}")
        with col3:
            if best_score is not None:
                st.metric("Best Score", f"{best_score:.4f}")


# SIDEBAR
with st.sidebar:
    st.markdown("---")
    st.header("🎛️ Mission Control")
    
    tab_new, tab_load = st.tabs(["New Mission", "Resume"])
    
    with tab_new:
        st.subheader("Launch Experiment")
        
        exp_goal = st.text_area(
            "What are we optimizing for?",
            "Reasoning at 3B scale, <9B final model",
            height=60,
            help="Be specific: model size, capability, constraints"
        )
        
        exp_name = st.text_input(
            "Mission codename (optional)",
            placeholder="reasoning_fusion_v1",
            help="Auto-generated from goal if blank"
        )
        
        if st.button("🚀 Initialize", type="primary", use_container_width=True):
            if not exp_goal.strip():
                st.error("Define your goal first")
            else:
                try:
                    experiment = st.session_state.exp_manager.create_experiment(
                        goal=exp_goal,
                        base_models=[],
                        merge_methods=[],
                        num_cycles=1,
                        custom_name=exp_name if exp_name else None
                    )
                    st.session_state.current_experiment = experiment
                    st.session_state.cycle_stats = {"total_cycles": 0, "best_score": 0.0, "best_model": None}
                    st.success(f"✅ Mission active: `{experiment['name']}`")
                    st.info(f"📁 {experiment['paths']['root']}")
                except Exception as e:
                    st.error(f"Initialization failed: {e}")
    
    with tab_load:
        st.subheader("Resume Mission")
        
        available_exps = st.session_state.exp_manager.list_experiments()
        
        if available_exps:
            exp_options = {e['name']: e for e in available_exps}
            selected = st.selectbox(
                "Available experiments",
                list(exp_options.keys()),
                format_func=lambda x: f"{x} ({exp_options[x]['cycles_completed']} cycles, score: {exp_options[x]['best_score']:.4f})"
            )
            
            if st.button("📂 Load", type="secondary", use_container_width=True):
                loaded_exp = st.session_state.exp_manager.load_experiment(selected)
                if loaded_exp:
                    st.session_state.current_experiment = loaded_exp
                    st.session_state.cycle_stats = {
                        "total_cycles": loaded_exp['cycles_completed'],
                        "best_score": loaded_exp['best_score'],
                        "best_model": loaded_exp['best_model']
                    }
                    st.success(f"✅ Resumed: `{loaded_exp['name']}`")
        else:
            st.info("No prior experiments. Launch a new mission.")
    
    st.markdown("---")
    
    if st.session_state.current_experiment:
        exp = st.session_state.current_experiment
        st.markdown("### 📊 Current Mission")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Cycles", f"{exp['cycles_completed']}/{exp['num_cycles_planned']}")
        with col2:
            st.metric("Best", f"{exp['best_score']:.4f}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📁 Open", use_container_width=True):
                import subprocess
                try:
                    subprocess.Popen(f'explorer "{exp["paths"]["root"]}"')
                except:
                    st.info(f"📁 {exp['paths']['root']}")
        with col2:
            if st.button("📋 Logs", use_container_width=True):
                st.session_state.show_logs = True
        
        st.markdown("---")
    
    st.markdown("### ⚙️ Evolution Settings")

    duration_mode = st.select_slider(
        "Duration",
        options=["Speedy", "Balanced", "Thorough"],
        value="Balanced",
        help="Speedy: Simple/fast merges. Thorough: Complex merges and deep analysis."
    )
    
    # Categorize methods
    mergekit_methods = ["slerp", "ties", "dare", "moe", "rmm", "negmerge"]
    fusionbench_methods = [m for m in MERGING_METHODS.keys() if m not in mergekit_methods]
    
    # Filter methods based on duration
    if duration_mode == "Speedy":
        mk_options = ["SLERP", "LINEAR", "TASK_ARITHMETIC"]
        fb_options = ["LINEAR", "VOTING"]
        # Intersect with available
        mk_available = [m.upper() for m in mergekit_methods if m.upper() in mk_options or m == "slerp"]
        fb_available = [m.upper() for m in fusionbench_methods if m.upper() in fb_options]
    else:
        mk_available = [m.upper() for m in mergekit_methods]
        fb_available = [m.upper() for m in fusionbench_methods]

    st.caption("🔧 MergeKit (Weight Interpolation)")
    mergekit_selected = st.multiselect(
        "MergeKit methods",
        mk_available,
        default=["SLERP"] if duration_mode == "Speedy" else ["SLERP", "TIES"],
        help="Classical interpolation & weighted merging",
        key="mergekit_select",
        label_visibility="collapsed"
    )
    
    st.caption("🧠 FusionBench (Advanced Techniques)")
    fusionbench_selected = st.multiselect(
        "FusionBench methods",
        fb_available[:8],
        default=["VOTING"] if duration_mode == "Speedy" else ["TASK_ARITHMETIC", "REGMEAN"],
        help="Regression, voting, layer-wise, and advanced merging",
        key="fb_select",
        label_visibility="collapsed"
    )
    
    merge_methods = [m.lower() for m in (mergekit_selected + fusionbench_selected)]
    
    num_cycles = st.number_input("Evolution Rounds", 1, 100, 3, help="Evolution iterations")
    models_per_evolution = st.number_input("Models per Evolution", 1, 10, 2, help="Branching factor: children per parent")

    culling_rate = st.slider("Culling %", 0, 100, 50, help="% of population to eliminate")
    min_passing_score = st.slider("Min Passing Score", 0.0, 1.0, 0.0, 0.01, help="Models below this are culled immediately")
    second_chances = st.checkbox("Second Chances", value=False, help="Re-evaluate borderline models before culling")

    include_sae = st.checkbox("Include SAE Analysis", value=duration_mode == "Thorough", help="Run SAE analysis on offspring")
    
    st.markdown("---")
    st.markdown("### ⚙️ Method Parameters")
    
    # Per-method parameter controls
    with st.expander("Task Arithmetic", expanded=False):
        ta_reg = st.slider("Regularization", 0.0, 1.0, 0.0, help="Regularization strength")
    
    with st.expander("RegMean", expanded=False):
        rm_reg = st.slider("Regularization (RegMean)", 0.0, 1.0, 0.0)
    
    with st.expander("DARE", expanded=False):
        dare_drop = st.slider("Drop Rate", 0.0, 0.5, 0.1, help="Sparsity level")
    
    with st.expander("TIES", expanded=False):
        ties_thresh = st.slider("Threshold", 0.5, 1.0, 0.9, help="Density threshold")
    
    with st.expander("Voting", expanded=False):
        vote_method = st.selectbox("Voting Type", ["majority", "unanimous", "weighted"])
    
    with st.expander("Magnitude Prune", expanded=False):
        prune_ratio = st.slider("Prune Ratio", 0.0, 0.5, 0.1, help="Fraction to prune")
    
    with st.expander("Frankenmerge", expanded=False):
        fm_rank = st.slider("Rank", 1, 32, 8, help="Layer-wise decomposition rank")
    
    st.markdown("---")
    st.markdown("### 🛡️ Hardware Guard")

    hw_stats = get_hardware_stats()
    # Assume 2.5B parameter models (avg 5GB) for estimation if no models selected
    estimated_size = 5.0

    if merge_methods:
        prediction = predict_resources(merge_methods[0], [estimated_size] * 2)
        risk_assessment = get_risk_assessment(prediction, hw_stats)

        risk_color = "red" if risk_assessment["status"] == "danger" else "orange" if risk_assessment["status"] == "warning" else "green"
        st.markdown(f"Risk Level: <span style='color:{risk_color}; font-weight:bold;'>{risk_assessment['max_risk']:.1f}%</span>", unsafe_allow_html=True)

        if risk_assessment["max_risk"] > 75:
            st.warning("⚠️ High failure risk! Lower 'Models per Evolution' or use 'Speedy' mode.")

        with st.expander("Resource Estimates"):
            st.write(f"VRAM: {prediction['vram']:.1f} / {hw_stats['vram_total']:.1f} GB")
            st.write(f"RAM: {prediction['ram']:.1f} / {hw_stats['ram_available']:.1f} GB")
            st.write(f"Disk: {prediction['disk']:.1f} / {hw_stats['disk_free']:.1f} GB")

    st.markdown("---")
    st.markdown("### 🤖 Advisor")
    
    advisor_model = st.selectbox(
        "Advisor model",
        ["Qwen/Qwen2.5-0.8B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct"],
        help="AI guide for recipe suggestions"
    )
    
    user_question = st.text_input(
        "Ask the advisor",
        placeholder="Which models work best together?",
        help="Get AI-guided suggestions"
    )
    
    if user_question.strip():
        with st.spinner("Consulting AI..."):
            try:
                advisor = MergeAdvisor(model_id=advisor_model)
                response = advisor.generate_recipe(user_question, MODEL_ZOO, merge_methods)
                
                st.session_state.advisor_history.append({
                    "question": user_question,
                    "answer": response,
                    "timestamp": datetime.now().isoformat()
                })
                
                with st.expander(f"💡 {user_question[:40]}...", expanded=True):
                    st.markdown(response)
                
                if hasattr(advisor, 'model'):
                    del advisor.model
                    if hasattr(advisor, 'tokenizer'):
                        del advisor.tokenizer
                torch.cuda.empty_cache()
                
            except Exception as e:
                st.error(f"Advisor error: {e}")


# MAIN INTERFACE
if st.session_state.current_experiment:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["🧪 Evolution", "🌳 Lineage", "🧠 SAE", "🔬 Methods", "📊 Analysis", "📋 Logs"]
    )
    
    with tab1:
        st.markdown("## Evolution Pipeline")
        st.markdown("Configure and execute model synthesis across multiple cycles.")
        
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            st.subheader("Base Models")
            
            # Get local models already transferred
            local_models_list = st.session_state.model_transfer.list_local_models()
            local_model_names = [m['name'] for m in local_models_list]
            
            # Combine HuggingFace models with local models
            all_model_options = MODEL_ZOO + local_model_names
            
            selected_models = st.multiselect(
                "Selection",
                all_model_options,
                default=["Qwen/Qwen2.5-0.5B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct"],
                help="2+ models to merge (HF IDs or uploaded local models)",
                label_visibility="collapsed"
            )
            
            # Local model upload section
            with st.expander("📤 Upload Local Model", expanded=False):
                st.markdown("Transfer a local model to the model zoo for use in experiments.")
                
                uploaded_path = st.text_input(
                    "Local model path",
                    placeholder="/path/to/my-qwen-finetuned/",
                    help="Full path to model directory (must contain config.json)"
                )
                
                if uploaded_path.strip():
                    is_valid, validation_msg = st.session_state.model_transfer.validate_model_path(uploaded_path)
                    if is_valid:
                        st.success(f"✅ {validation_msg}")
                    else:
                        st.warning(f"⚠️ {validation_msg}")
                
                model_display_name = st.text_input(
                    "Display name",
                    placeholder="my-qwen-finetuned",
                    help="How to refer to this model in experiments"
                )
                
                model_description = st.text_area(
                    "Description (optional)",
                    placeholder="Finetuned on math reasoning dataset...",
                    height=60
                )
                
                if st.button("🚀 Transfer Model", use_container_width=True):
                    if not uploaded_path.strip():
                        st.error("Provide a local path")
                    elif not model_display_name.strip():
                        st.error("Provide a display name")
                    else:
                        with st.spinner("Transferring model..."):
                            success, dest_path, info = st.session_state.model_transfer.register_local_model(
                                local_path=uploaded_path.strip(),
                                model_name=model_display_name.strip(),
                                experiment_id=st.session_state.current_experiment['name'] if st.session_state.current_experiment else None,
                                metadata={
                                    "description": model_description.strip(),
                                    "uploaded_at": datetime.now().isoformat()
                                }
                            )
                            
                            if success:
                                st.success(f"✅ Model transferred: `{info['name']}`")
                                st.info(f"📁 Zoo location: `{dest_path}`")
                                st.info(f"📊 Size: {info['size_bytes'] / (1024**3):.2f} GB")
                                st.rerun()
                            else:
                                st.error(f"Transfer failed: {info.get('error', 'Unknown error')}")
            
            add_custom = st.checkbox("Custom HF model", value=False)
            custom_models = []
            if add_custom:
                custom_input = st.text_input("HF ID", placeholder="mistralai/Mistral-7B")
                if custom_input.strip():
                    custom_models = [custom_input.strip()]
            
            base_models = selected_models + custom_models
            
            if base_models:
                st.success(f"✅ {len(base_models)} model(s) selected")
                with st.expander("Details", expanded=False):
                    for i, m in enumerate(base_models, 1):
                        st.code(m, language=None)
        
        with col2:
            st.subheader("Advisor")
            
            if st.button("🤖 Get Recipe", use_container_width=True):
                if len(base_models) < 2:
                    st.error("Need 2+ models")
                else:
                    with st.spinner("Generating recipe..."):
                        advisor = MergeAdvisor(model_id=advisor_model)
                        try:
                            exp = st.session_state.current_experiment
                            recipe = advisor.generate_recipe(exp['goal'], base_models, merge_methods, hardware_constraints=hw_stats)
                            
                            st.session_state.exp_manager.save_config(
                                exp,
                                {"recipe": recipe, "models": base_models},
                                "advisor_recommendation"
                            )
                            
                            st.markdown(recipe)
                        except Exception as e:
                            st.error(f"Failed: {e}")
                        finally:
                            if hasattr(advisor, 'model'):
                                del advisor.model
                                if hasattr(advisor, 'tokenizer'):
                                    del advisor.tokenizer
                            torch.cuda.empty_cache()
        
        st.markdown("---")
        
        # Run evolution
        if st.button("▶️ START EVOLUTION", type="primary", use_container_width=True, key="evo_run"):
            if len(base_models) < 2:
                st.error("Select 2+ base models")
            elif not merge_methods:
                st.error("Select at least one merge method")
            else:
                exp = st.session_state.current_experiment
                
                # Update config
                exp['base_models'] = base_models
                exp['merge_methods'] = merge_methods
                exp['num_cycles_planned'] = num_cycles
                st.session_state.exp_manager._save_metadata(exp)
                
                # Create containers
                st.markdown("---")
                st.subheader("🚀 Evolution in Progress")
                
                progress_placeholder = st.empty()
                metrics_container = st.empty()
                log_container = st.container()
                log_container.markdown("### 📜 Cycle Log")
                
                try:
                    def progress_callback(current, total, status):
                        update_progress(
                            progress_placeholder, log_container, metrics_container,
                            current, total, status,
                            current_score=st.session_state.cycle_stats.get("best_score"),
                            best_score=st.session_state.cycle_stats.get("best_score")
                        )
                    
                    log_to_ui(f"Starting evolution: {num_cycles} cycles", "success")
                    log_to_ui(f"Methods: {', '.join(merge_methods)}", "debug")
                    log_to_ui(f"Models: {', '.join([m.split('/')[-1] for m in base_models])}", "debug")
                    
                    update_progress(progress_placeholder, log_container, metrics_container,
                                  0, num_cycles, "Initializing evolution engine...",
                                  best_score=exp['best_score'])
                    
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
                        allowed_methods=merge_methods,
                        resume_from_cycle=exp['cycles_completed'],
                        models_per_evolution=models_per_evolution,
                        min_passing_score=min_passing_score,
                        second_chances=second_chances,
                        include_sae=include_sae,
                        duration_mode=duration_mode
                    )
                    
                    # Update stats
                    improvement = ((best_model['score'] - exp['best_score']) / (exp['best_score'] + 1e-8)) * 100
                    excitement = get_excitement(improvement, is_new_best=best_model['score'] > exp['best_score'])
                    
                    log_to_ui(f"Evolution complete!", "success")
                    log_to_ui(f"Best model: {best_model['name']}", "success")
                    log_to_ui(f"Final score: {format_benchmark_result(best_model['score'], exp['best_score'])}", "success")
                    log_to_ui(excitement, "success")
                    
                    st.session_state.cycle_stats = {
                        "total_cycles": num_cycles,
                        "best_score": best_model['score'],
                        "best_model": best_model['name']
                    }
                    
                    update_progress(progress_placeholder, log_container, metrics_container,
                                  num_cycles, num_cycles, "✅ Complete",
                                  best_score=best_model['score'])
                    
                    st.markdown("---")
                    st.markdown(f"### {excitement}")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Best Score", f"{best_model['score']:.4f}")
                    with col2:
                        st.metric("Best Model", best_model['name'][-25:])
                    with col3:
                        st.metric("Improvement", f"{improvement:+.1f}%")
                    
                    st.balloons()
                    
                except Exception as e:
                    log_to_ui(f"Evolution failed: {str(e)}", "error")
                    st.error(f"❌ Failed: {e}")
                    logger.error(f"Evolution error: {e}")
    
    with tab2:
        st.markdown("## Model Lineage")
        st.markdown("Genealogy and performance history of evolved models.")
        
        exp = st.session_state.current_experiment
        benchmark_db_path = exp["paths"]["benchmark_db"]
        
        try:
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
                                "Model": model["name"][-30:],
                                "Score": model.get("score", 0),
                                "Method": model.get("method", "?").upper()
                            })
                    
                    df = pd.DataFrame(rows)
                    
                    # Stats
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Models Tested", len(rows))
                    with col2:
                        st.metric("Best Score", f"{df['Score'].max():.4f}")
                    with col3:
                        st.metric("Avg Score", f"{df['Score'].mean():.4f}")
                    with col4:
                        st.metric("Cycles", len(benchmarks["cycles"]))
                    
                    st.markdown("---")
                    
                    # Table
                    st.markdown("### Performance History")
                    st.dataframe(
                        df.sort_values("Score", ascending=False),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Chart
                    st.markdown("### Score Trajectory")
                    best_per_cycle = df.groupby("Cycle")["Score"].max()
                    st.line_chart(best_per_cycle)
                else:
                    st.info("Run evolution to populate lineage.")
            else:
                st.info("Lineage data not available yet.")
        except Exception as e:
            st.error(f"Lineage error: {e}")
    
    with tab3:
        st.markdown("## Sparse Autoencoder Analysis")
        st.markdown("Geometric feature discovery and layer introspection.")
        st.info("📊 SAE results available after evolution completes.")
    
    with tab4:
        st.markdown("## Available Merging Methods")
        st.markdown("**20+ techniques from MergeKit and FusionBench**")
        
        # Display all methods
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔧 MergeKit Methods (7)")
            mergekit_desc = {
                "slerp": "Spherical linear interpolation",
                "ties": "Trim, Interleave, Elect Subnets",
                "dare": "Drop And REscale",
                "moe": "Mixture of Experts",
                "rmm": "Resurrection by Majority Merging",
                "negmerge": "Negative direction subtraction",
                "task_arithmetic": "Vector arithmetic on task deltas"
            }
            for method, desc in mergekit_desc.items():
                st.code(f"**{method.upper()}** - {desc}", language=None)
        
        with col2:
            st.markdown("### 🧠 FusionBench Methods (13+)")
            fb_desc = {
                "linear": "Simple linear interpolation",
                "regmean": "Regression-based mean with optimization",
                "voting": "Majority voting on weight values",
                "magnitude_prune": "Sparse merging by magnitude",
                "git_rebasin": "Geometric mean in task space",
                "dare_linear": "Drop & rescale variant",
                "ties_linear": "TIES with linear interpolation",
                "frankenmerge": "Layer-wise expert selection",
                "layer_wise": "Per-layer weighted merging",
                "multi_task": "Multi-task optimization",
                "expert_selection": "Automatic expert routing",
                "variance_reduction": "Variance-aware blending",
            }
            for method, desc in fb_desc.items():
                st.code(f"**{method.upper()}** - {desc}", language=None)
        
        st.markdown("---")
        st.markdown("### Parameter Configuration")
        st.info("Configure method-specific parameters in the sidebar under 'Method Parameters'")
    
    with tab5:
        st.markdown("## SAE Self-Analysis")
        st.markdown("Analyze model internals with streaming memory optimization.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            vram_gb = st.selectbox("VRAM", [8, 12, 24, 48], index=1)
        with col2:
            num_samples = st.slider("Samples", 10, 100, 30)
        with col3:
            num_layers = st.number_input("Layers", 1, 32, 8)
        
        col1, col2 = st.columns(2)
        with col1:
            model_id = st.text_input("Model", "gpt2")
        with col2:
            compare_with = st.text_input("Compare (optional)", "")
        
        if st.button("🔬 Analyze", type="primary"):
            with st.spinner("Analyzing model internals..."):
                try:
                    analyzer = SAEScopedAnalyzer(model_id, vram_gb=vram_gb)
                    results = analyzer.analyze_self(num_samples=num_samples, num_layers=num_layers)
                    
                    st.success("✅ Analysis complete")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Layers", results["activation_statistics"]["num_layers_analyzed"])
                    with col2:
                        st.metric("Sparsity", f"{results['activation_statistics']['avg_sparsity']:.3f}")
                    with col3:
                        st.metric("Specialized", len(results["activation_statistics"]["specialized_layers"]))
                    
                    if st.button("📥 Export"):
                        st.download_button(
                            "Download JSON",
                            json.dumps(results, indent=2, default=str),
                            f"sae_{model_id.replace('/', '_')}.json",
                            "application/json"
                        )
                    
                    del analyzer
                    torch.cuda.empty_cache()
                
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
    
    with tab6:
        st.markdown("## Master Log")
        st.markdown("Complete experiment timeline and decisions.")
        
        exp = st.session_state.current_experiment
        log_path = exp["paths"]["master_log"]
        
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                log_content = f.read()
            
            col1, col2 = st.columns([3, 1])
            with col2:
                st.download_button(
                    "📥 Download",
                    log_content,
                    f"{exp['name']}_master.log",
                    "text/plain"
                )
            
            st.code(log_content, language="log", line_numbers=False)
        else:
            st.info("Logs appear after first cycle.")

else:
    st.info("👈 Create a new mission or resume an existing one to begin.")
