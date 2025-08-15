import json
import ffmpeg
import math
import random
from paths import add_io_dir

# CHANGE LIST TO BE RIGHT
FONTS = [
    {"font": "Academy Engraved LET", "styles": [""]},
    {"font": "American Typewriter", "styles": ["", "Light", "Semibold", "Condensed Light", "Condensed", "Condensed Bold"]},
    {"font": "Annai MN", "styles": [""]},
    {"font": "Apple Chancery", "styles": [""]},
    {"font": "Baskerville", "styles": ["", "Italic", "SemiBold Italic"]},
    {"font": "Big Caslon", "styles": [""]},
    {"font": "Bodoni 72", "styles": ["", "Book", "Book Italic", "Bold"]},
    {"font": "Bradley Hand", "styles": [""]},
    {"font": "Brill", "styles": ["", "Italic"]},
    {"font": "Brush Script MT", "styles": [""]},
    {"font": "Canela", "styles": [""]},
    {"font": "Chalkduster", "styles": [""]},
    {"font": "Charter", "styles": ["", "Italic", "Black"]},
    {"font": "Cochin", "styles": ["", "Italic"]},
    {"font": "Copperplate", "styles": ["", "Light", "Bold"]},
    {"font": "Courier New", "styles": ["", "Italic"]},
    {"font": "Didot", "styles": ["", "Italic"]},
    {"font": "DIN Condensed", "styles": [""]},
    {"font": "Domaine Display", "styles": [""]},
    {"font": "Herculanum", "styles": [""]},
    {"font": "Hoefler Text", "styles": ["", "Italic"]},
    {"font": "Impact", "styles": [""]},
    {"font": "Luminari", "styles": [""]},
    {"font": "Marker Felt", "styles": ["", "Wide"]},
    {"font": "Noteworthy", "styles": ["", "Bold"]},
    {"font": "Optima", "styles": ["", "Italic", "Bold"]},
    {"font": "Palatino", "styles": [""]},
    {"font": "Papyrus", "styles": [""]},
    {"font": "Party LET", "styles": [""]},
    {"font": "Phosphate", "styles": ["", "Inline"]},
    {"font": "Quotes Caps", "styles": [""]},
    {"font": "Quotes Script", "styles": [""]},
    {"font": "Rockwell", "styles": [""]},
    {"font": "Sauber Script", "styles": [""]},
    {"font": "Savoye LET", "styles": [""]},
    {"font": "SignPainter", "styles": [""]},
    {"font": "Skia", "styles": ["", "Light"]},
    {"font": "Snell Roundhand", "styles": [""]},
    {"font": "Trattatello", "styles": [""]},
    {"font": "Zapfino", "styles": [""]},
]

ass_styles = []

# FUNCTIONS -------------------------
def convert_to_ass_time(seconds: float) -> str:
    """Convert seconds to ASS timestamp format - H:MM:SS.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"

def make_ass(json_path, ass_path, video_path):
    """Create ASS file with timestamps and settings."""
    json_path = add_io_dir(json_path)
    ass_path = add_io_dir(ass_path)
    video_path = add_io_dir(video_path)

    resolution = get_video_resolution(video_path)
    width = resolution[0]
    height = resolution[1]

    with open(json_path) as f:
        data = json.load(f)

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""

    # Generate style entries from FONTS
    style_template = "Style: {name},{fontname},250,{primary},{secondary},{outline},{back},0,0,0,0,100,110,0,0,0,0,0,5,30,30,60,1\n"
    primary_white = "&H00FFFFFF" # White
    primary_red = "&H000000FF" # Red (BGR)
    secondary = "&H00000000"
    outline = "&H00000000"
    back = "&H00000000"

    styles_text = ""

    for font in FONTS:
        base_fontname = font["font"]
        styles = font.get("styles", [""])

        for style_suffix in styles:
            full_fontname = base_fontname
            if style_suffix.strip():
                full_fontname += " " + style_suffix

            # White style
            style_name_white = full_fontname
            styles_text += style_template.format(
                name=style_name_white,
                fontname=full_fontname,
                primary=primary_white,
                secondary=secondary,
                outline=outline,
                back=back,
            )
            # Red style
            style_name_red = f"{full_fontname} Red"
            styles_text += style_template.format(
                name=style_name_red,
                fontname=full_fontname,
                primary=primary_red,
                secondary=secondary,
                outline=outline,
                back=back,
            )

            ass_styles.append(style_name_white)
            ass_styles.append(style_name_red)

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
            importance = word['importance']

            if importance == 2:
                switch_interval = 0.05
                flicker_text(start_time, end_time, word_text, subtitles, ass_styles, switch_interval) # NOT JUST FONTS BUT ALL STYLES LATER
            elif importance == 1:
                red_text(start_time, end_time, word_text, subtitles)
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
    
def red_text(start_time, end_time, word_text, subtitles):
    """Add the red text for the subtitles."""
    start = convert_to_ass_time(start_time)
    end = convert_to_ass_time(end_time)
    text = word_text.strip()
    line = f"Dialogue: 0,{start},{end},Didot Red,,0,0,0,,{text}"
    subtitles.append(line)

def flicker_text(start_time, end_time, word_text, subtitles, styles, switch_interval=0.05):
    """Add rapidly changing styles for subtitles."""
    duration = end_time - start_time
    num_chunks = math.ceil(duration / switch_interval)
    actual_interval = duration / num_chunks

    style_names = []
    for style in styles:
        style_names.append(style)

    for i in range(num_chunks):
        chunk_start = start_time + i * actual_interval
        chunk_end = chunk_start + actual_interval

        style = random.choice(style_names)

        ass_start = convert_to_ass_time(chunk_start)
        ass_end = convert_to_ass_time(min(chunk_end, end_time))

        line = f"Dialogue: 0,{ass_start},{ass_end},{style},,0,0,0,,{{\\fs500}}{word_text}"
        subtitles.append(line)

def get_video_resolution(video_path):
    """Use ffmpeg.probe to get video resolution (width, height)."""
    probe = ffmpeg.probe(video_path)
    
    # Find the video stream
    video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
    if not video_streams:
        raise RuntimeError(f"No video stream found in {video_path}")
    stream = video_streams[0]
    
    # Get resolution 
    width = int(stream['width'])
    height = int(stream['height'])
    return width, height

def burn_subtitles(input, output, subtitles):
    input = add_io_dir(input)
    output = add_io_dir(output)
    subtitles = add_io_dir(subtitles)
    
    ffmpeg.input(input).output(output, vf=f"ass={subtitles}:shaping=complex", acodec='copy').global_args('-y').run()

def combine_video_audio(video_input, audio_input, output):
    video = ffmpeg.input(add_io_dir(video_input))
    audio = ffmpeg.input(add_io_dir(audio_input))

    output = add_io_dir(output)

    ffmpeg.output(video.video, audio.audio, output, vcodec='copy', acodec='aac', shortest=None).global_args('-y').run()
    

# IMPLEMENTATION -------------------------
