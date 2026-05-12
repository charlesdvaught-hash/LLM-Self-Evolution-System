import subprocess
import socket
import sys
import os
import webbrowser
import time
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Docker images to build and manage
# Note: breeding-vat-mergekit is deprecated - use breeding-vat-merge instead
REQUIRED_IMAGES = {
    "breeding-vat-ui": "docker/Dockerfile.ui",
    "breeding-vat-merge": "docker/Dockerfile.merge",  # MergeKit + FusionBench
    "breeding-vat-eval": "docker/Dockerfile.eval",
    "breeding-vat-sae": "docker/Dockerfile.sae"
    # Optional (for advanced features):
    # "breeding-vat-fusionbench": "docker/Dockerfile.fusionbench"
}

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_container_using_port(port):
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"publish={port}", "--format", "{{.ID}}|{{.Image}}"],
            capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            cid, image = result.stdout.strip().split('|')
            return cid, image
    except Exception:
        pass
    return None, None

def is_container_healthy(container_id):
    """Check if a container is running and healthy."""
    try:
        result = subprocess.run(
            ["docker", "ps", "-q", "--filter", f"id={container_id}"],
            capture_output=True, text=True, check=True
        )
        return bool(result.stdout.strip())
    except:
        return False

def container_exists(container_name):
    """Check if a container exists (running or stopped)."""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "-q", "--filter", f"name=^{container_name}$"],
            capture_output=True, text=True, check=True
        )
        return bool(result.stdout.strip())
    except:
        return False

def get_container_id(container_name):
    """Get container ID by name."""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "-q", "--filter", f"name=^{container_name}$"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip() if result.stdout.strip() else None
    except:
        return None

def stop_container(container_id, port=None):
    logger.info(f"Stopping container {container_id[:12]}...")
    try:
        subprocess.run(["docker", "stop", container_id], check=True, capture_output=True)
        if port:
            logger.info(f"Waiting for port {port} to be released...")
            attempts = 0
            while is_port_in_use(port) and attempts < 10:
                time.sleep(1)
                attempts += 1
        return True
    except Exception as e:
        logger.warning(f"Error stopping container: {e}")
        return False

def remove_container(container_id):
    """Forcefully remove a container."""
    logger.info(f"Removing container {container_id[:12]}...")
    try:
        subprocess.run(["docker", "rm", "-f", container_id], check=True, capture_output=True)
        return True
    except Exception as e:
        logger.warning(f"Error removing container: {e}")
        return False

def restart_container(container_id):
    """Restart an existing container."""
    logger.info(f"Restarting existing container {container_id[:12]}...")
    try:
        subprocess.run(["docker", "start", container_id], check=True, capture_output=True)
        return True
    except Exception as e:
        logger.warning(f"Error restarting container: {e}")
        return False

def stop_all_vat_containers():
    """Stop all Breeding Vat containers (graceful cleanup)."""
    logger.info("Stopping any running Breeding Vat containers...")
    try:
        result = subprocess.run(
            ["docker", "ps", "-q", "--filter", "label=breeding_vat=true"],
            capture_output=True, text=True
        )
        container_ids = result.stdout.strip().split('\n') if result.stdout.strip() else []
        for cid in container_ids:
            if cid:
                subprocess.run(["docker", "stop", cid], capture_output=True)
                logger.info(f"Stopped {cid[:12]}")
    except Exception as e:
        logger.warning(f"Could not stop all containers: {e}")

def find_available_port(start_port):
    port = start_port
    while is_port_in_use(port):
        cid, image = get_container_using_port(port)
        if image and "breeding-vat-ui" in image:
            logger.info(f"Port {port} is used by existing breeding-vat-ui container. Using it...")
            return port
        else:
            logger.info(f"Port {port} in use by another process. Trying {port + 1}...")
            port += 1
    return port

def image_exists(image_name):
    result = subprocess.run(["docker", "images", "-q", image_name], capture_output=True, text=True)
    return bool(result.stdout.strip())

def image_size(image_name):
    """Get image size in human-readable format."""
    try:
        result = subprocess.run(
            ["docker", "images", "--format", "{{.Size}}", image_name],
            capture_output=True, text=True
        )
        return result.stdout.strip()
    except:
        return "unknown"

def rebuild_image(name, dockerfile, force=False):
    """Rebuild a Docker image."""
    logger.info(f"Building {name}...")
    
    # Remove old image if force rebuild
    if force and image_exists(name):
        logger.info(f"Force rebuild: removing old {name} image...")
        subprocess.run(["docker", "image", "rm", name, "-f"], capture_output=True)
    
    try:
        result = subprocess.run(
            ["docker", "build", "-t", name, "-f", dockerfile, "."],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"[✓] {name} built successfully ({image_size(name)})")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to build {name}")
        if hasattr(e, 'stderr') and e.stderr:
            logger.error(f"Error: {e.stderr[:200]}")
        return False

def ensure_images(force_rebuild=False):
    """Verify and repair Docker images."""
    logger.info("[🧬] Verifying Lab Environment...")
    
    status = {}
    for name in REQUIRED_IMAGES:
        if image_exists(name):
            status[name] = ("exists", image_size(name))
        else:
            status[name] = ("missing", "0B")
    
    # Report status
    missing = [k for k, (s, _) in status.items() if s == "missing"]
    if not missing and not force_rebuild:
        logger.info("[✓] All systems operational.")
        for name, (s, size) in status.items():
            logger.info(f"  {name}: {size}")
        return True

    if missing or force_rebuild:
        if force_rebuild:
            logger.warning(f"Force rebuild requested. Rebuilding all {len(REQUIRED_IMAGES)} images...")
        else:
            logger.warning(f"Missing {len(missing)} image(s): {', '.join(missing)}")
            logger.warning("Initializing repair/setup...")
        
        for name in REQUIRED_IMAGES:
            dockerfile = REQUIRED_IMAGES[name]
            if not rebuild_image(name, dockerfile, force=force_rebuild):
                logger.error(f"[X] Critical: Failed to build {name}. Run 'setup.bat' to fix.")
                return False

        logger.info("[✓] Environment setup complete.")
        return True

    return True

def cleanup_old_containers():
    """Remove stopped Breeding Vat containers."""
    logger.info("Cleaning up old stopped containers...")
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "-q", "--filter", "label=breeding_vat=true", "--filter", "status=exited"],
            capture_output=True, text=True
        )
        container_ids = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        count = 0
        for cid in container_ids:
            if cid:
                remove_container(cid)
                count += 1
        
        if count > 0:
            logger.info(f"[✓] Removed {count} old container(s)")
        return True
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")
        return True

def download_models():
    """Download base models for breeding."""
    logger.info("[🧬] Checking for base models...")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/download_models.py"],
            check=False
        )
        if result.returncode == 0:
            logger.info("[✓] Models ready.")
            return True
        else:
            logger.warning("[!] Model download skipped. Proceeding anyway.")
            return True
    except Exception as e:
        logger.warning(f"Model download skipped: {e}")
        return True

def ensure_directories():
    """Create necessary data directories."""
    dirs = [
        "breeding_vat/data",
        "breeding_vat/data/merged_models",
        "breeding_vat/data/eval_results",
        "breeding_vat/configs",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        logger.debug(f"Directory ready: {d}")

def run_ui(reuse_container=True):
    """
    Launch the Streamlit UI container.
    
    Args:
        reuse_container: If True, reuse existing container if healthy
    """
    # Verify images are available
    if not ensure_images():
        logger.error("[X] Environment setup failed. Run 'setup.bat' to initialize.")
        return False

    target_port = 8501
    host_pwd = os.getcwd()
    container_name = "breeding-vat-ui"

    # Check for existing container
    existing_cid = get_container_id(container_name)
    if existing_cid and reuse_container:
        is_healthy = is_container_healthy(existing_cid)
        
        if is_healthy:
            logger.info(f"[✓] Reusing existing container {existing_cid[:12]}")
            logger.info(f"[🧬] Control Room is live at http://localhost:{target_port}")
            time.sleep(1)
            webbrowser.open(f"http://localhost:{target_port}")
            logger.info("Press Ctrl+C to stop. (Container will keep running)")
            try:
                subprocess.run(["docker", "logs", "-f", container_name])
            except KeyboardInterrupt:
                logger.info("Detached from logs. Container still running.")
            return True
        else:
            logger.warning(f"Existing container {existing_cid[:12]} is stopped or unhealthy.")
            try_restart = input("Restart it? (y/n): ").strip().lower() == 'y'
            
            if try_restart:
                if restart_container(existing_cid):
                    logger.info(f"[✓] Container restarted.")
                    logger.info(f"[🧬] Control Room is live at http://localhost:{target_port}")
                    time.sleep(1)
                    webbrowser.open(f"http://localhost:{target_port}")
                    logger.info("Press Ctrl+C to stop.")
                    try:
                        subprocess.run(["docker", "logs", "-f", container_name])
                    except KeyboardInterrupt:
                        logger.info("Detached from logs.")
                    return True
                else:
                    logger.warning("Could not restart container.")
            
            # Ask user if they want to rebuild
            rebuild_choice = input("Rebuild container? (y/n): ").strip().lower() == 'y'
            if rebuild_choice:
                logger.info("Removing old container and rebuilding...")
                remove_container(existing_cid)
            else:
                logger.info("Skipping container recreation. Exiting.")
                return False

    # Create new container
    logger.info(f"[🧬] Launching Control Room on port {target_port}...")

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

    try:
        result = subprocess.run(docker_cmd, capture_output=True, text=True, check=True)
        container_id = result.stdout.strip()
        logger.info(f"[✓] Container created: {container_id[:12]}")
        logger.info(f"[🧬] Control Room is live at http://localhost:{target_port}")

        time.sleep(2)
        webbrowser.open(f"http://localhost:{target_port}")

        logger.info("Press Ctrl+C to stop. (Container will continue running)")
        try:
            subprocess.run(["docker", "logs", "-f", container_name])
        except KeyboardInterrupt:
            logger.info("Detached from logs. Container still running.")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"[X] Error launching container:")
        if e.stderr:
            logger.error(f"  {e.stderr[:300]}")
        logger.error(f"[!] Run 'setup.bat' to rebuild images, or check Docker Desktop.")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "run":
            ensure_directories()
            download_models()
            cleanup_old_containers()
            run_ui(reuse_container=True)
            
        elif sys.argv[1] == "verify":
            ensure_directories()
            ensure_images()
            
        elif sys.argv[1] == "rebuild":
            logger.info("Force rebuilding all Docker images...")
            ensure_directories()
            ensure_images(force_rebuild=True)
            logger.info("[✓] Images rebuilt. Run 'run.bat' to start.")
            
        elif sys.argv[1] == "clean":
            stop_all_vat_containers()
            cleanup_old_containers()
            logger.info("[✓] Cleanup complete.")
            
        elif sys.argv[1] == "reset":
            logger.info("🔄 FULL SYSTEM RESET...")
            stop_all_vat_containers()
            cleanup_old_containers()
            existing_cid = get_container_id("breeding-vat-ui")
            if existing_cid:
                remove_container(existing_cid)
            ensure_directories()
            ensure_images(force_rebuild=True)
            logger.info("[✓] System reset complete. Run 'run.bat' to start fresh.")
            
        else:
            print("Unknown command. Usage: manager.py [run|verify|rebuild|clean|reset]")
    else:
        print("Breeding Vat Container Manager")
        print("Usage: manager.py [run|verify|rebuild|clean|reset]")
        print("  run     - Start UI (reuses existing container if healthy)")
        print("  verify  - Check environment & images")
        print("  rebuild - Force rebuild all Docker images")
        print("  clean   - Stop and remove stopped containers")
        print("  reset   - Full reset (remove all, rebuild images)")
