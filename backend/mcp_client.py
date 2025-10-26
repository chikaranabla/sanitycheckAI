"""
MCP Client for Camera and Opentrons Integration
"""

import os
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """MCP Client to interact with camera and Opentrons servers"""
    
    def __init__(self):
        """Initialize MCP Client"""
        # Get the v2 directory path
        self.v2_dir = Path(__file__).parent.parent / "v2"
        
        # MCP server commands
        self.camera_server_cmd = ["python", str(self.v2_dir / "camera_server.py")]
        self.opentrons_server_cmd = ["python", str(self.v2_dir / "opentrons_server.py")]
    
    async def _call_mcp(self, server: str, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        Call an MCP tool
        
        Args:
            server: Server name ("camera" or "opentrons")
            tool_name: Tool name to call
            args: Arguments for the tool
            
        Returns:
            Tool execution result
        """
        if server == "camera":
            server_cmd = self.camera_server_cmd
        elif server == "opentrons":
            server_cmd = self.opentrons_server_cmd
        else:
            raise ValueError(f"Unknown server: {server}")
        
        params = StdioServerParameters(command=server_cmd[0], args=server_cmd[1:])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=args)
                return result
    
    async def take_photo(
        self,
        device_index: int = 0,
        width: int = 1920,
        height: int = 1080,
        warmup_frames: int = 10
    ) -> str:
        """
        Capture a photo using the camera
        
        Args:
            device_index: Camera device index (default: 0)
            width: Image width (default: 1920)
            height: Image height (default: 1080)
            warmup_frames: Number of warmup frames (default: 10)
            
        Returns:
            Absolute path to the captured image
        """
        args = {
            "device_index": device_index,
            "width": width,
            "height": height,
            "warmup_frames": warmup_frames
        }
        
        try:
            result = await self._call_mcp("camera", "take_photo", args)
            # Extract the image path from the result
            if hasattr(result, 'content'):
                # MCP result has content attribute
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        return content_item.text
            return str(result)
        except Exception as e:
            raise RuntimeError(f"Failed to capture photo: {str(e)}")
    
    async def ping_robot(self) -> Dict[str, Any]:
        """
        Ping the Opentrons robot to check health
        
        Returns:
            Robot health status
        """
        try:
            result = await self._call_mcp("opentrons", "ping", {})
            # Parse the result
            if hasattr(result, 'content'):
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        return json.loads(content_item.text)
            return json.loads(str(result))
        except Exception as e:
            raise RuntimeError(f"Failed to ping robot: {str(e)}")
    
    async def upload_and_run_protocol(
        self,
        protocol_path: str,
        start: bool = True,
        wait: bool = False,
        poll_interval_s: int = 5
    ) -> Dict[str, Any]:
        """
        Upload and run a protocol on the Opentrons robot
        
        Args:
            protocol_path: Absolute path to the protocol file
            start: Whether to start the run immediately (default: True)
            wait: Whether to wait for completion (default: False)
            poll_interval_s: Polling interval in seconds (default: 5)
            
        Returns:
            Result containing protocol_id, run_id, and status
        """
        # Ensure absolute path
        abs_path = os.path.abspath(protocol_path)
        
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Protocol file not found: {abs_path}")
        
        args = {
            "protocol_path": abs_path,
            "start": start,
            "wait": wait,
            "poll_interval_s": poll_interval_s
        }
        
        try:
            result = await self._call_mcp("opentrons", "upload_and_run", args)
            # Parse the result
            if hasattr(result, 'content'):
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        return json.loads(content_item.text)
            return json.loads(str(result))
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

