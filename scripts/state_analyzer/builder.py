from typing import Dict, List, Any, Set
import os
import re

class StateBuilder:
    def __init__(self, code_results: Dict[str, Any], docker_results: Dict[str, Any]):
        self.code_results = code_results
        self.docker_results = docker_results
        self.system_state = {
            "containers": [],
            "entrypoints": [],
            "execution_paths": [],
            "modules": [],
            "pipelines": [],
            "orphan_suspects": [],
            "intent_from_md": [],
            "runtime_truth": [],
            "contradictions": [],
            "review_recommendations": []
        }

    def build(self) -> Dict[str, Any]:
        self._process_modules()
        self._process_docker()
        self._process_intent()
        self._detect_orphans()
        self._detect_contradictions()
        self._detect_pipelines()
        self._check_structural_health()
        self._generate_review_recommendations()
        return self.system_state

    def _process_modules(self):
        self.system_state["modules"] = self.code_results.get("modules", [])

    def _process_docker(self):
        rt = self.docker_results.get("runtime_truth", {})
        self.system_state["runtime_truth"] = rt
        self.system_state["containers"] = rt.get("containers", [])
        self.system_state["entrypoints"] = self.docker_results.get("entrypoints", [])

    def _process_intent(self):
        self.system_state["intent_from_md"] = self.code_results.get("intent_from_md", [])

    def _detect_orphans(self):
        # A module is an orphan suspect if it's not imported by anything
        # and not mentioned in intent or runtime entrypoints
        all_modules = {m["name"] for m in self.system_state["modules"] if "name" in m}
        imported_modules = set()
        for m in self.system_state["modules"]:
            if "imports" in m:
                for imp in m["imports"]:
                    imported_modules.add(imp)
        
        # Also check if it's an entrypoint
        entrypoint_scripts = set()
        for ep in self.system_state["entrypoints"]:
            if ep.get("cmd"):
                # Extract potential script from CMD [ "python", "script.py" ]
                scripts = [s.strip('"') for s in ep["cmd"].strip('[]').split(',') if '.py' in s]
                entrypoint_scripts.update(scripts)

        intent_mentions = set()
        for intent in self.system_state["intent_from_md"]:
            intent_mentions.update(intent.get("mentions", []))

        for m_name in all_modules:
            # Check if this module name or its path appears in imports or intent
            is_referenced = False
            
            # Check imports
            if any(m_name in imp for imp in imported_modules):
                is_referenced = True
            
            # Check intent
            if any(m_name in mention for mention in intent_mentions):
                is_referenced = True
                
            # Check if it's a known entrypoint script
            if any(m_name in script for script in entrypoint_scripts):
                is_referenced = True

            if not is_referenced:
                self.system_state["orphan_suspects"].append(m_name)

    def _detect_contradictions(self):
        # Documentation mentions something that doesn't exist
        all_module_names = {m["name"] for m in self.system_state["modules"] if "name" in m}
        all_module_paths = {m["path"] for m in self.system_state["modules"] if "path" in m}
        
        intent_mentions = set()
        for intent in self.system_state["intent_from_md"]:
            for mention in intent.get("mentions", []):
                # Clean mention
                clean = mention.strip('./')
                if clean and '.' in clean: # likely a path or module
                    if clean not in all_module_names and clean not in all_module_paths:
                        # Check if it might be a partial path
                        if not any(clean in p for p in all_module_paths):
                            self.system_state["contradictions"].append({
                                "type": "documented_but_missing",
                                "item": mention,
                                "source": intent["source"]
                            })

        # Runtime uses something not documented (not in intent)
        # This is a bit harder, but we can check containers
        intent_md_content = " ".join([i.get("summary", "") for i in self.system_state["intent_from_md"]])
        for container in self.system_state["containers"]:
            c_name = container["name"]
            if c_name not in intent_md_content:
                 self.system_state["contradictions"].append({
                    "type": "running_but_undocumented",
                    "item": f"Container: {c_name}",
                    "source": "runtime"
                })

    def _detect_pipelines(self):
        # Extract pipelines from intent and try to find matching code structures
        for intent in self.system_state["intent_from_md"]:
            for p in intent.get("pipelines", []):
                self.system_state["pipelines"].append({
                    "name": p,
                    "source": intent["source"],
                    "status": "declared"
                })
        
        # Build execution paths from entrypoints and script intent
        entrypoint_scripts = set()
        
        # From Dockerfiles
        for ep in self.system_state["entrypoints"]:
            if ep.get("cmd"):
                scripts = [s.strip('"').strip("'") for s in ep["cmd"].strip('[]').split(',') if '.py' in s]
                for s in scripts:
                    entrypoint_scripts.add(s.strip())

        # From Script Intent (runtime_truth)
        rt = self.system_state.get("runtime_truth", {})
        for key, cmds in rt.items():
            if key.startswith("intent_from_"):
                for cmd in cmds:
                    # Support python script.py, python -m module, and docker run ... python script.py
                    # 1. Look for python script.py
                    match = re.search(r'python\s+([a-zA-Z0-9_\./\-]+\.py)', cmd)
                    if match:
                        entrypoint_scripts.add(match.group(1))
                    else:
                        # 2. Look for python -m module
                        match_m = re.search(r'python\s+-m\s+([a-zA-Z0-9_\.]+)', cmd)
                        if match_m:
                            # Convert module to potential path
                            mod_path = match_m.group(1).replace('.', '/') + '.py'
                            entrypoint_scripts.add(mod_path)

        for script in entrypoint_scripts:
            # Clean path (remove leading /app/ if present)
            clean_script = script.replace('/app/', '').lstrip('./')
            path = [clean_script]
            self._trace_execution_path(clean_script, path, set())
            self.system_state["execution_paths"].append({
                "entrypoint": clean_script,
                "chain": path
            })

    def _trace_execution_path(self, current_module: str, path: List[str], visited: Set[str]):
        if current_module in visited or len(path) > 10:
            return
        visited.add(current_module)
        
        # Find module info
        m_info = next((m for m in self.system_state["modules"] if current_module in m.get("name", "") or current_module in m.get("path", "")), None)
        if m_info and "imports" in m_info:
            for imp in m_info["imports"]:
                # Only trace internal imports
                if "breeding_vat" in imp or any(m["name"] in imp for m in self.system_state["modules"]):
                    path.append(imp)
                    self._trace_execution_path(imp, path, visited)

    def _check_structural_health(self):
        health = {
            "broken_imports": [],
            "module_depth": 0,
            "complexity_score": 0
        }
        all_module_names = {m["name"] for m in self.system_state["modules"] if "name" in m}
        
        for m in self.system_state["modules"]:
            if "imports" in m:
                for imp in m["imports"]:
                    # Check if internal import exists
                    if ("breeding_vat" in imp or "scripts" in imp) and imp not in all_module_names:
                        # Might be sub-module import, check prefix
                        if not any(imp.startswith(name) for name in all_module_names):
                            health["broken_imports"].append({
                                "module": m["name"],
                                "import": imp
                            })
        
        self.system_state["structural_health"] = health

    def _generate_review_recommendations(self):
        recommendations = []
        
        # Files with broken imports
        broken = self.system_state.get("structural_health", {}).get("broken_imports", [])
        for b in broken:
            recommendations.append({
                "file": b["module"],
                "reason": f"Broken internal import: {b['import']}",
                "priority": "high",
                "suggested_tool": "aider"
            })
            
        # Contradictions
        for c in self.system_state.get("contradictions", []):
            recommendations.append({
                "file": c["source"] if "source" in c else c["item"],
                "reason": f"Contradiction: {c['type']} ({c['item']})",
                "priority": "medium",
                "suggested_tool": "aider"
            })

        # Modules with many unused definitions
        for m in self.system_state.get("modules", []):
            unused = m.get("unused_definitions", [])
            if len(unused) > 5:
                recommendations.append({
                    "file": m["path"],
                    "reason": f"High dead code count ({len(unused)} unused definitions)",
                    "priority": "low",
                    "suggested_tool": "aider"
                })

        self.system_state["review_recommendations"] = recommendations
