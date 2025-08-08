import torch # Runs the RVM deep learning model
import cv2 # Handles video/image processing
import numpy as np 
import subprocess # Runs ffmpeg for final transparent video
from model import MattingNetwork 

# Settings
device = "cpu"
model_path = "models/rvm_mobilenetv3.pth"
input_video = "test.mp4"
output_video = "cutout.mov"
downsample_ratio = 0.75 # 0-1, higher = better but slower

# Load the model
model = MattingNetwork("mobilenetv3").eval().to(device)
model.load_state_dict(torch.load(model_path, map_location=device))

# Read the input video
cap = cv2.VideoCapture(input_video)
if not cap.isOpened():
    raise RuntimeError(f"Failed to open input video: {input_video}")
# Metadata
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

if fps <= 0 or width <= 0 or height <= 0:
    raise ValueError("Invalid video metadata — check your input video file.")

# Runs ffmpeg as a subprocess (eliminate need for saving temp files)
ffmpeg_cmd = [
    "ffmpeg",
    "-y",  # Overwrite output
    "-f", "rawvideo",
    "-pix_fmt", "rgba",
    "-s", f"{width}x{height}",
    "-r", str(fps),
    "-i", "-",  # Read from stdin
    "-an",  # Disable audio in output
    "-c:v", "prores_ks",
    "-pix_fmt", "yuva444p10le",
    output_video
]
ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
if ffmpeg_proc.stdin is None:
    raise RuntimeError("ffmpeg process stdin is None; cannot write frames.")

# RVM recurrent states -> memory across frames for smoother video
rec = [None] * 4

frame_num = 0
# Main processing loop (one frame per time)
while True:
    ret, frame_bgr = cap.read()
    if not ret:
        print("No more frames or error reading frame.")
        break
    frame_num += 1
    print(f"Processing frame {frame_num}/{frame_count}")

    # Prepare the frame for model
    #   BGR -> RGB
    #   change shape
    #   convert float to 0-1
    #   add a batch dimension in front of chw
    #   change to CPU
    src = torch.from_numpy(frame_bgr[:, :, ::-1].copy()).permute(2, 0, 1).float() / 255.0
    src = src.unsqueeze(0).to(device)

    # Run the model
    #   fgr -> RGB image of person
    #   alpha -> alpha mask - grayscale image defining how transparent each pixel is
    with torch.no_grad():
        fgr, alpha, *rec = model(src, *rec, downsample_ratio=downsample_ratio)

    # Convert output into OpenCV processable arrays
    fgr_np = (fgr[0].permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
    alpha_np = (alpha[0, 0].cpu().numpy() * 255).astype(np.uint8)

    if alpha_np.ndim != 2 or alpha_np.size == 0:
        print(f"Skipping frame {frame_num} due to invalid alpha shape: {alpha_np.shape}")
        continue

    # Post processing alpha
    #   Smooth edges
    alpha_np = cv2.bilateralFilter(alpha_np, d=9, sigmaColor=75, sigmaSpace=75)
    #   Sharpen mask
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    alpha_np = cv2.filter2D(alpha_np, -1, kernel)
    #   Adjust contrast
    alpha_float = alpha_np.astype(np.float32) / 255.0
    gamma = 0.8
    alpha_np = (np.power(alpha_float, gamma) * 255).astype(np.uint8)
    #   Make edges hard (i.e. no blur -> opaque/transparent)
    alpha_threshold = 200
    alpha_np = (alpha_np > alpha_threshold).astype(np.uint8) * 255

    # Double check that alpha_np has correct shape + convert to rbga data
    alpha_np = alpha_np.reshape(height, width)
    rgba = np.dstack((fgr_np, alpha_np))

    # Send raw pixel data to ffmpeg to convert to  mov
    ffmpeg_proc.stdin.write(rgba.tobytes())

# Close all processes
cap.release()
ffmpeg_proc.stdin.close()
ffmpeg_proc.wait()

print(f"Saved transparent video to: {output_video}")