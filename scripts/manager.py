import subprocess
import socket
import sys
import os
import time
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SIMULATION_MODE = os.environ.get("SIMULATION_MODE", "false").lower() == "true"

REQUIRED_IMAGES = {
    "breeding-vat-ui":          "docker/Dockerfile.ui",
    "breeding-vat-merge":       "docker/Dockerfile.merge",
    "breeding-vat-eval":        "docker/Dockerfile.eval",
    "breeding-vat-sae":         "docker/Dockerfile.sae",
    "breeding-vat-fusionbench": "docker/Dockerfile.fusionbench",
    "breeding-vat-finetune":    "docker/Dockerfile.finetune",
}

def image_exists(image_name):
    if SIMULATION_MODE: return True
    try:
        result = subprocess.run(["docker", "images", "-q", image_name], capture_output=True, text=True)
        return bool(result.stdout.strip())
    except: return False

def download_models():
    logger.info("[*] Downloading models from HuggingFace...")
    try:
        # Default to baseline preset for setup efficiency
        result = subprocess.run([sys.executable, "scripts/download_models.py", "--preset", "baseline"], check=False)
        return result.returncode == 0
    except Exception as e:
        logger.warning(f"[!] Model download error: {e}")
        return False

def ensure_directories():
    dirs = [
        "breeding_vat/data", "breeding_vat/data/model_zoo", "breeding_vat/data/merged_models",
        "breeding_vat/data/eval_results", "breeding_vat/configs", "breeding_vat/data/experiments",
        "breeding_vat/data/recipes",
    ]
    for d in dirs: os.makedirs(d, exist_ok=True)

def ensure_images():
    if SIMULATION_MODE:
        logger.info("⚠️ [SIMULATION MODE] Bypassing Docker build checks.")
        return True
    
    # Check if docker is even available
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
    except:
        logger.error("[X] Docker not found. Install Docker Desktop or enable SIMULATION_MODE=true.")
        return False

    for name, dockerfile in REQUIRED_IMAGES.items():
        if not image_exists(name):
            logger.info(f"Building {name}...")
            try:
                subprocess.run(["docker", "build", "-t", name, "-f", dockerfile, "."], check=True)
                logger.info(f"[✓] {name} built successfully")
            except:
                logger.error(f"Failed to build {name}")
                return False
    return True

def run_ui():
    if SIMULATION_MODE:
        logger.warning("!" * 60)
        logger.warning("!  SIMULATION MODE ACTIVE - RESULTS ARE MOCKED                  !")
        logger.warning("!  Docker tasks will be bypassed. No models will be merged.    !")
        logger.warning("!" * 60)
        logger.info("🚀 [SIMULATION MODE] Starting Streamlit UI locally.")
        # Ensure current dir is in pythonpath
        env = os.environ.copy()
        env["PYTHONPATH"] = f".{os.pathsep}{env.get('PYTHONPATH', '')}"
        subprocess.run(["streamlit", "run", "breeding_vat/ui/app.py"], env=env)
        return

    target_port = 8501
    host_pwd = os.getcwd()
    container_name = "breeding-vat-ui"

    # Check if container exists
    cid_result = subprocess.run(["docker", "ps", "-a", "-q", "--filter", f"name={container_name}"], capture_output=True, text=True)
    if cid_result.stdout.strip():
        logger.info(f"Restarting existing {container_name}...")
        subprocess.run(["docker", "start", container_name])
    else:
        logger.info(f"Launching new {container_name}...")
        docker_cmd = [
            "docker", "run", "-d",
            "-p", f"{target_port}:8501",
            "-v", "//var/run/docker.sock:/var/run/docker.sock",
            "-v", f"{host_pwd}:/app",
            "-e", f"HOST_PWD={host_pwd}",
            "--gpus", "all",
            "--label", "breeding_vat=true",
            "--name", container_name,
            "breeding-vat-ui:latest"
        ]
        subprocess.run(docker_cmd)

    logger.info(f"Control Room live at http://localhost:{target_port}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: manager.py [setup|run|verify]")
        sys.exit(1)
    cmd = sys.argv[1]
    ensure_directories()
    if cmd == "setup":
        ensure_images()
        download_models()
    elif cmd == "run":
        run_ui()
    elif cmd == "verify":
        ensure_images()
