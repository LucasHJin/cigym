import json
import ffmpeg
import math

# FUNCTIONS -------------------------
def convert_to_ass_time(seconds: float) -> str:
    """Convert seconds to ASS timestamp format - H:MM:SS.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"

def make_ass(json_path, ass_path, resolution=(1024, 576)):
    """Create ASS file with timestamps and settings."""
    with open(json_path) as f:
        data = json.load(f)

    # Header
    '''
    HEADER SECTIONS:
        Script Info - metadata and global settings
        V4+ Styles - defines styles (subtitle appearances)
            Format - defines what is required for each style
            I.e. a Default style (can choose which one to call in events section)
        Events - actual timed subtitles
            Format - defines what is required for each subtitle
            Dialogue - the text to be displayed (can change effect here)
    '''
    
    # GET AN AI TO DECIDE THE STYLING
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {resolution[0]}
PlayResY: {resolution[1]}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Didot,80,&H00FFFFFF,&H0000FF,&H00000000,&H00000000,0,0,0,0,100,120,0,0,1,0,0,5,30,30,60,1
Style: Default-Red,Didot,80,&H0000FF,&H00000000,&H00000000,&H00000000,0,0,0,0,100,120,0,0,1,0,0,5,30,30,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # Add each of the subtitle lines
    subtitles = []
    
    for segment in data['segments']:
        for word in segment['words']:
            word_text = word['word'].strip()
            start_time = word['start']
            end_time = word['end']
            duration = end_time - start_time
            
            # CHANGE TO NOT BE BASED ON DURATION BUT SOMETHING ELSE
            if duration > 0.5:
                styles = [
                    "Default",
                    "Default-Red",
                ]
                switch_interval = 0.04 
                flicker_text(start_time, end_time, word_text, subtitles, styles, switch_interval)
            else:
                normal_text(start_time, end_time, word_text, subtitles)

    # Write to the ASS file
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(subtitles))

def normal_text(start_time, end_time, word_text, subtitles):
    """Add the normal text for the subtitles."""
    start = convert_to_ass_time(start_time)
    end = convert_to_ass_time(end_time)
    text = word_text.strip()
    line = f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
    subtitles.append(line)

def flicker_text(start_time, end_time, word_text, subtitles, styles, switch_interval=0.05):
    """Add rapidly changing styles for subtitles."""
    duration = end_time - start_time
    num_chunks = math.ceil(duration / switch_interval)
    actual_interval = duration / num_chunks

    for i in range(num_chunks):
        chunk_start = start_time + i * actual_interval
        chunk_end = chunk_start + actual_interval
        style = styles[i % len(styles)]

        ass_start = convert_to_ass_time(chunk_start)
        ass_end = convert_to_ass_time(min(chunk_end, end_time))

        line = f"Dialogue: 0,{ass_start},{ass_end},{style},,0,0,0,,{word_text}"
        subtitles.append(line)

def burn_subtitles(input, output, subtitles):
    ffmpeg.input(input).output(output, vf=f"ass={subtitles}", acodec='copy').global_args('-y').run()

def combine_video_audio(video_input, audio_input, output):
    video = ffmpeg.input(video_input)
    audio = ffmpeg.input(audio_input)

    ffmpeg.output(video.video, audio.audio, output, vcodec='copy', acodec='aac', shortest=None).global_args('-y').run()
    

# IMPLEMENTATION -------------------------
# Create the ass file
make_ass("transcript.json", "subtitles.ass", resolution=(1024, 576))

# Add audio to the video
combine_video_audio("test.mp4", "audio.mp4", "video_with_audio.mp4")

# Add subtitles to the video
burn_subtitles("video_with_audio.mp4", "output_final.mp4", "subtitles.ass")