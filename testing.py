from transcribe import transcribe_audio
from add_lyrics import make_ass, combine_video_audio, burn_subtitles
from remove_bg import add_foreground_to_background

# Code logic for testing
#transcribe_audio('audio.MP4')
#make_ass("transcript.json", "subtitles.ass", resolution=(1024, 576))
burn_subtitles("test.mp4", "output_subtitles.mp4", "subtitles.ass")
add_foreground_to_background("test.mp4", "output_subtitles.mp4", "output_with_cutout.mp4")
combine_video_audio("output_with_cutout.mp4", "audio.mp4", "output_final.mp4")