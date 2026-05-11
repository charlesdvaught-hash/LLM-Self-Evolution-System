import subprocess
import socket
import sys
import os
import webbrowser
import time

REQUIRED_IMAGES = {
    "vat-ui": "docker/Dockerfile.ui",
    "vat-merge": "docker/Dockerfile.merge",
    "vat-eval": "docker/Dockerfile.eval",
    "vat-sae": "docker/Dockerfile.sae"
}

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_container_using_port(port):
    try:
        # Look for containers mapping to the specified port
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

def stop_container(container_id, port):
    print(f"[i] Stopping container {container_id}...")
    subprocess.run(["docker", "stop", container_id], check=True, capture_output=True)

    # "The Patient Waiter" - Wait for the port to be released
    # Since we use --rm, Docker will remove the container automatically.
    print(f"[i] Waiting for port {port} to be released...")
    attempts = 0
    while is_port_in_use(port) and attempts < 10:
        time.sleep(1)
        attempts += 1

def find_available_port(start_port):
    port = start_port
    while is_port_in_use(port):
        cid, image = get_container_using_port(port)
        if image and "vat-ui" in image:
            print(f"[i] Port {port} is used by an existing vat-ui container ({cid}). Restarting...")
            stop_container(cid, port)
            # Re-check the port after stopping
            if not is_port_in_use(port):
                return port
        else:
            print(f"[!] Port {port} is in use by another process. Checking next port...")
            port += 1
    return port

def image_exists(image_name):
    result = subprocess.run(["docker", "images", "-q", image_name], capture_output=True, text=True)
    return bool(result.stdout.strip())

def ensure_images():
    print("[🧬] Verifying Lab Environment...")
    missing = []
    for name in REQUIRED_IMAGES:
        if not image_exists(name):
            missing.append(name)

    if not missing:
        print("[✓] All systems operational. Containers are ready.")
        return True

    print(f"[!] Missing {len(missing)} container(s). Initializing repair/setup...")
    for name in missing:
        dockerfile = REQUIRED_IMAGES[name]
        print(f"[i] Building {name} from {dockerfile}...")
        try:
            subprocess.run(["docker", "build", "-t", name, "-f", dockerfile, "."], check=True)
            print(f"[✓] {name} built successfully.")
        except subprocess.CalledProcessError:
            print(f"[X] Failed to build {name}. Please check Docker logs.")
            return False

    print("[✓] Environment repair complete.")
    return True

def run_ui():
    if not ensure_images():
        print("[X] Environment setup failed. Cannot launch UI.")
        sys.exit(1)

    target_port = find_available_port(8501)
    host_pwd = os.getcwd()

    print(f"[🧬] Launching Control Room on port {target_port}...")

    # We use a unique name for the container instance
    container_name = "vat-ui-live"
    # Ensure no name collision - silent stop if exists
    subprocess.run(["docker", "stop", container_name], capture_output=True)

    docker_cmd = [
        "docker", "run", "--rm", "-d",
        "-p", f"{target_port}:8501",
        "-v", "//var/run/docker.sock:/var/run/docker.sock",
        "-v", f"{host_pwd}:/app",
        "-e", f"HOST_PWD={host_pwd}",
        "--gpus", "all",
        "--name", container_name,
        "vat-ui"
    ]

    try:
        subprocess.run(docker_cmd, check=True)
        url = f"http://localhost:{target_port}"
        print(f"[✓] Control Room is live at {url}")

        # Give Streamlit a moment to start before opening browser
        time.sleep(2)
        webbrowser.open(url)

        print("\nPress Ctrl+C to stop the lab.")
        subprocess.run(["docker", "logs", "-f", container_name])
    except KeyboardInterrupt:
        print("\n[i] Stopping the Control Room...")
        subprocess.run(["docker", "stop", container_name], capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error launching container: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "run":
            run_ui()
        elif sys.argv[1] == "verify":
            ensure_images()
    else:
        print("Usage: manager.py [run|verify]")
