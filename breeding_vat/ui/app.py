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
from typing import Optional, Dict, List, Any
import threading
import time
import math

from breeding_vat.modules.merge.advisor import MergeAdvisor
from breeding_vat.modules.merge.evolution import EvolutionEngine
from breeding_vat.modules.merge.merger import AdvancedMerger
from breeding_vat.modules.sae.scoped_analyzer import SAEScopedAnalyzer
from breeding_vat.modules.assay import ASSAYAnalyzer
from breeding_vat.modules.assay.visualizer import make_heatmap, make_constellation
from breeding_vat.modules.benchmark import ReceiptWriter
from breeding_vat.modules.experiment_manager import ExperimentManager
from breeding_vat.modules.evolution.evolution_with_logging import EvolutionWithLogging
from breeding_vat.modules.model_transfer import ModelTransfer
from breeding_vat.modules.recipe_executor import RecipeExecutor
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
    model_transfer = ModelTransfer(experiment_manager=exp_manager)
    return runner, exp_manager, merger, model_transfer

if 'runner' not in st.session_state:
    try:
        st.session_state.runner, st.session_state.exp_manager, st.session_state.merger, st.session_state.model_transfer = init_system()
    except Exception as e:
        st.error(f"System initialization failed: {e}")
        st.stop()

# Simulation Warning Banner (Must be after initialization)
if st.session_state.runner.simulation_mode:
    st.warning("⚠️ **SIMULATION MODE ACTIVE** — Docker tasks are emulated. Results are randomized and no actual models are merged.")
    st.markdown("""
    <div style="background-color: #ff4b4b22; border: 1px solid #ff4b4b; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
        <span style="color: #ff4b4b; font-weight: bold;">[DEV ONLY]</span>
        The system is running in simulation mode because <code>SIMULATION_MODE=true</code> is set.
        No GPU or Docker resources will be used.
    </div>
    """, unsafe_allow_html=True)

if 'advisor_history' not in st.session_state:
    st.session_state.advisor_history = []

if 'current_experiment' not in st.session_state:
    st.session_state.current_experiment = None

if 'evolution_log' not in st.session_state:
    st.session_state.evolution_log = []

if 'cycle_stats' not in st.session_state:
    st.session_state.cycle_stats = {"total_cycles": 0, "best_score": 0.0, "best_model": None}

if 'sae_results' not in st.session_state:
    st.session_state.sae_results = None

if 'frankenmerge_layer_assignment' not in st.session_state:
    st.session_state.frankenmerge_layer_assignment = None

if 'finetuning_config' not in st.session_state:
    st.session_state.finetuning_config = {'enabled': False}

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


def build_recipe_from_ui(
    exp_name: str,
    goal: str,
    base_models: List[str],
    merge_methods: List[str],
    num_cycles: int,
    culling_rate: int,
    eval_tier: str,
    skip_perplexity: bool,
    use_scope_filter: bool,
    ft_config: Optional[Dict] = None,
    method_params: Optional[Dict] = None,
    advanced_config: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Convert all UI sidebar values into the canonical recipe JSON that
    RecipeExecutor.validate() and build_evolution_config() expect.
    """
    method_params = method_params or {}

    methods_dict: Dict[str, Any] = {}
    for m in merge_methods:
        entry: Dict[str, Any] = {"enabled": True}
        if m in method_params:
            entry.update(method_params[m])
        methods_dict[m] = entry

    if ft_config and ft_config.get("enabled"):
        ft_block = {
            "enabled": True,
            "method":        ft_config.get("method", "lora"),
            "dataset":       ft_config.get("dataset", "synthetic_qa"),
            "num_epochs":    ft_config.get("num_epochs", 3),
            "batch_size":    ft_config.get("batch_size", 4),
            "learning_rate": ft_config.get("learning_rate", 1e-4),
            "lora_rank":     ft_config.get("lora_rank", 8),
            "lora_alpha":    ft_config.get("lora_alpha", 16),
            "per_cycle":     ft_config.get("per_cycle", True),
            "apply_to":      ft_config.get("apply_to", "best_model"),
        }
    else:
        ft_block = {"enabled": False}

    return {
        "metadata": {
            "name": exp_name,
            "goal": goal,
            "timestamp": datetime.now().isoformat(),
            "created_by": "streamlit_ui",
        },
        "evolution": {
            "base_models": base_models,
            "merge_methods": methods_dict,
            "num_cycles": num_cycles,
            "culling_rate": culling_rate,
        },
        "evaluation": {
            "tier": eval_tier,
            "skip_perplexity": skip_perplexity,
            "scope_prefilter": use_scope_filter,
        },
        "finetuning": ft_block,
        "assay": {"enabled": False},
        "sae":   {"enabled": False},
        "advanced": advanced_config or {},
    }


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
            key="exp_goal_input",
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
    
    st.markdown("### ⚙️ Merge Methods")
    
    # Categorize methods
    mergekit_methods = ["slerp", "ties", "dare", "moe", "rmm", "negmerge"]
    fusionbench_methods = [m for m in MERGING_METHODS.keys() if m not in mergekit_methods]
    
    st.caption("🔧 MergeKit (Weight Interpolation)")
    mergekit_selected = st.multiselect(
        "MergeKit methods",
        [m.upper() for m in mergekit_methods],
        default=["SLERP", "TIES"],
        help="Classical interpolation & weighted merging",
        key="mergekit_select",
        label_visibility="collapsed"
    )
    
    st.caption("🧠 FusionBench (Advanced Techniques)")
    fusionbench_selected = st.multiselect(
        "FusionBench methods",
        [m.upper() for m in fusionbench_methods],
        default=["TASK_ARITHMETIC", "REGMEAN"],
        help="Regression, voting, layer-wise, and advanced merging",
        key="fb_select",
        label_visibility="collapsed"
    )
    
    merge_methods = [m.lower() for m in (mergekit_selected + fusionbench_selected)]
    
    num_cycles = st.number_input("Cycles", 1, 100, 3, help="Evolution iterations")
    culling_rate = st.slider("Culling %", 0, 100, 50, help="% of population to eliminate")
    
# Fine-tuning strategy (only shown if enabled)
    with st.expander("🎯 Fine-tuning Strategy", expanded=False):
        ft_enabled = st.checkbox(
            "Enable between-cycle fine-tuning",
            value=False,
            help="Adapt best model each cycle to your data before moving to next cycle",
            key="ft_enabled_ck"
        )
        
        if ft_enabled:
            ft_col1, ft_col2 = st.columns(2)
            
            with ft_col1:
                ft_method = st.selectbox(
                    "Method",
                    ["lora", "qlora"],
                    help="LoRA: parameter-efficient | QLoRA: quantized (more VRAM-efficient)",
                    key="ft_method_sel"
                )
            
            with ft_col2:
                ft_dataset = st.selectbox(
                    "Dataset",
                    ["synthetic_qa", "benchmark_qa"],
                    help="synthetic_qa: AI-generated | benchmark_qa: your eval set",
                    key="ft_dataset_sel"
                )
            
            ft_col_a, ft_col_b, ft_col_c = st.columns(3)
            
            with ft_col_a:
                ft_epochs = st.slider(
                    "Epochs",
                    1, 20, 3,
                    help="Training passes",
                    key="ft_epochs"
                )
            
            with ft_col_b:
                ft_batch = st.slider(
                    "Batch size",
                    1, 32, 4,
                    help="Samples/step",
                    key="ft_batch"
                )
            
            with ft_col_c:
                ft_lr = st.select_slider(
                    "Learning rate",
                    options=[1e-5, 5e-5, 1e-4, 5e-4],
                    value=1e-4,
                    key="ft_lr"
                )
            
            if ft_method == "lora":
                ft_rank = st.slider(
                    "LoRA rank",
                    1, 32, 8,
                    help="Decomposition rank",
                    key="ft_lora_rank"
                )
                st.caption(f"LoRA config: rank={ft_rank}, alpha=16")
            else:
                ft_rank = 8
            
            st.session_state.finetuning_config = {
                'enabled': True,
                'method': ft_method,
                'dataset': ft_dataset,
                'num_epochs': ft_epochs,
                'batch_size': ft_batch,
                'learning_rate': ft_lr,
                'lora_rank': ft_rank,
                'lora_alpha': 16,
                'per_cycle': True,
                'apply_to': 'best_model'
            }
        else:
            st.session_state.finetuning_config = {'enabled': False}
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
        if st.session_state.frankenmerge_layer_assignment is not None:
            la = st.session_state.frankenmerge_layer_assignment
            src = st.session_state.get('frankenmerge_source_model', 'unknown').split('/')[-1]
            st.success(f"✅ SAE layer map active ({len(la)} layers from {src})")
            if st.button("🗑️ Clear SAE map", key="clear_fm_map"):
                st.session_state.frankenmerge_layer_assignment = None
                st.session_state.frankenmerge_source_model = None
                st.rerun()
        else:
            st.caption("No SAE layer map — run Analysis tab to generate one.")

    # ── 🧬 Advanced Presets (opt-in, orthogonal toggles) ────────────────
    # Each toggle composes with any merge method. Most map to native MergeKit
    # YAML (slices / filter / density / weight). A few are post-merge.
    # Reference: docs/reference/MERGING_METHODS_INVENTORY.md
    from breeding_vat.modules.merge.advanced_toggles import describe_toggle as _adv_help
    adv: Dict[str, Any] = {}
    with st.expander("🧬 Advanced Presets (Opt-in)", expanded=False):
        st.caption("Orthogonal toggles. Off by default. Each composes with any merge method.")

        # Per-tensor filtering
        st.markdown("**Per-tensor filtering**")
        if st.checkbox("Attn/MLP filter", help=_adv_help("attn_mlp_filter"),
                       key="adv_attnmlp"):
            c1, c2 = st.columns(2)
            with c1:
                ma = st.checkbox("Merge attention", value=True, key="adv_amlp_a")
                mm = st.checkbox("Merge MLP", value=True, key="adv_amlp_m")
            with c2:
                mn = st.checkbox("Merge norms", value=True, key="adv_amlp_n")
                me = st.checkbox("Merge embeddings", value=True, key="adv_amlp_e")
            mut = st.checkbox("Mutate across cycles", key="adv_amlp_mut")
            adv["attn_mlp_filter"] = {"enabled": True, "mutate": mut,
                "params": {"merge_attention": ma, "merge_mlp": mm,
                           "merge_norms": mn, "merge_embeddings": me}}

        if st.checkbox("Top-K sparsify", help=_adv_help("topk_sparsify"),
                       key="adv_topk"):
            kp = st.slider("Keep %", 1.0, 100.0, 10.0, 1.0, key="adv_topk_kp")
            mut = st.checkbox("Mutate across cycles", key="adv_topk_mut")
            adv["topk_sparsify"] = {"enabled": True, "mutate": mut,
                "params": {"keep_percent": kp}}

        if st.checkbox("Sign consensus mask", help=_adv_help("sign_consensus_mask"),
                       key="adv_sign"):
            sm = st.selectbox("Vote mode", ["majority", "unanimous", "weighted"],
                              key="adv_sign_mode")
            mut = st.checkbox("Mutate across cycles", key="adv_sign_mut")
            adv["sign_consensus_mask"] = {"enabled": True, "mutate": mut,
                "params": {"sign_mode": sm}}

        if st.checkbox("Embedding mode", help=_adv_help("embedding_mode"),
                       key="adv_emb"):
            em = st.selectbox("Mode", ["partial", "freeze", "full", "scaled"],
                              key="adv_emb_mode")
            mut = st.checkbox("Mutate across cycles", key="adv_emb_mut")
            adv["embedding_mode"] = {"enabled": True, "mutate": mut,
                "params": {"embedding_mode": em}}

        # Layer targeting
        st.markdown("---")
        st.markdown("**Layer targeting**")
        if st.checkbox("Layerwise alpha", help=_adv_help("layerwise_alpha"),
                       key="adv_law"):
            lm = st.selectbox("Curve",
                ["flat", "linear", "frontloaded", "backloaded",
                 "exponential", "sigmoid", "middle"], key="adv_law_mode")
            ba = st.slider("Base alpha", 0.0, 2.5, 1.0, 0.05, key="adv_law_alpha")
            ga = st.slider("Curve sharpness γ", 0.1, 8.0, 1.0, 0.1, key="adv_law_g")
            tl = st.number_input("Total layers", 1, 200, 32,
                                  help="Model depth — set to actual layer count",
                                  key="adv_law_tl")
            mut = st.checkbox("Mutate across cycles", key="adv_law_mut")
            adv["layerwise_alpha"] = {"enabled": True, "mutate": mut,
                "params": {"base_alpha": ba, "gamma": ga,
                           "layer_mode": lm, "total_layers": tl}}

        if st.checkbox("Alt-layer injection", help=_adv_help("alt_layer_inject"),
                       key="adv_alt"):
            ap = st.selectbox("Pattern",
                ["odd_even", "even_odd", "first_half", "second_half", "random"],
                key="adv_alt_p")
            mut = st.checkbox("Mutate across cycles", key="adv_alt_mut")
            adv["alt_layer_inject"] = {"enabled": True, "mutate": mut,
                "params": {"alt_pattern": ap}}

        if st.checkbox("Dynamic coefficient sample", help=_adv_help("dynamic_coef_sample"),
                       key="adv_dyn"):
            sc = st.selectbox("Scope", ["region", "layer", "tensor", "global"],
                              key="adv_dyn_s")
            lo = st.slider("α min", 0.0, 2.5, 0.1, 0.05, key="adv_dyn_lo")
            hi = st.slider("α max", 0.0, 2.5, 1.5, 0.05, key="adv_dyn_hi")
            mut = st.checkbox("Mutate across cycles", value=True, key="adv_dyn_mut",
                              help="Recommended ON — this toggle is built to mutate.")
            adv["dynamic_coef_sample"] = {"enabled": True, "mutate": mut,
                "params": {"coef_scope": sc, "alpha_min": lo, "alpha_max": hi}}

        # Evolution & diversity
        st.markdown("---")
        st.markdown("**Evolution & diversity**")
        if st.checkbox("Gaussian mutation", help=_adv_help("gaussian_mutation"),
                       key="adv_gm"):
            sg = st.select_slider("σ", options=[1e-5, 5e-5, 1e-4, 5e-4, 1e-3],
                                   value=1e-4, key="adv_gm_s")
            tg = st.selectbox("Target",
                ["all", "attention", "mlp", "embedding", "lora"], key="adv_gm_t")
            mut = st.checkbox("Mutate across cycles", key="adv_gm_mut")
            adv["gaussian_mutation"] = {"enabled": True, "mutate": mut,
                "params": {"mutation_sigma": float(sg), "mutation_target": tg}}

        if st.checkbox("Bench-weighted blend", help=_adv_help("bench_weighted_blend"),
                       key="adv_bw"):
            gw = st.slider("Sharpness γ", 0.5, 5.0, 2.0, 0.1, key="adv_bw_g")
            mut = st.checkbox("Mutate across cycles", key="adv_bw_mut")
            adv["bench_weighted_blend"] = {"enabled": True, "mutate": mut,
                "params": {"gamma": gw}}

        # Quality control
        st.markdown("---")
        st.markdown("**Quality control**")
        if st.checkbox("Cosine filter", help=_adv_help("cosine_filter"),
                       key="adv_cos"):
            ct = st.slider("Min cosine sim", -1.0, 1.0, 0.0, 0.05,
                            key="adv_cos_t")
            cm = st.selectbox("Mode",
                ["suppress", "keep_a", "keep_b", "report"], key="adv_cos_m")
            mut = st.checkbox("Mutate across cycles", key="adv_cos_mut")
            adv["cosine_filter"] = {"enabled": True, "mutate": mut,
                "params": {"similarity_threshold": ct, "cosine_mode": cm}}

        if st.checkbox("LoRA rank prune", help=_adv_help("lora_rank_prune"),
                       key="adv_lrp"):
            rr = st.slider("Retain rank %", 1.0, 100.0, 50.0, 1.0,
                            key="adv_lrp_r")
            mut = st.checkbox("Mutate across cycles", key="adv_lrp_mut")
            adv["lora_rank_prune"] = {"enabled": True, "mutate": mut,
                "params": {"retain_rank_percent": rr}}

        # Geometric
        st.markdown("---")
        st.markdown("**Geometric interpolation**")
        if st.checkbox("SLERP variant (nuSLERP)", help=_adv_help("slerp_variants"),
                       key="adv_sl"):
            sv = st.selectbox("Variant",
                ["linear", "slerp", "nuslerp"], key="adv_sl_v", index=2)
            tt = st.slider("Blend t", 0.0, 1.0, 0.5, 0.05, key="adv_sl_t")
            mut = st.checkbox("Mutate across cycles", key="adv_sl_mut")
            adv["slerp_variants"] = {"enabled": True, "mutate": mut,
                "params": {"slerp_variant": sv, "t": tt}}

    st.session_state.advanced_config = adv

    # Verification button — opt-in dry-run, no Docker, no models loaded.
    with st.expander("🔬 Verify advanced toggle wiring", expanded=False):
        st.caption("Dry-run: validates schema, executor handoff, YAML emitters, mutation routine. Safe to click anytime.")
        if st.button("Run verification", key="adv_verify_btn",
                     use_container_width=True):
            try:
                from scripts.verify_advanced_toggles import run_verification
                result = run_verification()
                if result["ok"]:
                    st.success(f"✅ All {len(result['steps'])} checks passed")
                else:
                    failed = sum(1 for _, p, _ in result["steps"] if not p)
                    st.error(f"❌ {failed} of {len(result['steps'])} checks failed")
                for label, passed, detail in result["steps"]:
                    icon = "✅" if passed else "❌"
                    st.markdown(f"{icon} **{label}** — {detail}")
            except Exception as e:
                st.error(f"Verification crashed: {e}")

    st.markdown("---")
    st.markdown("### 🤖 Advisor")

    # Resolve actual GGUF filename from zoo folder (download_models puts it there)
    def _find_gguf(zoo_name):
        zoo_path = os.path.join("breeding_vat/data/model_zoo", zoo_name)
        if os.path.isdir(zoo_path):
            files = [f for f in os.listdir(zoo_path) if f.endswith(".gguf")]
            if files:
                return os.path.join(zoo_path, sorted(files)[0])
        return None

    _gguf_quick    = _find_gguf("Qwen3.5-0.8B-Reasoning-GGUF")
    _gguf_advanced = _find_gguf("qwen-ai-research-qa-q4_k_m.gguf") or \
                     "breeding_vat/data/GGUF Models/qwen-ai-research-qa-q4_k_m.gguf/qwen-ai-research-qa-q4_k_m.gguf"

    _advisor_options = ["Qwen/Qwen2.5-1.5B-Instruct"]
    if _gguf_quick:
        _advisor_options.insert(0, _gguf_quick)
    if _gguf_advanced and os.path.exists(_gguf_advanced):
        _advisor_options.append(_gguf_advanced)
    _advisor_options.append("Qwen/Qwen2.5-0.5B-Instruct")

    advisor_model = st.selectbox(
        "Advisor model",
        _advisor_options,
        format_func=lambda x: (
            "[GGUF] Qwen3.5-0.8B Reasoning (quick)"   if "0.8B-Reasoning" in x or "0.8B-Claude" in x else
            "[GGUF] Qwen2.5-3B Research QA (advanced)" if "research-qa"    in x else
            x.split("/")[-1]
        ),
        help="AI guide for recipe suggestions"
    )

    use_laser_rag = st.checkbox(
        "LaSER semantic KB search",
        value=False,
        help="Use LaSER-Qwen3-4B embeddings for semantic KB retrieval (first run builds an index cache)"
    )

    # Suggest button reads mission goal from session state
    current_goal = st.session_state.get("exp_goal_input", "")
    if st.button("💡 Suggest methods & models", use_container_width=True,
                 help="Generate method/model suggestions from the mission goal"):
        if not current_goal.strip():
            st.warning("Type a mission goal first (Mission Control → New Mission)")
        else:
            with st.spinner("Generating suggestions..."):
                try:
                    adv = MergeAdvisor(model_id=advisor_model)
                    suggestion = adv.generate_recipes(
                        goal=current_goal,
                        base_models=MODEL_ZOO[:6],
                        methods=list(MERGING_METHODS.keys())[:4],
                        num_variants_per_method=1,
                        use_laser_rag=use_laser_rag,
                    )
                    st.session_state.goal_suggestions = suggestion["advisory_note"]
                    if hasattr(adv, 'model'):
                        del adv.model
                    torch.cuda.empty_cache()
                except Exception as e:
                    st.session_state.goal_suggestions = f"Suggestion failed: {e}"

    if st.session_state.get("goal_suggestions"):
        with st.expander("💡 Suggestions", expanded=True):
            st.markdown(st.session_state.goal_suggestions)

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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        ["🧪 Evolution", "🌳 Lineage", "🧠 SAE", "🔬 Methods", "📊 Analysis", "📋 Logs", "⚗️ ASSAY"]
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
                            recipe = advisor.generate_recipe(exp['goal'], base_models, merge_methods)
                            
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

        use_scope_filter = st.checkbox(
            "SCOPE pre-filter",
            value=False,
            help=(
                "Run each merged model through 3 coherence test prompts before lm-eval. "
                "Catches completely broken merges in seconds, saving minutes of eval time."
            ),
        )

        with st.expander("Benchmark tier", expanded=False):
            eval_tier = st.radio(
                "Evaluation depth",
                options=["fast", "standard", "full"],
                index=1,
                horizontal=True,
                help=(
                    "fast: arc_easy (~2 min) | "
                    "standard: hellaswag + arc_challenge (~10 min) | "
                    "full: + winogrande + truthfulqa_mc (~30 min)"
                ),
                key="eval_tier_radio",
            )
            skip_perplexity = st.checkbox(
                "Skip perplexity gate (Tier 0)",
                value=False,
                help=(
                    "Tier 0 runs a ~15 s perplexity check and rejects models scoring > 1000. "
                    "Disable only when iterating quickly and you trust the merge won't be broken."
                ),
                key="skip_perplexity_ck",
            )

        # Run evolution
        if st.button("▶️ START EVOLUTION", type="primary", use_container_width=True, key="evo_run"):
            if len(base_models) < 2:
                st.error("Select 2+ base models")
            elif not merge_methods:
                st.error("Select at least one merge method")
            else:
                exp = st.session_state.current_experiment

                # --- Collect per-method params from sidebar locals ---
                method_params = {
                    "dare":            {"drop_rate": dare_drop},
                    "dare_ties":       {"drop_rate": dare_drop},
                    "dare_linear":     {"drop_rate": dare_drop},
                    "ties":            {"threshold": ties_thresh},
                    "ties_linear":     {"threshold": ties_thresh},
                    "task_arithmetic": {"reg": ta_reg},
                    "regmean":         {"reg": rm_reg},
                    "voting":          {"voting_method": vote_method},
                    "magnitude_prune": {"prune_ratio": prune_ratio},
                    "frankenmerge":    {"rank": fm_rank},
                }

                # --- Build recipe JSON from all UI state ---
                recipe = build_recipe_from_ui(
                    exp_name=exp["name"],
                    goal=exp["goal"],
                    base_models=base_models,
                    merge_methods=merge_methods,
                    num_cycles=num_cycles,
                    culling_rate=culling_rate,
                    eval_tier=eval_tier,
                    skip_perplexity=skip_perplexity,
                    use_scope_filter=use_scope_filter,
                    ft_config=st.session_state.finetuning_config,
                    method_params=method_params,
                    advanced_config=st.session_state.get("advanced_config", {}),
                )

                # --- Validate recipe before touching the engine ---
                executor = RecipeExecutor()
                validation = executor.validate(recipe)

                if not validation.valid:
                    for err in validation.errors:
                        st.error(f"Recipe error: {err}")
                    for warn in validation.warnings:
                        st.warning(f"Recipe warning: {warn}")
                    st.stop()

                if validation.warnings:
                    for warn in validation.warnings:
                        st.warning(f"Recipe warning: {warn}")

                # --- Extract validated engine config ---
                evo_config = executor.build_evolution_config(recipe)

                # --- Persist recipe to experiment folder ---
                try:
                    recipe_path = os.path.join(exp["paths"]["configs"], "evolution_recipe.json")
                    os.makedirs(exp["paths"]["configs"], exist_ok=True)
                    with open(recipe_path, "w") as f:
                        json.dump(recipe, f, indent=2, default=str)
                except Exception as save_err:
                    logger.warning(f"Could not save recipe file: {save_err}")

                # --- Update experiment metadata from validated config ---
                exp["base_models"] = evo_config["base_models"]
                exp["merge_methods"] = evo_config["merge_methods"]
                exp["num_cycles_planned"] = evo_config["num_cycles"]
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

                    log_to_ui("Recipe validated ✓", "success")
                    log_to_ui(f"Starting evolution: {evo_config['num_cycles']} cycles", "success")
                    log_to_ui(f"Methods: {', '.join(evo_config['merge_methods'])}", "debug")
                    log_to_ui(f"Models: {', '.join([m.split('/')[-1] for m in evo_config['base_models']])}", "debug")

                    update_progress(progress_placeholder, log_container, metrics_container,
                                    0, evo_config["num_cycles"], "Initializing evolution engine...",
                                    best_score=exp["best_score"])

                    base_evo = EvolutionEngine(st.session_state.runner)
                    base_evo.eval_tier       = evo_config["eval_tier"]
                    base_evo.skip_perplexity = evo_config["skip_perplexity"]
                    base_evo.method_params   = evo_config.get("method_params", {})
                    base_evo.advanced        = evo_config.get("advanced", {})
                    if base_evo.advanced:
                        log_to_ui(f"Advanced toggles enabled: {', '.join(base_evo.advanced.keys())}", "debug")
                    log_to_ui(f"Benchmark tier: {evo_config['eval_tier']} | perplexity gate: {'off' if evo_config['skip_perplexity'] else 'on'}", "debug")

                    if evo_config.get("scope_prefilter"):
                        from breeding_vat.modules.benchmark.scope_filter import SCOPEFilter
                        base_evo.scope_filter = SCOPEFilter(st.session_state.runner)
                        log_to_ui("SCOPE pre-filter enabled — broken merges will be skipped", "info")

                    if st.session_state.frankenmerge_layer_assignment is not None:
                        base_evo.frankenmerge_layer_assignment = st.session_state.frankenmerge_layer_assignment
                        src = st.session_state.get("frankenmerge_source_model", "unknown")
                        log_to_ui(f"SAE layer map active ({src.split('/')[-1]})", "info")

                    evo_logged = EvolutionWithLogging(
                        evolution_engine=base_evo,
                        experiment_manager=st.session_state.exp_manager,
                        experiment=exp,
                        progress_callback=progress_callback
                    )

                    best_model = evo_logged.run_waterfall(
                        base_models=evo_config["base_models"],
                        goal=exp["goal"],
                        num_cycles=evo_config["num_cycles"],
                        culling_rate=evo_config["culling_rate"],
                        allowed_methods=evo_config["merge_methods"],
                        resume_from_cycle=exp["cycles_completed"]
                    )

                    # Update stats
                    improvement = ((best_model["score"] - exp["best_score"]) / (exp["best_score"] + 1e-8)) * 100
                    excitement = get_excitement(improvement, is_new_best=best_model["score"] > exp["best_score"])

                    log_to_ui("Evolution complete!", "success")
                    log_to_ui(f"Best model: {best_model['name']}", "success")
                    log_to_ui(f"Final score: {format_benchmark_result(best_model['score'], exp['best_score'])}", "success")
                    log_to_ui(excitement, "success")

                    st.session_state.cycle_stats = {
                        "total_cycles": evo_config["num_cycles"],
                        "best_score": best_model["score"],
                        "best_model": best_model["name"],
                    }

                    update_progress(progress_placeholder, log_container, metrics_container,
                                    evo_config["num_cycles"], evo_config["num_cycles"], "✅ Complete",
                                    best_score=best_model["score"])

                    st.markdown("---")
                    st.markdown(f"### {excitement}")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Best Score", f"{best_model['score']:.4f}")
                    with col2:
                        st.metric("Best Model", best_model["name"][-25:])
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
            genealogy_file = None
            for candidate in [
                benchmark_db_path,
                os.path.join(exp["paths"]["results"], "benchmarks.json"),
                os.path.join(exp["paths"]["root"], "benchmarks.json")
            ]:
                if candidate and os.path.exists(candidate):
                    genealogy_file = candidate
                    break

            if genealogy_file:
                with open(genealogy_file, 'r') as f:
                    benchmarks = json.load(f)

                if benchmarks.get("cycles"):
                    import pandas as pd

                    rows = []
                    all_anomalies = []

                    for cycle_data in benchmarks["cycles"]:
                        for model in cycle_data.get("models", []):
                            parents = model.get("parents", [])
                            parent_names = " + ".join([p.split("/")[-1][-15:] for p in parents]) if parents else "base"
                            anomaly_count = len(model.get("anomalies", []))

                            rows.append({
                                "Cycle": cycle_data["cycle"],
                                "Model": model["name"][-32:],
                                "Score": model.get("score", 0),
                                "Method": model.get("method", "?").upper(),
                                "Parents": parent_names,
                                "Anomalies": anomaly_count
                            })

                            for anom in model.get("anomalies", []):
                                all_anomalies.append({
                                    "model": model["name"],
                                    "type": anom.get("type", "unknown"),
                                    "detail": anom.get("detail", "")
                                })

                    if rows:
                        df = pd.DataFrame(rows)

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Models", len(rows))
                        with col2:
                            st.metric("Best Score", f"{df['Score'].max():.4f}")
                        with col3:
                            st.metric("Avg Score", f"{df['Score'].mean():.4f}")
                        with col4:
                            st.metric("Cycles", len(benchmarks["cycles"]))

                        st.markdown("---")

                        st.markdown("### Genealogy Table")
                        st.dataframe(
                            df.sort_values("Score", ascending=False),
                            use_container_width=True,
                            hide_index=True
                        )

                        st.markdown("### Score Progression")
                        best_per_cycle = df.groupby("Cycle")["Score"].max()
                        st.line_chart(best_per_cycle, use_container_width=True)

                        st.markdown("### Anomalies Detected")
                        anomaly_per_cycle = df.groupby("Cycle")["Anomalies"].sum()
                        st.bar_chart(anomaly_per_cycle, use_container_width=True)

                        if not df.empty:
                            st.markdown("### Methods Used")
                            method_counts = df["Method"].value_counts()
                            st.bar_chart(method_counts, use_container_width=True)

                        if all_anomalies:
                            st.markdown("---")
                            st.markdown("### Anomaly Details")
                            anomaly_df = pd.DataFrame(all_anomalies)
                            anomaly_summary = anomaly_df["type"].value_counts()
                            st.markdown(f"**Total anomalies detected**: {len(all_anomalies)}")
                            st.bar_chart(anomaly_summary, use_container_width=True)
                            for anom_type in anomaly_df["type"].unique():
                                with st.expander(f"🔍 {anom_type.upper()}", expanded=False):
                                    type_anomalies = anomaly_df[anomaly_df["type"] == anom_type]
                                    for _, row in type_anomalies.iterrows():
                                        st.warning(f"**{row['model']}**: {row['detail']}")
                    else:
                        st.info("Evolution completed but no models kept.")
                else:
                    st.info("No cycles completed yet. Run evolution to populate genealogy.")
            else:
                st.info("Genealogy data not available yet.")
        except Exception as e:
            st.error(f"Lineage error: {e}")

        st.markdown("---")
        st.markdown("### Model Receipts")

        exp = st.session_state.current_experiment
        receipt_writer = ReceiptWriter(exp["paths"]["root"])
        receipts = receipt_writer.list_receipts()

        if not receipts:
            st.info("No receipts yet. Receipts are generated automatically after each merge cycle completes.")
        else:
            # Sort by locked_at descending
            receipts_sorted = sorted(receipts, key=lambda r: r.get("locked_at", ""), reverse=True)

            for receipt in receipts_sorted:
                model_name = receipt.get("model_name", "unknown")
                locked_at = receipt.get("locked_at", "")[:16].replace("T", " ")
                gen = receipt.get("general_benchmark", {})
                goal = receipt.get("goal_benchmark", {})
                anomalies = receipt.get("anomalies", [])

                # Anomaly indicator
                anomaly_badge = " ⚠️" if anomalies else ""

                with st.expander(f"{model_name}  —  locked {locked_at}{anomaly_badge}"):
                    col_g, col_b = st.columns(2)

                    with col_g:
                        st.markdown("**Goal Benchmark**")
                        st.metric("Scaled Score", f"{goal.get('scaled_score', 0):.1f}/100")
                        st.caption(f"Task: {goal.get('task', 'N/A')}  |  Raw: {goal.get('raw_score', 0):.3f}")

                    with col_b:
                        st.markdown("**General Benchmark**")
                        st.metric("Scaled Score", f"{gen.get('scaled_score', 0):.1f}/100")
                        st.caption(f"Q attempted: {gen.get('questions_attempted', 0)}  |  Correct: {gen.get('questions_correct', 0)}  |  Stopped at Q{gen.get('stopped_at', '?')}")

                    if anomalies:
                        st.markdown("**Anomalies**")
                        for a in anomalies:
                            st.warning(f"[{a.get('type','?')}] {a.get('detail','')}")

                    recipe = receipt.get("merge_recipe", {})
                    if recipe:
                        st.markdown("**Merge Recipe**")
                        st.json(recipe)

                    st.download_button(
                        "📥 Download Receipt",
                        data=json.dumps(receipt, indent=2, default=str),
                        file_name=f"{model_name}_receipt.json",
                        mime="application/json",
                        key=f"receipt_dl_{model_name}"
                    )

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
            sae_model_id = st.text_input("Model", "gpt2", key="sae_model_input")
        with col2:
            compare_with = st.text_input("Compare (optional)", "")

        if st.button("🔬 Analyze", type="primary"):
            with st.spinner("Analyzing model internals..."):
                try:
                    analyzer = SAEScopedAnalyzer(sae_model_id, vram_gb=vram_gb)
                    results = analyzer.analyze_self(num_samples=num_samples, num_layers=num_layers)
                    st.session_state.sae_results = results
                    st.session_state.sae_analyzed_model = sae_model_id
                    del analyzer
                    torch.cuda.empty_cache()
                    st.success("✅ Analysis complete")
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

        # Results panel — persists across re-runs via session_state
        if st.session_state.sae_results is not None:
            results = st.session_state.sae_results
            analyzed_model = st.session_state.get("sae_analyzed_model", "unknown")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Layers analysed", results["activation_statistics"]["num_layers_analyzed"])
            with col2:
                st.metric("Avg sparsity", f"{results['activation_statistics']['avg_sparsity']:.3f}")
            with col3:
                st.metric("Specialized layers", len(results["activation_statistics"]["specialized_layers"]))

            st.download_button(
                "📥 Download JSON",
                json.dumps(results, indent=2, default=str),
                f"sae_{analyzed_model.replace('/', '_')}.json",
                "application/json",
            )

            # --- Frankenmerge bridge ---
            st.markdown("---")
            st.markdown("### 📐 Use for Frankenmerge")
            st.caption(
                "Convert SAE specialization data into a layer-assignment dict "
                "for Frankenmerge. Run SAE on each parent model, then build assignments."
            )

            specialized_layers = results["activation_statistics"].get("specialized_layers", [])
            total_layers = results["activation_statistics"]["num_layers_analyzed"]

            col1, col2 = st.columns(2)
            with col1:
                fm_this_idx = st.number_input(
                    "This model's merge index",
                    min_value=0, max_value=9, value=0,
                    help="0 = first model selected in Evolution tab, 1 = second, etc."
                )
            with col2:
                fm_other_idx = st.number_input(
                    "Fallback model index",
                    min_value=0, max_value=9, value=1,
                    help="Which model supplies non-specialized layers"
                )

            if specialized_layers:
                st.info(
                    f"Detected {len(specialized_layers)} specialized layers "
                    f"(indices: {sorted(specialized_layers)[:10]}{'…' if len(specialized_layers) > 10 else ''})"
                )
            else:
                st.warning("No specialized layers detected — all layers will use the fallback model.")

            if st.button("📐 Build & activate layer assignment", type="secondary"):
                layer_assignment = {}
                for i in range(total_layers):
                    layer_assignment[str(i)] = int(fm_this_idx) if i in specialized_layers else int(fm_other_idx)
                st.session_state.frankenmerge_layer_assignment = layer_assignment
                st.session_state.frankenmerge_source_model = analyzed_model
                st.success(
                    f"✅ Layer map saved: {len(specialized_layers)} layers → model {fm_this_idx}, "
                    f"{total_layers - len(specialized_layers)} layers → model {fm_other_idx}. "
                    "Select FRANKENMERGE in the sidebar to use it."
                )
                with st.expander("Layer assignment preview"):
                    st.json(layer_assignment)
    
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

    with tab7:
        st.markdown("## ⚗️ ASSAY — Activation Layer Analysis")
        st.markdown("Probe a model across question styles to build a layer quality map for merge and fine-tune planning.")

        # --- Model picker: scan model_zoo for local models ---
        _zoo_path = os.path.join("breeding_vat", "data", "model_zoo")
        _local_assay_models = []
        if os.path.isdir(_zoo_path):
            _local_assay_models = [
                os.path.join(_zoo_path, d)
                for d in os.listdir(_zoo_path)
                if os.path.isdir(os.path.join(_zoo_path, d))
            ]

        col_cfg, col_run = st.columns([2, 1])

        with col_cfg:
            assay_topic = st.text_input(
                "Topic / Domain",
                placeholder="e.g. model merging, math reasoning, code generation",
                key="assay_topic_input"
            )

            assay_model = st.selectbox(
                "Model to probe",
                options=_local_assay_models if _local_assay_models else ["(no local models found)"],
                format_func=lambda p: os.path.basename(p),
                key="assay_model_select"
            )

            col_s1, col_s2 = st.columns(2)
            with col_s1:
                assay_n_mini = st.slider("Questions per mini-round", 6, 20, 12, key="assay_n_mini")
            with col_s2:
                assay_n_full = st.slider("Full-run questions", 20, 100, 50, key="assay_n_full")

        with col_run:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            run_assay = st.button("▶ Run ASSAY", type="primary", key="assay_run_btn",
                                  disabled=not assay_topic or "(no local" in str(assay_model))

        if run_assay:
            assay_log = st.empty()
            assay_progress = st.progress(0)
            _assay_messages = []

            def _assay_cb(msg):
                _assay_messages.append(msg)
                assay_log.code("\n".join(_assay_messages[-8:]), language="log")

            try:
                analyzer = ASSAYAnalyzer(model_path=assay_model, vram_gb=8)
                _assay_cb("Loading model...")
                results = analyzer.run(
                    topic=assay_topic,
                    n_mini=assay_n_mini,
                    n_full=assay_n_full,
                    progress_callback=_assay_cb
                )
                assay_progress.progress(100)
                st.session_state.assay_results = results
                assay_log.success(f"ASSAY complete. Winner: **{results['winning_strategy']}** | Signal layers: {results['signal_layers']}")
            except Exception as e:
                assay_log.error(f"ASSAY failed: {e}")

        # --- Results display ---
        if "assay_results" in st.session_state and st.session_state.assay_results:
            res = st.session_state.assay_results
            import numpy as np

            st.markdown("---")
            st.markdown(f"**Topic:** {res['topic']} &nbsp;|&nbsp; **Strategy:** {res['winning_strategy']} &nbsp;|&nbsp; **Questions:** {res['n_questions']}")

            qc = res.get("quality_counts", {})
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Great", qc.get("great", 0))
            mc2.metric("Acceptable", qc.get("acceptable", 0))
            mc3.metric("Wrong", qc.get("wrong", 0))
            mc4.metric("Hallucinated", qc.get("hallucinated", 0))

            viz_col1, viz_col2 = st.columns(2)

            with viz_col1:
                st.markdown("### Layer Heatmap")
                try:
                    fig_heat = make_heatmap(res["layer_stats"], res["topic"], res["winning_strategy"])
                    st.plotly_chart(fig_heat, use_container_width=True)
                except Exception as e:
                    st.warning(f"Heatmap error: {e}")

            with viz_col2:
                st.markdown("### Constellation")
                try:
                    _vecs = {int(k): np.array(v) for k, v in res["layer_vectors"].items()} if res.get("layer_vectors") else {}
                    fig_const = make_constellation(res["layer_stats"], _vecs, res["topic"])
                    st.plotly_chart(fig_const, use_container_width=True)
                except Exception as e:
                    st.warning(f"Constellation error: {e}")

            st.markdown("---")
            act_col1, act_col2, act_col3 = st.columns(3)

            with act_col1:
                if st.button("🔀 Send to Merge", key="assay_send_merge"):
                    assignment = {
                        layer: 0
                        for layer in res.get("signal_layers", [])
                    }
                    st.session_state.frankenmerge_layer_assignment = assignment
                    st.success(f"Frankenmerge assignment set: {len(assignment)} signal layers → model 0")

            with act_col2:
                if st.button("🎯 Send to Fine-tune", key="assay_send_ft"):
                    st.session_state.assay_lora_targets = {
                        "signal_layers": res.get("signal_layers", []),
                        "instability_layers": res.get("instability_layers", []),
                        "topic": res["topic"],
                        "strategy": res["winning_strategy"],
                    }
                    st.success("LoRA targets saved to session state.")

            with act_col3:
                st.download_button(
                    "📥 Export JSON",
                    data=json.dumps(res, indent=2, default=str),
                    file_name=f"assay_{res['topic'][:20].replace(' ','_')}.json",
                    mime="application/json",
                    key="assay_export"
                )

            with st.expander("Strategy Scores"):
                for s, score in res.get("strategy_scores", {}).items():
                    st.markdown(f"**{s}**: {score:.4f}")

            with st.expander("Signal & Instability Layers"):
                st.markdown(f"**Signal layers** (high contrast): `{res.get('signal_layers', [])}`")
                st.markdown(f"**Instability layers** (hallucination-dominant): `{res.get('instability_layers', [])}`")

else:
    st.info("👈 Create a new mission or resume an existing one to begin.")
