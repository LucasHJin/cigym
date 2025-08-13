import librosa
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

def find_highlights(audio_file, num_clips=5):
    """
    Finds the highlight points in an audio and matches them with beat drops to help with video clip editing.
    
    Returns:
        highlight_times - array of chosen highlight timestamps
        
    Extra:
        hype_score - array of hype scores 
        beat_times - array of beat timestamps
    """
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

    # Detect beats
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)

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

            # Snap to nearest beat
            closest_beat = beat_times[np.argmin(np.abs(beat_times - peak_time))]
            selected.append(closest_beat)
        else:
            # Use middle beat
            middle = (start_t + end_t) / 2
            closest_beat = beat_times[np.argmin(np.abs(beat_times - middle))]
            selected.append(closest_beat)

    highlight_times = sorted(selected)
    return highlight_times

#highlights = find_highlights("audio.mp4", num_clips=4)
