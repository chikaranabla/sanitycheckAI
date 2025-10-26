"""
MCP Client for Camera and Opentrons Integration
Windows対応版: 直接関数呼び出し方式
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional

# v2モジュールをインポートできるようにパスを追加
v2_path = Path(__file__).parent.parent / "v2"
if str(v2_path) not in sys.path:
    sys.path.insert(0, str(v2_path))

# カメラとOpentrons関数を直接インポート
import cv2
from datetime import datetime
import requests
import time


class MCPClient:
    """Windows対応: MCPサーバー機能を直接呼び出すクライアント"""
    
    def __init__(self):
        """Initialize MCP Client"""
        self.robot_base = os.getenv("OPENTRONS_HOST", "192.168.68.119:31950")
        if not self.robot_base.startswith("http"):
            self.robot_base = f"http://{self.robot_base}"
    
    def _opentrons_headers(self):
        """Opentrons API headers"""
        return {"Opentrons-Version": "*"}
    
    async def take_photo(
        self,
        device_index: int = 0,
        width: int = 1920,
        height: int = 1080,
        warmup_frames: int = 10
    ) -> str:
        """
        Capture a photo using the camera (直接実装版)
        
        Args:
            device_index: Camera device index (default: 0)
            width: Image width (default: 1920)
            height: Image height (default: 1080)
            warmup_frames: Number of warmup frames (default: 10)
            
        Returns:
            Absolute path to the captured image
        """
        try:
            # カメラを開く
            cam = cv2.VideoCapture(device_index)
            if not cam.isOpened():
                raise IOError(f"Cannot open webcam at index {device_index}. Check connection/permissions.")
            
            # 解像度設定
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, float(width))
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, float(height))
            
            # ウォームアップフレーム
            for _ in range(warmup_frames):
                cam.read()
            
            # 撮影
            ok, frame = cam.read()
            if not ok:
                cam.release()
                raise IOError("Failed to capture image from camera.")
            
            # 保存
            filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(filename, frame)
            
            # クリーンアップ
            cam.release()
            cv2.destroyAllWindows()
            
            return os.path.abspath(filename)
        except Exception as e:
            raise RuntimeError(f"Failed to capture photo: {str(e)}")
    
    async def ping_robot(self) -> Dict[str, Any]:
        """
        Ping the Opentrons robot to check health (直接実装版)
        
        Returns:
            Robot health status
        """
        try:
            response = requests.get(
                f"{self.robot_base}/health",
                headers=self._opentrons_headers(),
                timeout=8
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to ping robot at {self.robot_base}/health: {str(e)}")
    
    async def upload_and_run_protocol(
        self,
        protocol_path: str,
        start: bool = True,
        wait: bool = False,
        poll_interval_s: int = 5
    ) -> Dict[str, Any]:
        """
        Upload and run a protocol on the Opentrons robot (直接実装版)
        
        Args:
            protocol_path: Absolute path to the protocol file
            start: Whether to start the run immediately (default: True)
            wait: Whether to wait for completion (default: False)
            poll_interval_s: Polling interval in seconds (default: 5)
            
        Returns:
            Result containing protocol_id, run_id, and status
        """
        # Ensure absolute path
        abs_path = os.path.abspath(os.path.expanduser(protocol_path))
        
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Protocol file not found: {abs_path}")
        
        try:
            # 1) プロトコルをアップロード
            with open(abs_path, "rb") as f:
                files = {"files": f}
                response = requests.post(
                    f"{self.robot_base}/protocols",
                    headers=self._opentrons_headers(),
                    files=files,
                    timeout=90
                )
            response.raise_for_status()
            protocol_id = response.json()["data"]["id"]
            
            # 2) ランを作成
            payload = {"data": {"protocolId": protocol_id}}
            response = requests.post(
                f"{self.robot_base}/runs",
                headers=self._opentrons_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            run_id = response.json()["data"]["id"]
            
            result = {
                "protocol_id": protocol_id,
                "run_id": run_id,
                "started": False
            }
            
            # 3) ランを開始
            if start:
                play = {"data": {"actionType": "play"}}
                response = requests.post(
                    f"{self.robot_base}/runs/{run_id}/actions",
                    headers=self._opentrons_headers(),
                    json=play,
                    timeout=30
                )
                response.raise_for_status()
                result["started"] = True
            
            # 4) 完了を待機
            if wait:
                terminal_states = {"succeeded", "failed", "stopped", "canceled"}
                while True:
                    response = requests.get(
                        f"{self.robot_base}/runs/{run_id}",
                        headers=self._opentrons_headers(),
                        timeout=15
                    )
                    response.raise_for_status()
                    status = response.json().get("data", {}).get("status", "unknown")
                    
                    if status in terminal_states:
                        result["final_status"] = status
                        break
                    
                    await asyncio.sleep(poll_interval_s)
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Failed to upload and run protocol: {str(e)}")


# Singleton instance
_mcp_client = None


def get_mcp_client() -> MCPClient:
    """Get or create MCP client singleton"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client

