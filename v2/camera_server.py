import os
import cv2
from datetime import datetime
from fastmcp import FastMCP

# Use 'name' not 'server_name'
mcp = FastMCP(name="camera-tools")

@mcp.tool()
def take_photo(
    device_index: int = 0,
    width: int = 1920,
    height: int = 1080,
    warmup_frames: int = 10
) -> str:
    """
    Capture a photo from a USB camera and save it with a timestamped filename.

    Args:
        device_index: Camera index (0 default).
        width, height: Desired resolution.
        warmup_frames: Number of frames to warm up the camera.

    Returns:
        Absolute path of the saved image.
    """
    cam = cv2.VideoCapture(device_index)
    if not cam.isOpened():
        raise IOError(f"Cannot open webcam at index {device_index}. Check connection/permissions.")
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, float(width))
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, float(height))
    for _ in range(warmup_frames):
        cam.read()
    ok, frame = cam.read()
    if not ok:
        cam.release()
        raise IOError("Failed to capture image from camera.")
    filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    cv2.imwrite(filename, frame)
    cam.release()
    cv2.destroyAllWindows()
    return os.path.abspath(filename)

if __name__ == "__main__":
    mcp.run()
