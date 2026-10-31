"""Single source of paths, connection strings and seeds for M2."""
import os
import pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]  # repo root
RAW = ROOT / "data" / "raw"  # DVC-tracked in M1
PROCESSED = ROOT / "data" / "processed"
ARTIFACTS = ROOT / "artifacts"
REPORTS = ROOT / "reports"
CONFIGS = ROOT / "configs"

def _resolve_db_url() -> str:
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://cybersentry:cybersentry@localhost:5432/cybersentry"
    )
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(("localhost", 5432))
        s.close()
        # Verify if credentials work on localhost
        from sqlalchemy import create_engine
        e = create_engine(url, connect_args={"connect_timeout": 1})
        with e.connect():
            return url
    except Exception:
        pass
    # If localhost fails or native postgres is running, probe docker-desktop VM IP
    import subprocess
    try:
        out = subprocess.check_output(
            ["wsl", "-d", "docker-desktop", "-u", "root", "sh", "-c", "ip addr show eth0"],
            text=True, timeout=2, stderr=subprocess.DEVNULL
        )
        for line in out.splitlines():
            if "inet " in line:
                ip = line.strip().split()[1].split("/")[0]
                alt_url = url.replace("@localhost:", f"@{ip}:").replace("@127.0.0.1:", f"@{ip}:")
                try:
                    from sqlalchemy import create_engine
                    e = create_engine(alt_url, connect_args={"connect_timeout": 1})
                    with e.connect():
                        return alt_url
                except Exception:
                    pass
    except Exception:
        pass
    return url

DATABASE_URL = _resolve_db_url()
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
if "mlflow" in MLFLOW_URI:
    import socket
    try:
        host = MLFLOW_URI.split("://")[-1].split(":")[0]
        socket.getaddrinfo(host, 5000)
    except socket.gaierror:
        MLFLOW_URI = MLFLOW_URI.replace("://mlflow:", "://localhost:").replace("://mlflow", "://localhost")
        os.environ["MLFLOW_TRACKING_URI"] = MLFLOW_URI
MODEL_NAME = "cybersentry-auth-risk"
SEED = 42


def load_cfg(path=None) -> dict:
    with open(path or CONFIGS / "train.yaml") as fh:
        return yaml.safe_load(fh)
