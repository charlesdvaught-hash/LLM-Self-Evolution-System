import subprocess
import os
import json
import sqlite3
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Orchestrator")

class TaskRunner:
    def __init__(self, db_path="breeding_vat/data/breeding.db"):
        self.db_path = db_path
        self.host_pwd = os.environ.get("HOST_PWD", os.getcwd())
        self.simulation_mode = os.environ.get("SIMULATION_MODE", "false").lower() == "true"
        if self.simulation_mode:
            logger.info("⚠️ [SIMULATION MODE] TaskRunner will emulate Docker task success.")
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        schema_path = "breeding_vat/data/schema.sql"
        if not os.path.exists(schema_path):
            schema_path = os.path.join(os.path.dirname(__file__), "..", "data", "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, "r") as f:
                schema = f.read()
            conn = sqlite3.connect(self.db_path)
            conn.executescript(schema)
            conn.commit()
            conn.close()

    def run_docker_task(self, image, command, volumes=None, gpus="all"):
        if self.simulation_mode:
            return self._emulate_docker_task(image, command, volumes)
        docker_cmd = ["docker", "run", "--rm"]
        if gpus: docker_cmd.extend(["--gpus", gpus])
        if volumes:
            for rel_path, container_path in volumes.items():
                abs_host_path = os.path.join(self.host_pwd, rel_path).replace("\\", "/")
                docker_cmd.extend(["-v", f"{abs_host_path}:{container_path}"])
        docker_cmd.append(image)
        docker_cmd.extend(command)
        logger.info(f"Running task: {' '.join(docker_cmd)}")
        try:
            result = subprocess.run(docker_cmd, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Task failed: {e.stderr}")
            raise

    def _emulate_docker_task(self, image, command, volumes):
        logger.info(f"[SIMULATING] Docker Image: {image}")
        logger.info(f"[SIMULATING] Command: {' '.join(command)}")
        time.sleep(0.1)
        if "merge" in image or "fusionbench" in image:
            output_name = None
            # Command: mergekit-yaml /app/configs/mergekit_slerp.yaml /app/data/merged_models/mutant_c0_p0_o0 ...
            for arg in command:
                if "/app/data/merged_models/" in arg:
                    output_name = os.path.basename(arg)
                elif arg.startswith("output_path="):
                    output_name = arg.split("=")[1]

            if output_name:
                out_dir = os.path.join("breeding_vat/data/merged_models", output_name)
                os.makedirs(out_dir, exist_ok=True)
                with open(os.path.join(out_dir, "config.json"), "w") as f:
                    json.dump({"model_type": "gpt2", "_is_mock": True}, f)
                with open(os.path.join(out_dir, "mock_weights.bin"), "w") as f:
                    f.write("MOCK_WEIGHTS")
                logger.info(f"[SIMULATED] Created mock model at {out_dir}")

        if "eval" in image or "lm_eval" in command or "ppl" in "".join(command):
            results_dir = "breeding_vat/data/eval_results"
            os.makedirs(results_dir, exist_ok=True)
            if "ppl" in "".join(command):
                for arg in command:
                    if arg.endswith("_ppl.json"):
                        fname = os.path.basename(arg)
                        res_file = os.path.join(results_dir, fname)
                        with open(res_file, "w") as f: json.dump({"passed": True, "perplexity": 12.5, "reason": "mock success"}, f)
                        logger.info(f"[SIMULATED] Created mock PPL results at {res_file}")
                        return "SIMULATION_SUCCESS"

            output_path = None
            model_name = "unknown"
            for i, arg in enumerate(command):
                if arg == "--output_path":
                    output_path = command[i+1]
                if arg == "--model_args":
                    parts = command[i+1].split(",")
                    for p in parts:
                        if p.startswith("path=") or p.startswith("pretrained="):
                            model_name = os.path.basename(p.split("=")[1])

            if not output_path and model_name != "unknown":
                output_path = f"/app/data/eval_results/{model_name}.json"

            if output_path:
                fname = os.path.basename(output_path)
                res_file = os.path.join(results_dir, fname)
                import random
                mock_score = 0.5 + (random.random() * 0.4)
                with open(res_file, "w") as f:
                    json.dump({"results": {"arc_easy": {"acc": mock_score}, "arc_challenge": {"acc": mock_score - 0.1}, "hellaswag": {"acc": mock_score + 0.05}}, "mock": True}, f)
                logger.info(f"[SIMULATED] Created mock eval results at {res_file}")
        return "SIMULATION_SUCCESS"

    def image_exists(self, image_name):
        if self.simulation_mode: return True
        try:
            result = subprocess.run(["docker", "images", "-q", image_name], capture_output=True, text=True)
            return bool(result.stdout.strip())
        except: return False

    def log_model(self, name, base_models, method, parent_id=None, experiment_id=None, score=0.0):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO models (name, base_models, method, lineage_parent_id, experiment_id, score, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, json.dumps(base_models), method, parent_id, experiment_id, score, 'completed')
        )
        model_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return model_id
