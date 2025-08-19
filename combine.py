from transcribe import transcribe_audio, assign_importance
from add_lyrics import make_ass, combine_video_audio, burn_subtitles
from remove_bg import add_foreground_to_background
from alter_video import make_cinematic, add_scanlines_and_glitches
from segmenting import find_highlights, combine_clips

def initial_processing(num_clips, min_start_time, highlights2=[]):
    """All steps for processing the video the first time."""
    transcribe_audio('audio.mp4', 'transcript.json')
    assign_importance("transcript.json", "transcript_processed.json")
    highlights = find_highlights("audio.mp4", "transcript_processed.json", num_clips, min_start_time)
    combine_clips(["input1.mp4", "input2.mp4", "input3.mp4", "input4.mp4", "input5.mp4"], highlights, "output_highlights.mp4")
    make_ass("transcript_processed.json", "subtitles.ass", "output_highlights.mp4")
    combine_video_audio("output_highlights.mp4", "audio.mp4", "output_audio.mp4")
    burn_subtitles("output_audio.mp4", "output_subtitles.mp4", "subtitles.ass")
    
def repeated_processing(temp_path):
    """Steps for processing the video after initial processing (don't re transcribe/assign importance/highlight)"""
    make_ass("transcript_processed.json", "subtitles.ass", "output_highlights.mp4")
    combine_video_audio("output_highlights.mp4", "audio.mp4", "output_audio.mp4")
    burn_subtitles("output_audio.mp4", temp_path, "subtitles.ass")
    
# FXN call if needed to fix any issues relating to adding more clips
# initial_processing(5, 2.0, [6.67, 19.1, 19.2, 19.3, 21.31591836734694])