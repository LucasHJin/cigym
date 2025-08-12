from transcribe import transcribe_audio
from add_lyrics import make_ass, combine_video_audio, burn_subtitles
from remove_bg import add_foreground_to_background
from alter_video import make_cinematic, add_scanlines_and_glitches

# Testing behind person
"""#transcribe_audio('audio.MP4')
#make_ass("transcript.json", "subtitles.ass", resolution=(1024, 576))
burn_subtitles("test.mp4", "output_subtitles.mp4", "subtitles.ass")
add_foreground_to_background("test.mp4", "output_subtitles.mp4", "output_with_cutout.mp4")
combine_video_audio("output_with_cutout.mp4", "audio.mp4", "output_final.mp4")"""

# Testing adjustments
#make_vhs("test.mp4", "output_vhs.mp4")
#add_scanlines_and_glitches("output_vhs.mp4", "output_vhs_2.mp4")
#transcribe_audio('audio2.MP4')
make_ass("transcript.json", "subtitles.ass")
burn_subtitles("output_vhs.mp4", "output_subtitles.mp4", "subtitles.ass")
#combine_video_audio("output_subtitles.mp4", "audio2.MP4", "output_final.mp4")

#make_cinematic("test.mp4", "output_vhs.mp4")