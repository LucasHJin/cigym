# Take video and add words with their timestamp and erase when segment ends
import json
from moviepy import VideoFileClip, TextClip, CompositeVideoClip

with open("transcript.json") as f:
    data = json.load(f)

segments = data['segments']

video = VideoFileClip("sample.MP4")
clips = []

for segment in segments:
    for word in segment['words']:
        start_time = word['start']
        duration = segment['end']-word['start']
        
        txt_clip = TextClip(text=word['word'], font_size=24, color='white', bg_color='black').with_start(start_time).with_duration(duration).with_position('center')
        
        clips.append(txt_clip)

final = CompositeVideoClip([video, *clips])
final.write_videofile("output_sample.mp4", codec="libx264", fps=video.fps)