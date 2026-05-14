import ast
import os
import re
from typing import List, Dict, Set, Any

class CodeReader:
    def __init__(self, root_dir: str, max_file_size_mb: int = 5):
        self.root_dir = root_dir
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.modules = []
        self.intent_from_md = []
        self.skipped_files = []
        self.module_map = {} # path -> module info

    def analyze_repo(self):
        self._analyze_python_files()
        self._analyze_markdown_files()

    def _analyze_python_files(self):
        for root, dirs, files in os.walk(self.root_dir):
            if any(d in root for d in ['.git', '__pycache__', 'venv', 'node_modules']):
                continue
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.root_dir)
                    self._analyze_file(full_path, rel_path)

    def _analyze_file(self, full_path: str, rel_path: str):
        try:
            if os.path.getsize(full_path) > self.max_file_size:
                self.skipped_files.append({"path": rel_path, "reason": "file_too_large"})
                return

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = []
            definitions = {'classes': [], 'functions': []}
            
            defined_names = set()
            used_names = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        imports.append(n.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for n in node.names:
                        imports.append(f"{module}.{n.name}")
                elif isinstance(node, ast.ClassDef):
                    definitions['classes'].append(node.name)
                    defined_names.add(node.name)
                elif isinstance(node, ast.FunctionDef):
                    definitions['functions'].append(node.name)
                    defined_names.add(node.name)
                elif isinstance(node, ast.Name):
                    if isinstance(node.ctx, ast.Load):
                        used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    used_names.add(node.attr)

            unused_definitions = list(defined_names - used_names)

            module_info = {
                "name": rel_path.replace(os.path.sep, '.').replace('.py', ''),
                "unused_definitions": unused_definitions,
                "path": rel_path,
                "imports": list(set(imports)),
                "definitions": definitions
            }
            self.modules.append(module_info)
            self.module_map[rel_path] = module_info
        except Exception as e:
            # Fallback for files that can't be parsed
            self.modules.append({
                "name": rel_path.replace(os.path.sep, '.').replace('.py', ''),
                "path": rel_path,
                "error": str(e)
            })

    def _analyze_markdown_files(self):
        for root, dirs, files in os.walk(self.root_dir):
            if any(d in root for d in ['.git', '__pycache__', 'venv', 'node_modules']):
                continue
            for file in files:
                if file.endswith('.md'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.root_dir)
                    self._extract_intent_from_md(full_path, rel_path)

    def _extract_intent_from_md(self, full_path: str, rel_path: str):
        try:
            if os.path.getsize(full_path) > self.max_file_size:
                self.skipped_files.append({"path": rel_path, "reason": "file_too_large"})
                return

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Basic extraction: look for things that look like module paths or pipeline names
            # This is "intent" so it's fuzzy
            
            # Find possible module mentions
            possible_modules = re.findall(r'`([a-zA-Z_][a-zA-Z0-9_\./]*)`', content)
            
            # Find mentions of "pipeline"
            pipelines = re.findall(r'(?i)([a-zA-Z_ ]+pipeline)', content)

            self.intent_from_md.append({
                "source": rel_path,
                "mentions": list(set(possible_modules)),
                "pipelines": list(set(pipelines)),
                "summary": content[:200] + "..." if len(content) > 200 else content
            })
        except Exception as e:
            pass

    def get_results(self) -> Dict[str, Any]:
        return {
            "modules": self.modules,
            "intent_from_md": self.intent_from_md,
            "skipped_files": self.skipped_files
        }
