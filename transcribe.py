import whisper
import json
import string
from client import client

# FUNCTIONS -------------------------
# Note -> can't just tell it to return JSON with added importance because it hallucinates words
def assign_importance(transcript):
    """Send transcript JSON to Gemini API and get importance scoring per word as a patch."""
    
    with open(transcript, "r", encoding="utf-8") as f:
        input_json = json.load(f)
    
    prompt = f"""
You are given a transcription JSON of a song or spoken phrase.
Your task:
1. For each word, assign an "importance" score (considering both the factors listed below in part 2 and the fact that these are lyrics appearing on screen so there shouldn't be too many marked as important):
   - 0 = normal word, not worth highlighting (the majority of words should be 0).
   - 1 = slightly important word - this will highlight the text a different color.
   - 2 = very important word - this will make the text rapidly change fonts (keep it scarce, around 0-2 per segment).
2. Importance is based on:
   - The word's emotional or semantic weight.
   - Its role in emphasis.
   - The length of time spoken (less important).
3. DO NOT change, remove, or reorder any existing text, numbers, or structure.
4. OUTPUT ONLY a JSON array of objects with:
   - "segment_id": the segment's id
   - "word_index": the index of the word within the segment's "words" list
   - "importance": the assigned importance score (0, 1, or 2)
5. DO NOT output any explanations, markdown, or extra text.

Input JSON:
{json.dumps(input_json, indent=2)}
"""
    # Query the API
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    
    # Get output
    output_text = ""
    if response.candidates and response.candidates[0].content:
        parts = getattr(response.candidates[0].content, "parts", [])
        for part in parts:
            if hasattr(part, "text") and part.text:
                output_text += part.text.strip() + "\n"
    if not output_text.strip():
        raise ValueError("Gemini response contained no text output.")

    # Remove markdown ticks if there are any
    if output_text.strip().startswith("```"):
        output_text = "\n".join(
            line for line in output_text.splitlines()
            if not line.strip().startswith("```")
        )

    # Parse the output to json
    try:
        patch = json.loads(output_text)
    except json.JSONDecodeError as e:
        print("=== Gemini raw output ===")
        print(output_text)
        print("=========================")
        raise ValueError("Failed to parse Gemini's response into JSON") from e

    # Add importance to each word in the original json
    for entry in patch:
        segment_id = entry["segment_id"]
        word_index = entry["word_index"]
        importance = entry["importance"]
        input_json["segments"][segment_id]["words"][word_index]["importance"] = importance

    # Save updated JSON
    with open("transcript_processed.json", "w", encoding="utf-8") as f:
        json.dump(input_json, f, indent=2, ensure_ascii=False)

    print("Finished marking importance")

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

        words[0]["word"] = words[0]["word"].translate(remove_punct).strip().upper()
        current_words = [words[0]]
        current_start = words[0]["start"]
        current_end = words[0]["end"]

        # Go through each word and eheck gap
        for i in range(1, len(words)):
            prev_word = words[i-1]
            curr_word = words[i]
            curr_word["word"] = curr_word["word"].translate(remove_punct).strip().upper()
            gap = curr_word["start"] - prev_word["end"]

            if gap > max_gap:
                # If gap big enough, close off current subsegment
                text = " ".join(w["word"].upper() for w in current_words).strip() # Get just words for the text
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

def transcribe_audio(file_path):
    model = whisper.load_model('large')
    result = model.transcribe(file_path, language='en', word_timestamps=True)
    result["segments"] = split_segments(result, max_gap=0.2)
    with open("transcript.json", "w") as f: # json over srt because more precision
        json.dump(result, f, indent=2)

# IMPLEMENTATION -------------------------
#transcribe_audio('audio.MP4')
assign_importance("transcript.json")