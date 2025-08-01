import whisper
import json
import string
# from client import client

# FUNCTIONS -------------------------
"""
def check_importance(words):
    # Build a list of (word, duration) tuples
    word_infos = [
        {
            "word": w["word"],
            "duration": round(w["end"] - w["start"], 2)
        }
        for w in words
    ]

    # Prompt template
    prompt = (
        "You are given a list of words (including their duration) which correspond to a song's lyrics to be used in a motivational gym edit"
        "You are to mark each word as important (`true`) or not (`false`) based on the combination of the following two factors:\n"
        "- If it has meaningful content, especially with regards to the lyrics (e.g. it is not a filler and ends off a clause/phrase or is related to deeper concepts—e.g. death)."
        "- If the word is spoken for a long duration, i.e. emphasized (compared to the rest of the provided words)\n\n"
        "Return a JSON list of booleans matching the order of the input.\n"
        "    - For example, based on the previous two factors something like \"I will never give up\" where \"never\" is said longer would have \"never\" highlighted."
        f"Words with durations: {json.dumps(word_infos)}"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI API returned no content")

    importance_list = json.loads(content)

    if len(importance_list) != len(words):
        raise ValueError("Mismatched response length")

    for word, important in zip(words, importance_list):
        word["important"] = important

    return words
"""

def split_segments(result, max_gap=0.2):
    """
    Splits whisper segments into smaller segments based on gaps between individual words greater than max_gap.
    Returns a new list of segments with id, start, end, text, and words.
    """
    new_segments = []
    remove_punct = str.maketrans("", "", string.punctuation)
    
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
            curr_word["word"] = curr_word["word"].translate(remove_punct)
            gap = curr_word["start"] - prev_word["end"]

            if gap > max_gap:
                # If gap big enough, close off current subsegment
                text = "".join(w["word"] for w in current_words).strip() # Get just words for the text
                text = text.translate(remove_punct)
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
            text = text.translate(remove_punct)
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