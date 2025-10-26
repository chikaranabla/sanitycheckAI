"""
Configuration for V2 MCP Servers
"""

import os

# Opentrons Robot Configuration
OPENTRONS_HOST = os.getenv("OPENTRONS_HOST", "192.168.68.119:31950")
OPENTRONS_BASE_URL = f"http://{OPENTRONS_HOST}"

# Camera Configuration
CAMERA_DEVICE_INDEX = int(os.getenv("CAMERA_DEVICE_INDEX", "0"))
CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "1920"))
CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "1080"))
CAMERA_WARMUP_FRAMES = int(os.getenv("CAMERA_WARMUP_FRAMES", "10"))

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

# Session Configuration
SESSION_TEMP_DIR = os.getenv("SESSION_TEMP_DIR", "/tmp/sanitycheckAI_sessions")

