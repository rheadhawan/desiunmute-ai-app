import json
import re
import jiwer
from config import client, TEXT_MODEL, NATURAL_HINDI_RULES, MAX_TEXT_LENGTH
from audio import transcribe_audio
from azure_speech import check_pronunciation, NATURAL_ACCURACY
from lessons import all_lesson_phrases

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
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcript},
        ],
    )

    return json.loads(response.choices[0].message.content)["romanized"]


# What the coach is told about the accent

# Without Azure we only know which WORDS came through (OpenAI's listening
# models can't tell a native accent from an American one, tested 2026-11-17)
WORDS_ONLY_RULES = """
- You only see the WORDS that were heard, not how they sounded. Never say their
  accent or pronunciation sounded native, natural or correct, and never give
  accent tips you can't know. Praise getting the words right instead.
- Ignore softness, breathiness, accent, or volume.
- If the result is "sounds natural", every word came through: praise that, and don't invent refinements.
- focus_sounds: only sounds in words that came out differently, else leave it empty.
"""


def accent_rules(accent):
    if accent["accuracy"] >= NATURAL_ACCURACY:
        how_it_sounded = "natural, like a Hindi speaker"
    else:
        how_it_sounded = "less natural, probably an English accent"

    weak_words = ", ".join(accent["weak_words"]) or "none in particular"

    return f"""
A speech checker listened to the SOUNDS (you can't hear the recording yourself):
- Overall it sounded: {how_it_sounded}
- Words that sounded least natural (in Devanagari): {weak_words}

- Only repeat what the checker found. Never invent problems or praise.
- If it sounded natural, say so warmly and don't invent refinements.
- If it sounded less natural, name the words to listen to again (in romanized
  Hindi, never Devanagari) and give 1-2 gentle tips that commonly help English
  speakers with those words (for example: soft "t" and "d" with the tongue
  touching the teeth, short clear vowels, no English "r" sound). Say "try",
  because you can't know exactly which sound was off.
- Never mention numbers or scores.
- focus_sounds: only sounds in those words, else leave it empty.
"""


# Pronunciation feedback function
# reference is the phrase in Devanagari. When it's given, Azure listens to
# the accent too. Without it, OpenAI checks the words only.

def pronunciation_feedback(user_audio, target_phrase, reference=None):
    if user_audio is None:
        raise ValueError("Please record your pronunciation.")

    if not target_phrase or target_phrase.strip() == "":
        raise ValueError("Please enter the Hindi phrase you were trying to say.")

    if len(target_phrase) > MAX_TEXT_LENGTH:
        raise ValueError(f"Please keep the phrase under {MAX_TEXT_LENGTH} characters.")

    # 1. LISTEN (Azure also checks the accent)
    accent = None
    if reference:
        accent = check_pronunciation(user_audio, reference)
        transcript = accent["heard"]
    else:
        transcript = transcribe_audio(user_audio)

    # 2. ROMANIZE IT so we compare romanized with romanized
    if transcript.strip() == "":
        heard = ""   # nothing was heard, so nothing to romanize
    else:
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
    if error_rate <= 0.15 and accent and accent["accuracy"] < NATURAL_ACCURACY:
        result_level = "polish the sounds"   # right words, English-sounding accent
    elif error_rate <= 0.15:
        result_level = "sounds natural"
    elif error_rate <= 0.4:
        result_level = "close"
    else:
        result_level = "keep practicing"

    # 5. AI COACHING (for every attempt, good ones too)
    if accent is None:
        sound_rules = WORDS_ONLY_RULES
    else:
        sound_rules = accent_rules(accent)

    feedback_prompt = f"""
You are a warm, encouraging Hindi pronunciation coach for Indian heritage learners.

Target phrase (intended): "{target_phrase}"
What the learner actually said (transcribed, romanized): "{heard}"
Overall result: {result_level}

IMPORTANT RULES:
- ONLY comment on REAL differences visible in the transcription. DO NOT invent issues.
- If words came out differently, start with those.
- Treat all dialects as valid Hindi. Natural shortening (nai for nahi) is fine.
{sound_rules}
- Sound like a kind tutor, not a game. No scores, points, or grades.
- Write ALL feedback in simple English. The learner is still learning Hindi.
- Only use Hindi for the words being practiced, in romanized Hindi inside quotes (like 'namaste').
{NATURAL_HINDI_RULES}

Reply ONLY with JSON in this exact format:
{{
  "overall": "one short, honest, encouraging sentence",
  "went_well": ["something specific they got right", "..."],
  "tips": ["0-3 specific differences and how to fix them", "..."],
  "focus_sounds": ["see the focus_sounds rule above"],
  "better_example": "the target phrase, romanized"
}}
"""

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": feedback_prompt}],
    )

    result = json.loads(response.choices[0].message.content)
    result["heard"] = heard
    result["result_level"] = result_level
    result["accent_checked"] = accent is not None
    result["accuracy"] = round(1 - error_rate, 2)   # saved for progress tracking later, not shown
    return result


# The heading at the top of the feedback (shared by the website and Gradio)

def feedback_heading(result):
    if result["result_level"] == "sounds natural" and result.get("accent_checked"):
        return "Every word came through, and it sounds natural"

    headings = {
        "sounds natural": "Every word came through",
        "polish the sounds": "Every word came through. Now let's polish the sounds",
        "close": "Almost! A word or two was different",
        "keep practicing": "Let's try that again",
    }
    return headings[result["result_level"]]


# Turns the feedback into nicely formatted text for the screen

def format_feedback(result):
    def bullet_list(items):
        return "\n".join(f"- {item}" for item in items) or "- (nothing to fix here)"

    return f"""## {feedback_heading(result)}

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


# Ready-made phrases to practice
# The Devanagari is only for the voice. Drafts until a native speaker reviews them.

PRACTICE_PHRASES = [
    {"phrase": "namaste ji", "english": "Hello (respectful)", "devanagari": "नमस्ते जी"},
    {"phrase": "aap kaise hain?", "english": "How are you? (to an older man)", "devanagari": "आप कैसे हैं?"},
    {"phrase": "aap kaisi hain?", "english": "How are you? (to an older woman)", "devanagari": "आप कैसी हैं?"},
    {"phrase": "main theek hoon", "english": "I'm fine", "devanagari": "मैं ठीक हूँ"},
    {"phrase": "khana kha liya?", "english": "Have you eaten?", "devanagari": "खाना खा लिया?"},
    {"phrase": "mujhe aapki yaad aati hai", "english": "I miss you", "devanagari": "मुझे आपकी याद आती है"},
    {"phrase": "thoda dheere boliye", "english": "Please speak a little slower", "devanagari": "थोड़ा धीरे बोलिए"},
    {"phrase": "mujhe samajh aata hai, par bolna mushkil hai", "english": "I understand, but speaking is hard", "devanagari": "मुझे समझ आता है, पर बोलना मुश्किल है"},
    {"phrase": "accha, phir baat karte hain", "english": "Okay, let's talk later", "devanagari": "अच्छा, फिर बात करते हैं"},
]


# Finds the saved Devanagari for a ready-made or lesson phrase (or None)

def saved_devanagari(phrase):
    for item in PRACTICE_PHRASES + all_lesson_phrases():
        if item["phrase"] == phrase.strip():
            return item["devanagari"]
    return None


# Turns a romanized phrase into Devanagari so the voice can say it
# with a Hindi accent (learners never see the Devanagari)

def phrase_to_devanagari(phrase):
    if not phrase or phrase.strip() == "":
        raise ValueError("Type or pick a phrase first.")

    if len(phrase) > MAX_TEXT_LENGTH:
        raise ValueError(f"Please keep the phrase under {MAX_TEXT_LENGTH} characters.")

    # Ready-made and lesson phrases already have it, so no AI call needed
    saved = saved_devanagari(phrase)
    if saved:
        return saved

    prompt = """
Write this romanized Hindi phrase in Devanagari. Keep the exact same words.
Do not translate, correct or change anything.

Reply ONLY with JSON: {"devanagari": "..."}
"""

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": phrase},
        ],
    )

    return json.loads(response.choices[0].message.content)["devanagari"]
