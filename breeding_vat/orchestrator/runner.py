import subprocess
import os
import json
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Orchestrator")

class TaskRunner:
    def __init__(self, db_path="breeding_vat/data/breeding.db"):
        self.db_path = db_path
        # When running inside a container, we need to know the path on the HOST
        # to mount volumes correctly in sibling containers (Docker-out-of-Docker).
        self.host_pwd = os.environ.get("HOST_PWD", os.getcwd())
        self._init_db()

    def _init_db(self):
        # Ensure data dir exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with open("breeding_vat/data/schema.sql", "r") as f:
            schema = f.read()
        conn = sqlite3.connect(self.db_path)

        # Split schema by semicolon to handle statements individually
        # to support safe idempotency and manual migrations
        for statement in schema.split(';'):
            if statement.strip():
                try:
                    conn.execute(statement)
                except sqlite3.OperationalError as e:
                    if "already exists" in str(e) or "duplicate column name" in str(e):
                        continue
                    logger.warning(f"SQL warning: {e}")

        # Manual migration for 'method' column if not in schema.sql yet
        try:
            conn.execute("ALTER TABLE models ADD COLUMN method TEXT")
        except sqlite3.OperationalError:
            pass # Column already exists

        conn.commit()
        conn.close()

    def run_docker_task(self, image, command, volumes=None, gpus="all"):
        """
        Runs a command inside a docker container.
        volumes: dict of {relative_host_path: container_path}
        """
        docker_cmd = ["docker", "run", "--rm"]

        if gpus:
            docker_cmd.extend(["--gpus", gpus])

        if volumes:
            for rel_path, container_path in volumes.items():
                # We use the HOST path provided by the UI container environment
                # rel_path should be relative to the project root
                abs_host_path = os.path.join(self.host_pwd, rel_path)
                # Convert Windows backslashes to forward slashes for Docker
                abs_host_path = abs_host_path.replace("\\", "/")
                volume_mount = f"{abs_host_path}:{container_path}"
                docker_cmd.extend(["-v", volume_mount])

        docker_cmd.append(image)
        docker_cmd.extend(command)

        logger.info(f"Running task: {' '.join(docker_cmd)}")
        try:
            result = subprocess.run(docker_cmd, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Task failed: {e.stderr}")
            raise

    def log_model(self, name, base_models, recipe_path, experiment_id=None, parent_id=None, benchmark_results=None, cycle_number=None, status='completed', method=None):
        """Log a model to the database with full metadata."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        bench_str = json.dumps(benchmark_results) if benchmark_results else None

        cursor.execute(
            """INSERT INTO models
               (name, experiment_id, base_models, recipe_path, lineage_parent_id, benchmark_results, cycle_number, status, method)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, experiment_id, json.dumps(base_models), recipe_path, parent_id, bench_str, cycle_number, status, method)
        )
        model_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return model_id

    def update_model_status(self, model_id, status):
        """Update the status of an existing model."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE models SET status = ? WHERE id = ?", (status, model_id))
        conn.commit()
        conn.close()
