# opentrons_server.py (v3: host hardcoded & args ignored)
import os, time, json, requests
from fastmcp import FastMCP

mcp = FastMCP()

# 🔒 Hardcode your robot base URL here
ROBOT_BASE = "http://192.168.68.119:31950"

def _headers():
    return {"Opentrons-Version": "*"}

@mcp.tool()
def ping(host: str | None = None) -> str:
    """Ping robot health (host arg ignored; using hardcoded ROBOT_BASE)."""
    base = ROBOT_BASE
    try:
        r = requests.get(f"{base}/health", headers=_headers(), timeout=8)
        r.raise_for_status()
        return json.dumps(r.json())
    except Exception as e:
        raise RuntimeError(f"Ping failed for {base}/health: {e}")

@mcp.tool()
def upload_and_run(
    protocol_path: str,
    host: str | None = None,        # accepted but IGNORED
    start: bool = True,
    wait: bool = False,
    poll_interval_s: int = 5
) -> str:
    """Upload a .py protocol and optionally start/wait. Host arg is ignored."""
    base = ROBOT_BASE

    # Expand & absolutize path
    expanded = os.path.expanduser(protocol_path)
    if not os.path.isabs(expanded):
        expanded = os.path.abspath(expanded)

    if not os.path.exists(expanded):
        cwd = os.getcwd()
        nearby = [f for f in os.listdir(cwd) if f.endswith(".py")]
        raise FileNotFoundError(
            f"Protocol file not found: {expanded}\n"
            f"Server CWD: {cwd}\n"
            f"Nearby .py files: {nearby}"
        )

    # 1) Upload protocol
    try:
        with open(expanded, "rb") as f:
            files = {"files": f}  # mirrors your working snippet
            resp = requests.post(f"{base}/protocols", headers=_headers(), files=files, timeout=90)
        resp.raise_for_status()
        protocol_id = resp.json()["data"]["id"]
    except Exception as e:
        raise RuntimeError(f"Upload failed to {base}/protocols for {expanded}: {e}")

    # 2) Create run
    try:
        payload = {"data": {"protocolId": protocol_id}}
        r2 = requests.post(f"{base}/runs", headers=_headers(), json=payload, timeout=30)
        r2.raise_for_status()
        run_id = r2.json()["data"]["id"]
    except Exception as e:
        raise RuntimeError(f"Creating run failed at {base}/runs: {e}")

    result = {"protocol_id": protocol_id, "run_id": run_id, "started": False}

    # 3) Start
    if start:
        try:
            play = {"data": {"actionType": "play"}}
            r3 = requests.post(f"{base}/runs/{run_id}/actions", headers=_headers(), json=play, timeout=30)
            r3.raise_for_status()
            result["started"] = True
        except Exception as e:
            raise RuntimeError(f"Starting run failed at {base}/runs/{run_id}/actions: {e}")

    # 4) Wait
    if wait:
        try:
            terminal = {"succeeded", "failed", "stopped", "canceled"}
            while True:
                r4 = requests.get(f"{base}/runs/{run_id}", headers=_headers(), timeout=15)
                r4.raise_for_status()
                status = r4.json().get("data", {}).get("status", "unknown")
                if status in terminal:
                    result["final_status"] = status
                    break
                time.sleep(poll_interval_s)
        except Exception as e:
            raise RuntimeError(f"Polling run status failed at {base}/runs/{run_id}: {e}")

    return json.dumps(result)

if __name__ == "__main__":
    print("opentrons_server.py started. CWD:", os.getcwd())
    print("ROBOT_BASE:", ROBOT_BASE)
    mcp.run()

