import subprocess
import cv2
import numpy as np
import random
from paths import add_io_dir

# Now cut clips


def make_cinematic(input_file, output_file):
    input_file = add_io_dir(input_file)
    output_file = add_io_dir(output_file)

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-vf",
        (
            "scale=iw*0.95:ih*0.95:flags=bicubic,"
            "eq=contrast=1.3:brightness=-0.25:saturation=0.69:gamma=0.83,"
            "colorchannelmixer="
            "rr=0.88:rg=0:rb=0.12:"
            "gr=0:gg=0.78:gb=0.22:"
            "br=0.05:bg=0.15:bb=1.25,"
            "vignette,"
            "unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount=1.0"
        ),
        "-c:v",
        "libx264",
        "-crf",
        "20",
        "-preset",
        "slow",
        output_file,
    ]
    subprocess.run(ffmpeg_cmd, check=True)


def add_scanlines_and_glitches(input_file, output_file):
    input_file = add_io_dir(input_file)
    output_file = add_io_dir(output_file)

    # Open the video file
    cap = cv2.VideoCapture(input_file)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Setup output video writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

    # Go through video and add scanlines + random glitches
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:  # Check if frame was read successfully
            break

        # Scanline every 5 lines (70% opacity)
        for y in range(0, height, 5):
            frame[y : y + 1, :, :] = (frame[y : y + 1, :, :] * 0.7).astype(np.uint8)

        # Random glitch lines (7% each frame)
        if random.random() < 0.07:
            glitch_y = random.randint(0, height - 3)
            thickness = random.randint(1, 3)
            # Add glitch line (with a mask)
            glitch_mask = np.zeros_like(frame, dtype=np.uint8)
            cv2.line(
                glitch_mask,
                (0, glitch_y),
                (width, glitch_y),
                (255, 255, 255),
                thickness,
            )
            # Blur the line
            blurred_mask = cv2.GaussianBlur(glitch_mask, (7, 7), sigmaX=3)
            # Add line to frame
            frame = cv2.addWeighted(frame, 1.0, blurred_mask, 0.6, 0)

        out.write(frame)

    # Clean up
    cap.release()
    out.release()
