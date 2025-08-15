from transcribe import transcribe_audio, assign_importance
from add_lyrics import make_ass, combine_video_audio, burn_subtitles
from remove_bg import add_foreground_to_background
from alter_video import make_cinematic, add_scanlines_and_glitches
from segmenting import find_highlights, combine_clips

# Testing behind person
"""#transcribe_audio('audio.MP4')
#make_ass("transcript.json", "subtitles.ass", resolution=(1024, 576))
burn_subtitles("test.mp4", "output_subtitles.mp4", "subtitles.ass")
add_foreground_to_background("test.mp4", "output_subtitles.mp4", "output_with_cutout.mp4")
combine_video_audio("output_with_cutout.mp4", "audio.mp4", "output_final.mp4")"""

# Testing adjustments
#add_scanlines_and_glitches("output_vhs.mp4", "output_vhs_2.mp4")
#make_cinematic("test.mp4", "output_vhs.mp4")

# Testing overall
transcribe_audio('audio.mp4', 'transcript.json')
assign_importance("transcript.json", "transcript_processed.json")
highlights = find_highlights("audio.mp4", "transcript_processed.json", num_clips=4)
combine_clips(["input.mp4", "input.mp4", "input.mp4", "input.mp4"], highlights, "output_highlights.mp4")
make_ass("transcript_processed.json", "subtitles.ass", "output_highlights.mp4")
burn_subtitles("output_highlights.mp4", "output_subtitles.mp4", "subtitles.ass")
combine_video_audio("output_subtitles.mp4", "audio.mp4", "output_final.mp4")