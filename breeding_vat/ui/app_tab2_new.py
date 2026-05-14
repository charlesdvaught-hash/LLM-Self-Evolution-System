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
