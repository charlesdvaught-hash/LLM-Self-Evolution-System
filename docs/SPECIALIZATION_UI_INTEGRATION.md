"""
UI Integration Guide - How to add Specialization to Streamlit app.py

This shows the exact code sections to add for optional pre-specialization.
"""

# ============================================================================
# SECTION 1: Add imports at top of app.py
# ============================================================================

# After existing imports, add:
from breeding_vat.modules.specialize.advisor import SpecializationAdvisor
from breeding_vat.modules.specialize.orchestrator import SpecializationOrchestrator


# ============================================================================
# SECTION 2: Initialize in sidebar (after method parameters)
# ============================================================================

# In sidebar, add new section after "Method Parameters":

    st.markdown("---")
    st.markdown("### 🎯 Pre-Specialization (Optional)")
    
    # Get advisor recommendation based on selected methods
    if merge_methods:
        recommendation = SpecializationAdvisor.get_recommendation(
            merge_methods=merge_methods,
            goal=exp_goal,
            num_models=len(base_models) if base_models else 1,
            time_budget_minutes=120
        )
        
        # Display recommendation
        rec_level = recommendation.get("overall_recommendation", "SKIP")
        
        if rec_level == "MANDATORY":
            st.warning(
                f"🔴 **MANDATORY**: {recommendation['reasoning']}\n\n"
                f"Methods requiring specialization: "
                f"{', '.join([m.upper() for m, info in recommendation['methods_analysis'].items() if info.get('recommendation') == 'MANDATORY'])}"
            )
            enable_specialize = True
            default_strategy = recommendation.get("suggested_strategy", "task_lora")
        elif rec_level == "RECOMMENDED":
            st.info(
                f"🟡 **RECOMMENDED**: {recommendation['reasoning']}\n\n"
                f"Time estimate: {recommendation['time_estimate_minutes']} min"
            )
            enable_specialize = st.checkbox("Enable pre-specialization", value=False)
            default_strategy = recommendation.get("suggested_strategy", "task_lora")
        elif rec_level == "OPTIONAL":
            st.info(
                f"🟢 **OPTIONAL**: {recommendation['reasoning']}"
            )
            enable_specialize = st.checkbox("Enable pre-specialization", value=False)
            default_strategy = recommendation.get("suggested_strategy", "task_lora")
        else:  # SKIP
            st.success(
                f"✅ **SKIP**: {recommendation['reasoning']}"
            )
            enable_specialize = False
            default_strategy = "none"
        
        # Show method-by-method breakdown
        with st.expander("📊 Method Analysis"):
            for method, info in recommendation['methods_analysis'].items():
                emoji = {
                    "MANDATORY": "🔴",
                    "RECOMMENDED": "🟡",
                    "OPTIONAL": "🟢",
                    "NOT_RECOMMENDED": "⚪"
                }.get(info.get("recommendation"), "❓")
                
                st.markdown(
                    f"**{emoji} {method.upper()}**: {info.get('recommendation')}\n\n"
                    f"{info.get('reason')}"
                )
        
        # Configuration section
        if enable_specialize or rec_level == "MANDATORY":
            st.markdown("#### Configuration")
            
            strategy = st.selectbox(
                "Specialization strategy",
                ["task_lora", "curriculum", "sae_guided"],
                index=["task_lora", "curriculum", "sae_guided"].index(default_strategy)
                if default_strategy in ["task_lora", "curriculum", "sae_guided"] else 0,
                help="Pre-tuning method for base models"
            )
            
            # Strategy details
            strategy_info = SpecializationAdvisor.STRATEGIES.get(strategy, {})
            with st.expander("ℹ️ Strategy Details", expanded=False):
                st.markdown(f"**Description**: {strategy_info.get('description')}")
                st.markdown(f"**Compute cost**: {strategy_info.get('compute_cost')}")
                st.markdown(f"**Time estimate**: {strategy_info.get('time_estimate')}")
                st.markdown(f"**Data requirement**: {strategy_info.get('data_requirement')}")
            
            # Data source
            data_source = st.text_input(
                "Task data source",
                placeholder="hf:wikitext | /path/to/data.json | (leave blank for synthetic)",
                help="HuggingFace dataset (hf:ID), local file, or synthetic from goal"
            )
            
            # Strategy-specific parameters
            if strategy == "task_lora":
                lora_rank = st.slider("LoRA rank", 4, 64, 8, help="Low-rank decomposition size")
                num_samples = st.slider("Samples for tuning", 50, 500, 100, help="Examples to fine-tune on")
            
            elif strategy == "curriculum":
                num_samples = st.slider("Samples per phase", 100, 1000, 300, help="Easy/Medium/Hard each")
                st.info("Curriculum: Progressive training through 3 phases (easy → medium → hard)")
            
            elif strategy == "sae_guided":
                num_samples = st.slider("Samples for SAE", 20, 100, 50, help="Examples for layer discovery")
                st.info("SAE-guided: Identify specialized layers, then prompt-tune only those")
            
            # Validate configuration
            is_valid, validation_msg = SpecializationAdvisor.validate_specialization_config(
                strategy=strategy,
                data_source=data_source,
                num_models=len(base_models) if base_models else 1,
                time_budget_minutes=120
            )
            
            if is_valid:
                st.success(f"✅ {validation_msg}")
            else:
                st.error(f"⚠️ {validation_msg}")
                enable_specialize = False


# ============================================================================
# SECTION 3: Modify START EVOLUTION button to run specialization first
# ============================================================================

# Replace the existing "START EVOLUTION" button block with:

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
            st.subheader("🚀 Evolution Pipeline")
            
            progress_placeholder = st.empty()
            metrics_container = st.empty()
            log_container = st.container()
            log_container.markdown("### 📜 Pipeline Log")
            
            try:
                def progress_callback(current, total, status):
                    update_progress(
                        progress_placeholder, log_container, metrics_container,
                        current, total, status,
                        current_score=st.session_state.cycle_stats.get("best_score"),
                        best_score=st.session_state.cycle_stats.get("best_score")
                    )
                
                log_to_ui(f"Starting evolution pipeline: {num_cycles} cycles", "success")
                
                # ===== PHASE 0: OPTIONAL PRE-SPECIALIZATION =====
                active_models = base_models
                
                if enable_specialize and rec_level != "SKIP":
                    log_to_ui(f"Phase 0: Pre-specialization ({strategy})", "info")
                    update_progress(progress_placeholder, log_container, metrics_container,
                                  0, num_cycles, f"Pre-specializing with {strategy}...",
                                  best_score=exp['best_score'])
                    
                    orchestrator = SpecializationOrchestrator(
                        st.session_state.runner,
                        st.session_state.exp_manager
                    )
                    
                    def spec_progress(current, total, status):
                        log_to_ui(f"  {status}", "debug")
                    
                    success, specialized_models, spec_metadata = orchestrator.run_optional_specialization(
                        experiment=exp,
                        base_models=base_models,
                        strategy=strategy,
                        goal=exp['goal'],
                        data_source=data_source,
                        num_samples=num_samples,
                        progress_callback=spec_progress
                    )
                    
                    if success:
                        log_to_ui(f"✅ Specialization complete: {len(specialized_models)} models ready", "success")
                        active_models = specialized_models
                        # Save specialization info
                        exp['specialization'] = {
                            "strategy": strategy,
                            "models": specialized_models,
                            "metadata": spec_metadata
                        }
                    else:
                        log_to_ui(f"⚠️ Specialization failed: {spec_metadata.get('error', 'Unknown')}, using original models", "warning")
                        active_models = base_models
                else:
                    log_to_ui(f"Skipping pre-specialization (not needed for these methods)", "debug")
                
                # ===== PHASE 1: MERGE/EVAL/CULL EVOLUTION =====
                log_to_ui(f"Phase 1: Merge → Evaluate → Cull (using {len(active_models)} models)", "info")
                
                base_evo = EvolutionEngine(st.session_state.runner)
                
                evo_logged = EvolutionWithLogging(
                    evolution_engine=base_evo,
                    experiment_manager=st.session_state.exp_manager,
                    experiment=exp,
                    progress_callback=progress_callback
                )
                
                best_model = evo_logged.run_waterfall(
                    base_models=active_models,  # Use specialized or original models
                    goal=exp['goal'],
                    num_cycles=num_cycles,
                    culling_rate=culling_rate,
                    allowed_methods=merge_methods,
                    resume_from_cycle=exp['cycles_completed']
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
                log_to_ui(f"Pipeline failed: {str(e)}", "error")
                st.error(f"❌ Failed: {e}")
                logger.error(f"Pipeline error: {e}")


# ============================================================================
# SECTION 4: Add tab for Specialization history
# ============================================================================

# In main tabs, add before "Logs":

    with tab_spec:
        st.markdown("## Specialization History")
        st.markdown("Pre-tuning experiments and their outcomes.")
        
        spec_dir = "breeding_vat/data/specializations"
        if os.path.exists(spec_dir):
            spec_batches = []
            for batch_name in os.listdir(spec_dir):
                batch_file = os.path.join(spec_dir, batch_name, "specialization_batch.json")
                if os.path.exists(batch_file):
                    with open(batch_file, 'r') as f:
                        batch_info = json.load(f)
                    spec_batches.append((batch_name, batch_info))
            
            if spec_batches:
                for batch_name, batch_info in reversed(spec_batches):
                    with st.expander(
                        f"{batch_info['strategy'].upper()} — {batch_info['status']} "
                        f"({len(batch_info['specialized_models'])} models)"
                    ):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Strategy", batch_info['strategy'])
                        with col2:
                            st.metric("Status", batch_info['status'])
                        with col3:
                            st.metric("Models", len(batch_info['specialized_models']))
                        
                        st.markdown("**Specializations**")
                        for spec in batch_info['specialized_models']:
                            st.code(f"{spec['original']} → {spec['specialized']}", language=None)
            else:
                st.info("No specialization experiments yet.")
        else:
            st.info("No specialization experiments yet.")


# ============================================================================
# SECTION 5: Update main tabs line to include new tab
# ============================================================================

# Change from:
#     tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(...)
# To:
#     tab1, tab2, tab3, tab4, tab5, tab_spec, tab6 = st.tabs(
#         ["🧪 Evolution", "🌳 Lineage", "🧠 SAE", "🔬 Methods", "📊 Analysis", "📋 Specialization", "📋 Logs"]
#     )


# ============================================================================
# SUMMARY OF CHANGES
# ============================================================================
"""
Modifications to app.py:

1. Add 2 imports at top
2. Add UI section in sidebar for specialization config (MANDATORY/RECOMMENDED/OPTIONAL display)
3. Modify START EVOLUTION to call orchestrator.run_optional_specialization() first
4. Add new Specialization History tab
5. Update tab definitions

Key features:
✅ Context-aware recommendation (shows why specialization is needed or not)
✅ User approval/opt-out (MANDATORY forces it, RECOMMENDED asks, OPTIONAL/SKIP skips)
✅ Strategy selection (LoRA, Curriculum, SAE-guided)
✅ Data source input (HF dataset, local file, or synthetic)
✅ Two-phase pipeline: Phase 0 (optional pre-spec) → Phase 1 (evolution)
✅ Full logging and history tracking

User workflow:
1. Select merge methods (e.g., MOE + Task Arithmetic)
2. AI advisor shows: "MANDATORY - MOE needs specialized experts"
3. User configures: strategy=task_lora, data_source=hf:wikitext
4. Click "▶️ START EVOLUTION"
5. Phase 0 runs specialization, Phase 1 runs evolution with specialized models
6. Results show in Specialization History tab
"""
