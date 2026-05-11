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
        self._init_db()

    def _init_db(self):
        with open("breeding_vat/data/schema.sql", "r") as f:
            schema = f.read()
        conn = sqlite3.connect(self.db_path)
        conn.executescript(schema)
        conn.commit()
        conn.close()

    def run_docker_task(self, image, command, volumes=None, gpus="all"):
        """
        Runs a command inside a docker container.
        volumes: dict of {host_path: container_path}
        """
        docker_cmd = ["docker", "run", "--rm"]

        if gpus:
            docker_cmd.extend(["--gpus", gpus])

        if volumes:
            for host, container in volumes.items():
                abs_host = os.path.abspath(host)
                docker_cmd.extend(["-v", f"{abs_host}:{container}"])

        docker_cmd.append(image)
        docker_cmd.extend(command)

        logger.info(f"Running task: {' '.join(docker_cmd)}")
        try:
            result = subprocess.run(docker_cmd, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Task failed: {e.stderr}")
            raise

    def log_model(self, name, base_models, recipe_path, parent_id=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO models (name, base_models, recipe_path, lineage_parent_id, status) VALUES (?, ?, ?, ?, ?)",
            (name, json.dumps(base_models), recipe_path, parent_id, 'completed')
        )
        model_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return model_id

if __name__ == "__main__":
    # Test initialization
    runner = TaskRunner()
    print("Orchestrator initialized and DB schema applied.")
