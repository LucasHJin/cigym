import json
import ffmpeg

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
    
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {resolution[0]}
PlayResY: {resolution[1]}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H0000FFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2,0,2,30,30,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # Add each of the subtitle lines
    subtitles = []
    for segment in data['segments']:
        for word in segment['words']:
            start = convert_to_ass_time(word['start'])
            end = convert_to_ass_time(word['end'])
            text = word['word'].strip()
            line = f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
            subtitles.append(line)

    # Write to the ASS file
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(subtitles))

# IMPLEMENTATION -------------------------
# Create the ass file
make_ass("transcript.json", "subtitles.ass", resolution=(1024, 576))

# Burn ass subtitles onto the video
input = "sample.MP4"
ouput = "output_sample.mp4"
subtitles = "subtitles.ass"
ffmpeg.input(input).output(ouput, vf=f"ass={subtitles}", **{'c:a': 'copy'}).run()
