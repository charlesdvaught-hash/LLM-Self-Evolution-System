import subprocess
import socket
import sys
import os
import webbrowser
import time

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

def stop_container(container_id):
    print(f"[i] Stopping container {container_id}...")
    subprocess.run(["docker", "stop", container_id], check=True, capture_output=True)
    subprocess.run(["docker", "rm", container_id], check=True, capture_output=True)

def find_available_port(start_port):
    port = start_port
    while is_port_in_use(port):
        print(f"[!] Port {port} is in use.")
        cid, image = get_container_using_port(port)
        if image == "vat-ui":
            print(f"[i] Found existing vat-ui container ({cid}). Stopping it...")
            stop_container(cid)
            if not is_port_in_use(port):
                return port
        else:
            port += 1
    return port

def run_ui():
    target_port = find_available_port(8501)
    host_pwd = os.getcwd()

    print(f"[🧬] Launching Control Room on port {target_port}...")

    docker_cmd = [
        "docker", "run", "--rm", "-d",
        "-p", f"{target_port}:8501",
        "-v", "//var/run/docker.sock:/var/run/docker.sock",
        "-v", f"{host_pwd}:/app",
        "-e", f"HOST_PWD={host_pwd}",
        "--gpus", "all",
        "--name", "vat-ui-live",
        "vat-ui"
    ]

    try:
        subprocess.run(docker_cmd, check=True)
        url = f"http://localhost:{target_port}"
        print(f"[✓] Control Room is live at {url}")
        webbrowser.open(url)

        print("\nPress Ctrl+C to stop the lab.")
        # Follow logs so the process stays alive and user can see output
        subprocess.run(["docker", "logs", "-f", "vat-ui-live"])
    except KeyboardInterrupt:
        print("\n[i] Stopping the Control Room...")
        subprocess.run(["docker", "stop", "vat-ui-live"], capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error launching container: {e}")
        sys.exit(1)

def verify_setup():
    images = ["vat-ui", "vat-merge", "vat-eval", "vat-sae"]
    missing = []
    print("\n--- Setup Validation ---")
    for img in images:
        result = subprocess.run(["docker", "images", "-q", img], capture_output=True, text=True)
        if result.stdout.strip():
            print(f"[✓] Image '{img}' is valid.")
        else:
            print(f"[X] Image '{img}' is MISSING.")
            missing.append(img)

    if not missing:
        print("\n[✓] All systems go! Use run.bat to start the lab.")
    else:
        print(f"\n[!] Setup incomplete. Missing: {', '.join(missing)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "run":
            run_ui()
        elif sys.argv[1] == "verify":
            verify_setup()
    else:
        print("Usage: manager.py [run|verify]")
