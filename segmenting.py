import librosa
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import json
from paths import add_io_dir

# MAYBE CHANGE SO HIGHLIGHTS IS BASED ON MEDIAN FOR EACH SPLIT UP SEGMENT

def find_highlights(audio_file, transcript_json, num_clips=5):
    """
    Finds the highlight points in an audio and matches them with beat drops to help with video clip editing.
    
    Returns:
        highlight_times - array of chosen highlight timestamps
    """
    audio_file = add_io_dir(audio_file)
    transcript_json = add_io_dir(transcript_json)
    
    num_clips -= 1
    
    # Load transcript
    with open(transcript_json, "r") as f:
        transcript_json = json.load(f)
    
    # Load audio
    if audio_file.endswith(".mp4"):
        subprocess.run(["ffmpeg", "-y", "-i", audio_file, "-vn", "-ac", "2", "-ar", "44100", "audio.wav"])
        audio_file = "audio.wav"
    y, sr = librosa.load(audio_file, sr=None)

    # Find RMS (volume) + onset strength (any suddenly loud parts, i.e. beat drops)
    hop_length = 512
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)

    # Normalize features (equalize relative to each other)
    rms_norm = (rms - rms.min()) / (rms.max() - rms.min())
    onset_norm = (onset_env - onset_env.min()) / (onset_env.max() - onset_env.min())

    # Find peaks from single 'hype' data set
    hype_score = 0.6 * rms_norm + 0.4 * onset_norm
    times = librosa.frames_to_time(np.arange(len(hype_score)), sr=sr, hop_length=hop_length)
    peaks, _ = find_peaks(hype_score, height=np.median(hype_score))

    # Pick best peak in each section
    duration = times[-1]
    section_length = duration / num_clips
    selected = []
    for i in range(num_clips):
        start_t = i * section_length
        end_t = (i + 1) * section_length

        # Find peaks in this section
        section_indices = [p for p in peaks if start_t <= times[p] < end_t]

        if section_indices:
            # Highest hype score
            best_peak = max(section_indices, key=lambda x: hype_score[x])
            peak_time = times[best_peak]
            selected.append(peak_time)
            
    highlight_times = []
    if transcript_json:
        # Flatten all words with their start/end times
        words_list = []
        for seg in transcript_json["segments"]:
            for w in seg["words"]:
                words_list.append(w)

        # Match each highlight to the closest word
        for t in selected:
            closest_word = min(words_list, key=lambda w: abs(w["start"] - t))
            highlight_times.append(closest_word["start"])

    duration = librosa.get_duration(y=y, sr=sr)
    highlight_times.append(duration) # Need last segment to end when audio ends

    highlight_times = sorted(highlight_times)
    
    return highlight_times

def combine_clips(video_files, highlight_timestamps, output_file):
    """
    Trims multiple video files at given timestamps and concatenates them using filter_complex.
    If a segment's duration is longer than the remaining clip length, the leftover duration
    is rolled over to the start of the next clip.
    """
    output_file = add_io_dir(output_file)
    
    filters = []
    inputs = []
    concat_inputs = []

    leftover = 0  # Leftover duration from previous clip (if it wasn't long enough)

    for i, video in enumerate(video_files):
        video = add_io_dir(video)
        clip_length = get_video_duration(video)

        desired_duration = 0

        # Determine desired duration for this clip
        if i == 0:
            desired_duration = highlight_timestamps[0]
        elif i < len(highlight_timestamps):
            desired_duration = (highlight_timestamps[i] - highlight_timestamps[i-1]) + leftover

        # Trim logic
        if desired_duration <= clip_length:
            start = 0
            duration = desired_duration
            leftover = 0
        else:
            start = 0
            duration = clip_length
            leftover = desired_duration - clip_length  # Carry over to next clip

        if duration <= 0:
            continue  # skip clips that have nothing to trim

        # Add input and filter
        inputs.extend(["-i", video])
        filters.append(f"[{i}:v]trim=start={start}:duration={duration},setpts=PTS-STARTPTS[v{i}];")
        concat_inputs.append(f"[v{i}]")

    # Concatenate all segments
    if concat_inputs:
        filter_complex = "".join(filters) + f"{''.join(concat_inputs)}concat=n={len(concat_inputs)}:v=1:a=0[outv]"
        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            output_file
        ]
        subprocess.run(cmd)

    
def get_video_duration(video_file):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", video_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return float(result.stdout.strip())