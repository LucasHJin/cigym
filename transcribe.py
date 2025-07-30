import whisper
import json

# FUNCTIONS -------------------------
def split_segments(result, max_gap=0.2):
    """
    Splits whisper segments into smaller segments based on gaps between individual words greater than max_gap.
    Returns a new list of segments with id, start, end, text, and words.
    """
    new_segments = []
    
    # Go through each segment
    for segment in result["segments"]:
        words = segment.get("words", [])
        # If no word-level data, keep segment as is
        if not words:
            new_segments.append(segment)
            continue

        current_words = [words[0]]
        current_start = words[0]["start"]
        current_end = words[0]["end"]

        # Go through each word and eheck gap
        for i in range(1, len(words)):
            prev_word = words[i-1]
            curr_word = words[i]
            gap = curr_word["start"] - prev_word["end"]

            if gap > max_gap:
                # If gap big enough, close off current subsegment
                text = "".join(w["word"] for w in current_words).strip() # Get just words for the text
                new_segments.append({
                    "id": len(new_segments),
                    "start": current_start,
                    "end": current_end,
                    "text": text,
                    "words": current_words
                })
                # Start new subsegment
                current_words = [curr_word]
                current_start = curr_word["start"]
                current_end = curr_word["end"]
            else:
                current_words.append(curr_word)
                current_end = curr_word["end"]

        # Append final subsegment (hasn't been added because no gap to be checked)
        if current_words:
            text = "".join(w["word"] for w in current_words).strip()
            new_segments.append({
                "id": len(new_segments),
                "start": current_start,
                "end": current_end,
                "text": text,
                "words": current_words
            })

    return new_segments

# IMPLEMENTATION -------------------------
model = whisper.load_model('small') # Use medium/large in actual thing
result = model.transcribe('sample.MP4', language='en', word_timestamps=True)

result["segments"] = split_segments(result, max_gap=0.2)

with open("transcript.json", "w") as f: # json over srt because more precision
    json.dump(result, f, indent=2)
    