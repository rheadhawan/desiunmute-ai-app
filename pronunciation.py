import json
import re
import jiwer
from config import client, TEXT_MODEL, NATURAL_HINDI_RULES, MAX_TEXT_LENGTH
from audio import transcribe_audio

# Romanized Hindi has no single correct spelling (kaise / kese / kayse),
# and people naturally shorten words when they talk (nahi -> nai).
# These count as the same word when scoring.
SAME_WORDS = {
    "nahin": "nahi",
    "nai": "nahi",
    "kese": "kaise",
    "kayse": "kaise",
    "kyun": "kyu",
    "ra": "raha",
    "ri": "rahi",
    "theek": "thik",
    "tik": "thik",
}


# Makes spelling differences not count as pronunciation mistakes

def simplify_spelling(text):
    text = text.lower()
    text = re.sub(r"[^a-z ]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    # 1. Swap in the standard version of common variant words
    words = [SAME_WORDS.get(word, word) for word in text.split(" ")]
    text = " ".join(words)

    # 2. Long vowels are spelled many ways (aa/a, ee/i, oo/u)
    text = text.replace("aa", "a").replace("ee", "i").replace("oo", "u")
    text = text.replace("w", "v")

    return text


# Turns the transcript (usually Devanagari) into romanized Hindi,
# using the learner's spelling for any word that is the same word.

def romanize_transcript(transcript, target_phrase):
    prompt = f"""
Convert this Hindi transcript into simple romanized Hindi, the way people text.

Target phrase the learner was practicing: "{target_phrase}"

Rules:
- Write exactly what the transcript says. Do NOT correct it toward the target.
- If a transcript word is the same word as one in the target phrase, copy the
  target's spelling for it.
- Keep any English words as they are.

Reply ONLY with JSON: {{"romanized": "..."}}
"""

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcript},
        ],
    )

    return json.loads(response.choices[0].message.content)["romanized"]


# Pronunciation feedback function

def pronunciation_feedback(user_audio, target_phrase):
    if user_audio is None:
        raise ValueError("Please record your pronunciation.")

    if not target_phrase or target_phrase.strip() == "":
        raise ValueError("Please enter the Hindi phrase you were trying to say.")

    if len(target_phrase) > MAX_TEXT_LENGTH:
        raise ValueError(f"Please keep the phrase under {MAX_TEXT_LENGTH} characters.")

    # 1. TRANSCRIBE AUDIO
    transcript = transcribe_audio(user_audio)

    # 2. ROMANIZE IT so we compare romanized with romanized
    heard = romanize_transcript(transcript, target_phrase)

    # 3. MEASURE DIFFERENCE (ignoring spelling differences)
    target_clean = simplify_spelling(target_phrase)
    heard_clean = simplify_spelling(heard)

    if target_clean == "":
        raise ValueError("Please type the phrase in romanized Hindi (for example: aap kaise ho).")

    if heard_clean == "":
        error_rate = 1.0
    else:
        error_rate = min(jiwer.wer(target_clean, heard_clean), 1.0)

    # 4. PICK A RESULT (internal score stays the same every time)
    if error_rate <= 0.15:
        result_level = "sounds natural"
    elif error_rate <= 0.4:
        result_level = "close"
    else:
        result_level = "keep practicing"

    # 5. AI COACHING (for every attempt, good ones too)
    feedback_prompt = f"""
You are a warm, encouraging Hindi pronunciation coach for Indian heritage learners.

Target phrase (intended): "{target_phrase}"
What the learner actually said (transcribed, romanized): "{heard}"
Overall result: {result_level}

IMPORTANT RULES:
- ONLY comment on REAL differences visible in the transcription. DO NOT invent issues.
- Ignore softness, breathiness, accent, or volume.
- Treat all dialects as valid Hindi. Natural shortening (nai for nahi) is fine.
- If the result is "sounds natural", give specific praise and at most one small refinement.
- Sound like a kind tutor, not a game. No scores, points, or grades.
- Write ALL feedback in simple English. The learner is still learning Hindi.
- Only use Hindi for the words being practiced, in romanized Hindi inside quotes (like 'namaste').
{NATURAL_HINDI_RULES}

Reply ONLY with JSON in this exact format:
{{
  "overall": "one short, honest, encouraging sentence",
  "went_well": ["something specific they got right", "..."],
  "tips": ["0-3 specific differences and how to fix them", "..."],
  "focus_sounds": ["sounds to practice, e.g. 'the soft t in taala'", "..."],
  "better_example": "the target phrase, romanized"
}}
"""

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": feedback_prompt}],
    )

    result = json.loads(response.choices[0].message.content)
    result["heard"] = heard
    result["result_level"] = result_level
    result["accuracy"] = round(1 - error_rate, 2)   # saved for progress tracking later, not shown
    return result


# Turns the feedback into nicely formatted text for the screen

def format_feedback(result):
    def bullet_list(items):
        return "\n".join(f"- {item}" for item in items) or "- (nothing to fix here)"

    headings = {
        "sounds natural": "Sounds natural",
        "close": "Close",
        "keep practicing": "Let's keep practicing",
    }

    return f"""## {headings[result["result_level"]]}

{result.get("overall", "")}

**We heard:** {result["heard"]}

### What went well
{bullet_list(result.get("went_well", []))}

### What to work on
{bullet_list(result.get("tips", []))}

### Sounds to focus on
{bullet_list(result.get("focus_sounds", []))}

**Say it like this:** {result.get("better_example", "")}
"""
