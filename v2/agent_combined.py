import os
import re
import json
import asyncio
import google.generativeai as genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# -------- CONFIG --------
GEMINI_MODEL = "gemini-2.5-pro"  # ✅ your preferred model

# Commands to launch your MCP servers
CAMERA_SERVER_CMD = ["python", "camera_server.py"]
OPENTRONS_SERVER_CMD = ["python", "opentrons_server.py"]

# Hardcoded Opentrons configuration
OPENTRONS_HOST = "192.168.68.119:31950"   # ✅ your robot IP:port
OPENTRONS_PROTOCOL_PATH = (
    "/Users/aldairgongora/Documents/2025_10_25_Hackathon/96-ch_partial_test.py"
)

SYSTEM_INSTRUCTIONS = f"""You are a lab agent that can call tools via MCP.
You have two servers: "camera" and "opentrons".

TOOLS
- camera.take_photo(device_index=0, width=1920, height=1080, warmup_frames=10)
- opentrons.ping()
- opentrons.upload_and_run(protocol_path="{OPENTRONS_PROTOCOL_PATH}",
                           host="{OPENTRONS_HOST}",
                           start=True, wait=False, poll_interval_s=5)

WHEN TO CALL TOOLS
- If the user asks for a photo/snapshot/image, call camera.take_photo.
- If the user asks to check/verify the Flex, call opentrons.ping.
- If the user asks to upload/run a protocol, call opentrons.upload_and_run.
- If the user asks for multiple actions (e.g., "take a photo then run the protocol"),
  output a JSON ARRAY of actions in order.

RESPONSE FORMAT
- If planning tools, output ONLY JSON:
  Single tool:
    {{"action":"tool","server":"camera"|"opentrons","tool":"<toolName>","args":{{...}}}}
  Multiple tools:
    [{{...}}, {{...}}]
- Otherwise, answer with plain text.
- Use the hardcoded values for host and protocol_path.
"""

# ---- JSON parsing helpers ----
JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL | re.IGNORECASE)

def extract_first_json(text: str):
    if not text:
        return None
    t = text.strip()
    # Direct JSON
    if (t.startswith("{") and t.endswith("}")) or (t.startswith("[") and t.endswith("]")):
        try:
            return json.loads(t)
        except json.JSONDecodeError:
            pass
    # Fenced code block
    m = JSON_BLOCK_RE.search(t)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Heuristic fallback
    start = min([p for p in [t.find("{"), t.find("[")] if p != -1], default=-1)
    if start != -1:
        candidate = t[start:]
        for end in range(len(candidate), start, -1):
            snippet = candidate[:end].strip()
            if (snippet.startswith("{") and snippet.endswith("}")) or (snippet.startswith("[") and snippet.endswith("]")):
                try:
                    return json.loads(snippet)
                except json.JSONDecodeError:
                    continue
    return None

def try_parse_plans(text: str):
    obj = extract_first_json(text)
    if obj is None:
        return None
    if isinstance(obj, dict):
        return [obj]
    if isinstance(obj, list):
        return obj
    return None

# ---- MCP call helper ----
async def call_mcp(server: str, tool_name: str, args: dict):
    if server == "camera":
        server_cmd = CAMERA_SERVER_CMD
    elif server == "opentrons":
        server_cmd = OPENTRONS_SERVER_CMD
    else:
        raise ValueError(f"Unknown server: {server}")

    params = StdioServerParameters(command=server_cmd[0], args=server_cmd[1:])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(tool_name, arguments=args)

# ---- Plan normalization ----
def normalize_plan(plan: dict) -> dict:
    if not isinstance(plan, dict) or plan.get("action") != "tool":
        raise ValueError(f"Invalid plan: {plan}")

    server, tool = plan["server"], plan["tool"]
    args = plan.get("args", {}) or {}

    # Hardcoded camera defaults
    if server == "camera" and tool == "take_photo":
        args.setdefault("device_index", 0)
        args.setdefault("width", 1920)
        args.setdefault("height", 1080)
        args.setdefault("warmup_frames", 10)

    # Hardcoded Opentrons configuration
    if server == "opentrons" and tool == "upload_and_run":
        args["protocol_path"] = OPENTRONS_PROTOCOL_PATH
        args["host"] = OPENTRONS_HOST
        args.setdefault("start", True)
        args.setdefault("wait", False)
        args.setdefault("poll_interval_s", 5)

    if server == "opentrons" and tool == "ping":
        args["host"] = OPENTRONS_HOST

    plan["args"] = args
    return plan

# ---- Main agent loop ----
def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Please set GEMINI_API_KEY environment variable.")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=SYSTEM_INSTRUCTIONS)

    print("🤖 Gemini 2.5 Pro Combined Agent ready!")
    print("- 'Take a photo.'")
    print("- 'Ping the Flex robot.'")
    print("- 'Upload and run the protocol.'")
    print("- 'Take a photo then run the protocol and wait.'")
    print("Ctrl+C to exit.\n")

    while True:
        try:
            user = input("You: ").strip()
            if not user:
                continue

            resp = model.generate_content([{"role": "user", "parts": user}])
            text = (resp.text or "").strip()

            plans = try_parse_plans(text)
            if not plans:
                print("Agent:", text)
                continue

            for i, raw_plan in enumerate(plans, start=1):
                try:
                    plan = normalize_plan(raw_plan)
                    server, tool, args = plan["server"], plan["tool"], plan["args"]

                    print(f"🔧 Step {i}: {server}.{tool} with args={args} ...")
                    result = asyncio.run(call_mcp(server, tool, args))
                    print("✅ Result:", json.dumps(result.model_dump(mode='json'), indent=2))
                except Exception as e:
                    print(f"❌ Tool error at step {i}: {e}")
                    break

        except KeyboardInterrupt:
            print("\n👋 Bye!")
            break

if __name__ == "__main__":
    main()
