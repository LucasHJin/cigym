import json
import ffmpeg
import math
import random

# CHANGE LIST TO BE RIGHT
FONTS = [
    {"font": "American Typewriter", "styles": ["Condensed Light", "Condensed", "Condensed Bold", "Light", "Regular", "Bold"], "type": "serif"},
    {"font": "Apple Chancery", "styles": ["Regular"], "type": "script"},
    {"font": "Baskerville", "styles": ["Regular", "Italic", "Semi-bold", "Semi-bold Italic", "Bold", "Bold Italic"], "type": "serif"},
    {"font": "Brush Script", "styles": ["Italic"], "type": "script"},
    {"font": "Chalkboard", "styles": ["Regular", "Bold"], "type": "display"},
    {"font": "Chalkduster", "styles": ["Regular"], "type": "display"},
    {"font": "Cochin", "styles": ["Regular", "Italic", "Bold", "Bold Italic"], "type": "serif"},
    {"font": "Comic Sans", "styles": ["Regular", "Bold"], "type": "display"},
    {"font": "Cooper", "styles": ["Black"], "type": "display"},
    {"font": "Copperplate", "styles": ["Light", "Regular", "Bold"], "type": "display"},
    {"font": "Didot", "styles": ["Regular", "Italic", "Bold"], "type": "serif"},
    {"font": "Herculanum", "styles": ["Regular"], "type": "display"},
    {"font": "Hoefler Text", "styles": ["Regular", "Italic", "Black", "Black Italic", "Ornaments"], "type": "serif"},
    {"font": "Impact", "styles": ["Regular"], "type": "display"},
    {"font": "Kuenstler Script", "styles": ["Regular", "Black"], "type": "script"},
    {"font": "Marker Felt", "styles": ["Thin", "Wide"], "type": "display"},
    {"font": "Optima", "styles": ["Regular", "Italic", "Bold", "Bold Italic", "Extra Black"], "type": "display"},
    {"font": "Palatino", "styles": ["Regular", "Italic", "Bold", "Bold Italic"], "type": "serif"},
    {"font": "Papyrus", "styles": ["Regular", "Condensed"], "type": "display"},
    {"font": "Plantagenet Cherokee", "styles": ["Regular"], "type": "display"},
    {"font": "Skia", "styles": ["Light", "Light Condensed", "Light Extended", "Regular", "Condensed", "Extended", "Bold", "Black", "Black Condensed", "Black Extended"], "type": "display"},
    {"font": "Snell Roundhand", "styles": ["Regular"], "type": "script"},
    {"font": "Techno", "styles": ["Regular"], "type": "display"},
    {"font": "Textile", "styles": ["Regular"], "type": "display"},
    {"font": "Times", "styles": ["Regular", "Italic", "Bold", "Bold Italic"], "type": "serif"},
    {"font": "Times New Roman", "styles": ["Regular", "Italic", "Bold", "Bold Italic"], "type": "serif"},
    {"font": "Zapf Chancery", "styles": ["Medium Italic"], "type": "script"},
    {"font": "Zapfino", "styles": ["Regular"], "type": "script"},
]

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

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {resolution[0]}
PlayResY: {resolution[1]}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""

    # Generate style entries from FONTS
    style_template = "Style: {name},{fontname},100,{primary},{secondary},{outline},{back},0,0,0,0,100,120,0,0,0,0,0,5,30,30,60,1\n"
    primary_white = "&H00FFFFFF" # White
    primary_red = "&H000000FF" # Red (BGR)
    secondary = "&H00000000"
    outline = "&H00000000"
    back = "&H00000000"

    styles_text = ""
    for font in FONTS:
        fontname = font["font"]
        # White style
        style_name_white = fontname
        styles_text += style_template.format(
            name=style_name_white,
            fontname=fontname,
            primary=primary_white,
            secondary=secondary,
            outline=outline,
            back=back,
        )
        # Red style
        style_name_red = f"{fontname} Red"
        styles_text += style_template.format(
            name=style_name_red,
            fontname=fontname,
            primary=primary_red,
            secondary=secondary,
            outline=outline,
            back=back,
        )

    header += styles_text
    header += """
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    subtitles = []

    for segment in data['segments']:
        for word in segment['words']:
            word_text = word['word'].strip()
            start_time = word['start']
            end_time = word['end']
            duration = end_time - start_time
            
            # CHANGE TO NOT BE BASED ON DURATION BUT SOMETHING ELSE
            if duration > 0.8:
                switch_interval = 0.08
                flicker_text(start_time, end_time, word_text, subtitles, FONTS, switch_interval) # NOT JUST FONTS BUT ALL STYLES LATER
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
    line = f"Dialogue: 0,{start},{end},Didot,,0,0,0,,{text}"
    subtitles.append(line)

def flicker_text(start_time, end_time, word_text, subtitles, fonts, switch_interval=0.05):
    """Add rapidly changing styles for subtitles."""
    duration = end_time - start_time
    num_chunks = math.ceil(duration / switch_interval)
    actual_interval = duration / num_chunks

    style_names = []
    for font in fonts:
        style_names.append(font["font"])
        style_names.append(f"{font['font']} Red")

    for i in range(num_chunks):
        chunk_start = start_time + i * actual_interval
        chunk_end = chunk_start + actual_interval

        style = random.choice(style_names)

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
'''# Create the ass file
make_ass("transcript.json", "subtitles.ass", resolution=(1024, 576))

# Add audio to the video
combine_video_audio("test.mp4", "audio.mp4", "video_with_audio.mp4")

# Add subtitles to the video
burn_subtitles("video_with_audio.mp4", "output_final.mp4", "subtitles.ass")'''