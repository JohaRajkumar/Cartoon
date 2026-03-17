import argparse
import os
import subprocess
import sys

# make this script useful with command-line options
parser = argparse.ArgumentParser(description="Run Cartoon Project Streamlit server")
parser.add_argument("--port", default="8501", help="Streamlit server port")
parser.add_argument("--address", default="0.0.0.0", help="Streamlit server address")
parser.add_argument("--nogui", action="store_true", help="Do not open browser (Streamlit behavior depends on streamlit version)")
args = parser.parse_args()

# Ensure .streamlit/config.toml can be overridden, but default is set as fallback
os.environ.setdefault("STREAMLIT_SERVER_PORT", args.port)
os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", args.address)
os.environ.setdefault("STREAMLIT_SERVER_ENABLECORS", "false")
os.environ.setdefault("STREAMLIT_SERVER_ENABLEXSRFPROTECTION", "false")

# Use venv python executable
python_executable = sys.executable

command = [
    python_executable,
    "-m",
    "streamlit",
    "run",
    "app.py",
    "--server.port",
    args.port,
    "--server.address",
    args.address,
]
if args.nogui:
    command.append("--server.headless")
    command.append("true")

print(f"Starting Cartoon Project Streamlit server on http://{args.address}:{args.port}")
print("Command:", " ".join(command))

try:
    subprocess.run(command, check=True)
except KeyboardInterrupt:
    print("Interrupted by user. Shutting down.")
except subprocess.CalledProcessError as e:
    print(f"Streamlit exited with code {e.returncode}")
    sys.exit(e.returncode)

