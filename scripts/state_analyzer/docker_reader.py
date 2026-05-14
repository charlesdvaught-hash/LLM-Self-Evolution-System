"""
DockerReader — extracts Docker ground truth from:
  1. scripts/manager.py  (REQUIRED_IMAGES dict + docker run command)
  2. docker/ Dockerfiles  (ENTRYPOINT / CMD per image)
  3. docker ps / docker images  (live runtime state)
  4. Any extra files passed via --manual-docker-files
"""

import ast
import os
import re
import subprocess
from typing import Any, Dict, List


class DockerReader:
    def __init__(self, root_dir: str, max_file_size_mb: int = 5):
        self.root_dir = root_dir
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.runtime_truth: Dict[str, Any] = {
            "containers": [],
            "images": [],
            "networks": [],
            "volumes": [],
        }
        self.entrypoints: List[Dict] = []
        self.required_images: Dict[str, str] = {}   # name → Dockerfile path
        self.run_command: Dict[str, Any] = {}        # parsed docker run args
        self.manager_commands: List[str] = []        # subcommand → action map

    # ── public API ────────────────────────────────────────────────────────────────────

    def analyze_runtime(self):
        self._parse_manager()
        self._analyze_dockerfiles()
        self._get_docker_ps()
        self._get_docker_images()

    def analyze_specific_file(self, file_path: str):
        """Extra file passed via --manual-docker-files."""
        full = (os.path.join(self.root_dir, file_path)
                if not os.path.isabs(file_path) else file_path)
        full = os.path.abspath(full)
        if not os.path.isfile(full):
            print(f"  [!] Not found: {file_path}")
            return
        if os.path.getsize(full) > self.max_file_size:
            return
        rel = os.path.relpath(full, self.root_dir).replace("\\", "/")
        try:
            with open(full, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            cmds = re.findall(r"docker\s+(?:run|build|exec|compose|push|pull)\S*.*", content)
            if cmds:
                self.runtime_truth[f"intent_from_{rel}"] = [c.strip() for c in cmds]
                print(f"  [+] docker evidence in: {rel}")
        except Exception as e:
            print(f"  [!] Error reading {file_path}: {e}")

    def get_results(self) -> Dict[str, Any]:
        return {
            "runtime_truth":  self.runtime_truth,
            "entrypoints":    self.entrypoints,
            "required_images": self.required_images,
            "run_command":    self.run_command,
            "manager_commands": self.manager_commands,
        }

    # ── manager.py parsing ────────────────────────────────────────────────────────────────

    def _parse_manager(self):
        """
        Parse scripts/manager.py with AST to extract:
          - REQUIRED_IMAGES dict  (name → Dockerfile)
          - docker run command    (volumes, ports, flags)
          - subcommand dispatch   (run / rebuild / clean / reset / verify)
        Falls back to regex if AST fails.
        """
        manager_path = os.path.join(self.root_dir, "scripts", "manager.py")
        if not os.path.isfile(manager_path):
            print("  [!] scripts/manager.py not found — skipping manager parse")
            return

        print("  [+] Parsing scripts/manager.py for Docker canon...")
        try:
            with open(manager_path, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception as e:
            print(f"  [!] Cannot read manager.py: {e}")
            return

        # ── REQUIRED_IMAGES via AST ───────────────────────────────────────────────────
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if (isinstance(node, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "REQUIRED_IMAGES"
                                for t in node.targets)
                        and isinstance(node.value, ast.Dict)):
                    for k, v in zip(node.value.keys, node.value.values):
                        if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                            self.required_images[k.value] = v.value
            if self.required_images:
                print(f"  [+] REQUIRED_IMAGES: {list(self.required_images.keys())}")
                self.runtime_truth["required_images"] = self.required_images
        except SyntaxError:
            pass  # fall through to regex below

        # ── Fallback: regex for REQUIRED_IMAGES ────────────────────────────────────
        if not self.required_images:
            for m in re.finditer(
                r'"(breeding-vat-[^"]+)"\s*:\s*"([^"]+Dockerfile[^"]*)"', source
            ):
                self.required_images[m.group(1)] = m.group(2)
            if self.required_images:
                self.runtime_truth["required_images"] = self.required_images

        # ── docker run command ────────────────────────────────────────────────────────────────
        run_match = re.search(
            r'"docker",\s*"run"(.*?)(?=\]\s*\n)', source, re.DOTALL
        )
        if run_match:
            raw = run_match.group(0)
            rc = {
                "detached": '"-d"' in raw,
                "gpu":      '"--gpus"' in raw,
                "ports":    re.findall(r'"-p",\s*"([^"]+)"', raw),
                "volumes":  re.findall(r'"-v",\s*"([^"]+)"', raw),
                "env":      re.findall(r'"-e",\s*"([^"]+)"', raw),
                "labels":   re.findall(r'"--label",\s*"([^"]+)"', raw),
                "image":    (re.findall(r'"(breeding-vat-ui[^"]*)"', raw) or ["?"])[-1],
            }
            self.run_command = rc
            self.runtime_truth["canonical_run_command"] = rc
            print(f"  [+] docker run: ports={rc['ports']} vols={len(rc['volumes'])} gpu={rc['gpu']}")

        # ── subcommand → action map ─────────────────────────────────────────────────
        for m in re.finditer(r'sys\.argv\[1\]\s*==\s*"([^"]+)"', source):
            self.manager_commands.append(m.group(1))
        if self.manager_commands:
            self.runtime_truth["manager_subcommands"] = self.manager_commands

        # ── store intent lines ─────────────────────────────────────────────────────────────────
        docker_lines = re.findall(r'"docker"[^\n]+', source)
        if docker_lines:
            self.runtime_truth["intent_from_scripts/manager.py"] = docker_lines

    # ── Dockerfile parsing ─────────────────────────────────────────────────────────────────

    def _analyze_dockerfiles(self):
        docker_dir = os.path.join(self.root_dir, "docker")
        targets = []

        if os.path.isdir(docker_dir):
            for f in os.listdir(docker_dir):
                if f.startswith("Dockerfile"):
                    targets.append((os.path.join(docker_dir, f), f"docker/{f}"))

        root_df = os.path.join(self.root_dir, "Dockerfile")
        if os.path.isfile(root_df):
            targets.append((root_df, "Dockerfile"))

        for full_path, rel_name in targets:
            self._extract_dockerfile_info(full_path, rel_name)

    def _extract_dockerfile_info(self, path: str, name: str):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            entrypoint = re.findall(r"(?im)^ENTRYPOINT\s+(.*)", content)
            cmd        = re.findall(r"(?im)^CMD\s+(.*)",        content)
            expose     = re.findall(r"(?im)^EXPOSE\s+(.*)",     content)
            base_image = re.findall(r"(?im)^FROM\s+(\S+)",      content)
            workdir    = re.findall(r"(?im)^WORKDIR\s+(\S+)",   content)

            # Match to REQUIRED_IMAGES by Dockerfile filename
            image_name = next(
                (img for img, df in self.required_images.items()
                 if os.path.basename(df) == os.path.basename(path)),
                None,
            )

            self.entrypoints.append({
                "source":     name,
                "image_name": image_name,
                "base_image": base_image[0] if base_image else None,
                "workdir":    workdir[-1]    if workdir    else None,
                "entrypoint": entrypoint[0] if entrypoint else None,
                "cmd":        cmd[0]         if cmd        else None,
                "expose":     expose[0]      if expose     else None,
            })
        except Exception as e:
            print(f"  [!] Dockerfile parse error ({name}): {e}")

    # ── live Docker state ────────────────────────────────────────────────────────────────

    def _get_docker_ps(self):
        try:
            result = subprocess.run(
                ["docker", "ps", "--format",
                 "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}|{{.Labels}}"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().splitlines():
                    parts = line.split("|")
                    if len(parts) >= 5:
                        self.runtime_truth["containers"].append({
                            "id":     parts[0],
                            "name":   parts[1],
                            "image":  parts[2],
                            "status": parts[3],
                            "ports":  parts[4],
                            "labels": parts[5] if len(parts) > 5 else "",
                        })
        except Exception as e:
            self.runtime_truth["error_ps"] = str(e)

    def _get_docker_images(self):
        try:
            result = subprocess.run(
                ["docker", "images", "--format",
                 "{{.Repository}}:{{.Tag}}|{{.ID}}|{{.Size}}|{{.CreatedSince}}"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().splitlines():
                    parts = line.split("|")
                    if len(parts) >= 3:
                        img = {
                            "repository": parts[0],
                            "id":         parts[1],
                            "size":       parts[2],
                            "created":    parts[3] if len(parts) > 3 else "",
                        }
                        self.runtime_truth["images"].append(img)

            # Cross-reference: which REQUIRED_IMAGES are actually built?
            built = {i["repository"] for i in self.runtime_truth["images"]}
            image_status = {}
            for img_name in self.required_images:
                full_name = f"{img_name}:latest"
                image_status[img_name] = "built" if full_name in built else "MISSING"
            if image_status:
                self.runtime_truth["image_build_status"] = image_status
                missing = [k for k, v in image_status.items() if v == "MISSING"]
                if missing:
                    print(f"  [!] Images not yet built: {missing}  → run setup.bat")
                else:
                    print(f"  [+] All {len(image_status)} required images present")
        except Exception as e:
            self.runtime_truth["error_images"] = str(e)
