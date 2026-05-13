"""
Streamlit UI Component: Slot-Based Model Selection + Recipe Generation

Complete workflow:
1. User enters local path in form
2. System validates model
3. User enters display name
4. Click "📤 Add" 
5. Model copied to zoo
6. Registry updated
7. Immediately available in slots
8. No refresh needed
"""

import streamlit as st
from typing import List, Dict, Optional
import json


def render_model_zoo_uploader(model_zoo):
    """
    Quick model zoo uploader - single unified form.
    
    Handles all steps: validate → copy → register → available
    """
    st.markdown("#### ➕ Add Local Model to Zoo")
    st.caption("Add models without leaving the page. They're immediately available in slots.")
    
    # Two-step form (input → submit all at once)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        local_path = st.text_input(
            "Model directory path",
            placeholder="/home/user/models/my-qwen-3b/",
            key="model_path_input",
            help="Full path to model folder (must contain config.json)"
        )
    
    with col2:
        display_name = st.text_input(
            "Display name",
            placeholder="my-qwen-reasoning",
            key="model_name_input",
            help="How to refer to this model (e.g., 'my-qwen-reasoning')"
        )
    
    # Validation feedback (live)
    if local_path.strip():
        is_valid, msg = model_zoo._validate_model_path(local_path.strip())
        if is_valid:
            st.success(f"✅ {msg}")
        else:
            st.warning(f"⚠️ {msg}")
    
    # Add button
    if st.button("📤 Add to Zoo", type="secondary", use_container_width=True):
        
        # Validate inputs
        if not local_path.strip():
            st.error("Enter a model path")
            return
        
        if not display_name.strip():
            st.error("Enter a display name")
            return
        
        is_valid, msg = model_zoo._validate_model_path(local_path.strip())
        if not is_valid:
            st.error(f"Invalid model: {msg}")
            return
        
        # Add to zoo
        with st.spinner(f"Adding '{display_name}' to zoo..."):
            success, message = model_zoo.add_local_model(
                local_path=local_path.strip(),
                model_name=display_name.strip(),
                model_type="generic",
                description="Local upload"
            )
        
        if success:
            st.success(f"✅ {message}")
            st.info(f"Model now available in slots!")
            
            # Clear inputs for next upload
            st.session_state.model_path_input = ""
            st.session_state.model_name_input = ""
            
            # Rerun to update slot dropdowns
            st.rerun()
        else:
            st.error(f"❌ {message}")


def render_model_slots(model_zoo, num_slots: int = 5) -> List[Optional[str]]:
    """
    Render 5 model slots with dropdowns.
    
    Each slot shows:
    - Local models (from zoo)
    - HuggingFace models (reference)
    - (empty) option
    
    Returns: List of selected model IDs [model_id, None, model_id, None, None]
    """
    
    st.markdown("#### 🎯 Model Slots (Select 1-5)")
    st.caption("Pick models for evolution. Leave empty for AI to suggest.")
    
    # Get all available models
    all_models = model_zoo.list_all_models()
    
    # Build dropdown options: "Display Name" → model_id
    model_options = {}
    for m in all_models:
        display = m.get("display_name", m["name"])
        model_id = m["name"]
        
        # Add source indicator
        source = "[Local]" if m.get("source_type") == "local" else "[HF]"
        display_with_source = f"{source} {display}"
        
        model_options[display_with_source] = model_id
    
    # Build dropdown list
    model_options_list = ["(empty - let AI choose)"] + list(model_options.keys())
    
    # Render 5 slot columns
    selected_slots = []
    cols = st.columns(num_slots)
    
    for i, col in enumerate(cols):
        with col:
            selection = st.selectbox(
                f"Slot {i+1}",
                model_options_list,
                key=f"slot_{i}",
                label_visibility="collapsed"
            )
            
            if selection == "(empty - let AI choose)":
                selected_slots.append(None)
            else:
                selected_slots.append(model_options[selection])
    
    # Summary metrics
    filled = sum(1 for s in selected_slots if s is not None)
    empty = sum(1 for s in selected_slots if s is None)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Filled", filled, delta="models selected")
    with col2:
        st.metric("Empty", empty, delta="available slots")
    with col3:
        st.metric("AI Will Fill", empty if empty > 0 else "-", delta="")
    
    return selected_slots


def render_recipe_summary(recipe: Dict):
    """
    Display selected recipe summary before evolution starts.
    
    Shows what the evolution will do when user clicks START EVOLUTION.
    """
    
    st.markdown("---")
    st.markdown("#### 📊 Recipe Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Strategy", recipe['name'].split(" ")[0])
    with col2:
        st.metric("Cycles", recipe['num_cycles'])
    with col3:
        st.metric("Methods", len(recipe['merge_methods']))
    
    st.info(f"**Approach**: {recipe['reasoning']}")
    
    with st.expander("📋 Full Recipe Details", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Strategy Type**: {recipe['strategy']}")
            st.markdown(f"**Total Cycles**: {recipe['num_cycles']}")
            st.markdown(f"**Culling Rate**: {recipe['culling_rate']}%")
        
        with col2:
            st.markdown(f"**Pre-specialization**: {recipe['specialization']}")
            st.markdown(f"**Merge Methods**: {len(recipe['merge_methods'])}")
            st.markdown(f"**Base Models**: TBD in evolution")
        
        st.markdown("---")
        st.markdown("**Methods in this recipe:**")
        st.code(", ".join(recipe['merge_methods']), language=None)
