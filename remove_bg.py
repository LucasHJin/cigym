import torch
import cv2
import numpy as np
from model import MattingNetwork

def add_foreground_to_background(input_video, background_video, output_video):
    # Settings
    device = "cpu"
    model_path = "models/rvm_mobilenetv3.pth"
    downsample_ratio = 0.8 # 0-1, higher = better but slower
    
    # Load the model
    model = MattingNetwork("mobilenetv3").eval().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))

    # Open foreground video
    cap_fg = cv2.VideoCapture(input_video)
    if not cap_fg.isOpened():
        raise RuntimeError(f"Failed to open input video: {input_video}")

    # Open background video
    cap_bg = cv2.VideoCapture(background_video)
    if not cap_bg.isOpened():
        raise RuntimeError(f"Failed to open background video: {background_video}")

    # Metadata (assuming both videos have same size & fps)
    fps = cap_fg.get(cv2.CAP_PROP_FPS)
    width = int(cap_fg.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap_fg.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap_fg.get(cv2.CAP_PROP_FRAME_COUNT))

    # Setup output video writer (no alpha)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v") # type: ignore
    print(fourcc)
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    rec = [None] * 4
    frame_num = 0

    while True:
        # Is it readable, actual data
        ret_fg, frame_fg = cap_fg.read()
        ret_bg, frame_bg = cap_bg.read()

        if not ret_fg or not ret_bg:
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
        src = torch.from_numpy(frame_fg[:, :, ::-1].copy()).permute(2, 0, 1).float() / 255.0
        src = src.unsqueeze(0).to(device)

        # Run model
        #   fgr -> RGB image of person
        #   alpha -> alpha mask - grayscale image defining how transparent each pixel is
        with torch.no_grad():
            fgr, alpha, *rec = model(src, *rec, downsample_ratio=downsample_ratio)

        # Convert to numpy
        fgr_np = (fgr[0].permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
        alpha_np = (alpha[0, 0].cpu().numpy() * 255).astype(np.uint8)

        if alpha_np.ndim != 2 or alpha_np.size == 0:
            print(f"Skipping frame {frame_num} due to invalid alpha shape: {alpha_np.shape}")
            continue

        # Post-process alpha mask
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

        # Normalize alpha mask to 0-1 float for blending
        alpha_norm = alpha_np.astype(np.float32) / 255.0
        alpha_3c = np.repeat(alpha_norm[:, :, np.newaxis], 3, axis=2)
        
        # Convert model's RGB output to BGR to match OpenCV
        fgr_bgr = cv2.cvtColor(fgr_np, cv2.COLOR_RGB2BGR)

        # Combine foreground and background
        composite = (alpha_3c * fgr_bgr.astype(np.float32) + (1 - alpha_3c) * frame_bg.astype(np.float32)).astype(np.uint8)

        # Write combined frame to output
        out.write(composite)

    # Cleanup
    cap_fg.release()
    cap_bg.release()
    out.release()

    print(f"Saved composited video to: {output_video}")

#add_foreground_to_background('test.mp4', 'output_final.mp4', 'output_with_cutout.mp4')