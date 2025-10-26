import cv2
from datetime import datetime

# Open the default camera (0). If you have multiple, try 1 or 2 instead.
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    raise IOError("Cannot open webcam. Check your USB connection or permissions.")

# Optional: set resolution (you can comment these out if not needed)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# Warm up the camera
for _ in range(10):
    ret, frame = camera.read()

# Capture one frame
ret, frame = camera.read()
if not ret:
    raise IOError("Failed to capture image from camera.")

# Create filename with timestamp
filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

# Save image
cv2.imwrite(filename, frame)
print(f"Photo saved as {filename}")

# Release resources
camera.release()
cv2.destroyAllWindows()
