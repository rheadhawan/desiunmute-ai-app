import json
import re
import jiwer
from config import client, TEXT_MODEL, NATURAL_HINDI_RULES, MAX_TEXT_LENGTH
from audio import transcribe_audio
from azure_speech import check_pronunciation, NATURAL_ACCURACY, WEAK_SOUND_ACCURACY, PART_GAP
from sounds import SOUND_GUIDE, ROMAN, split_sounds, word_parts, romanize_part
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


# Matches each Devanagari word to the learner's romanized word
# (नमस्ते -> namaste), so tips use the learner's own spelling.

def romanized_words(reference, target_phrase):
    hindi = re.findall(r"[\u0900-\u0963\u0966-\u097F]+", reference)
    roman = re.findall(r"[A-Za-z]+", target_phrase)
    if len(hindi) != len(roman):
        return {}
    return dict(zip(hindi, roman))


# Finds the part of a word that clearly sounded the least natural, using
# Azure's score for each sound. Returns the part's sound numbers, or None
# when the scores don't line up or no part clearly stands out (then we
# don't guess).

def weakest_part(sounds, parts, scores):
    if not scores or len(scores) != len(sounds) or len(parts) < 2:
        return None

    averages = sorted((sum(scores[n] for n in part) / len(part), number) for number, part in enumerate(parts))
    lowest, next_lowest = averages[0][0], averages[1][0]

    if lowest < WEAK_SOUND_ACCURACY and next_lowest - lowest >= PART_GAP:
        return parts[averages[0][1]]
    return None


# Pronunciation tips built ONLY from what Azure measured.
# The tips come from here, not from Luna, so they can't be guessed.
# Returns (tips, focus_sounds, what_stood_out) where what_stood_out is a
# short note for Luna's summary sentence.

def sound_tips(accent, reference, target_phrase):
    if accent["accuracy"] >= NATURAL_ACCURACY:
        return [], [], "nothing, it sounded natural"

    names = romanized_words(reference, target_phrase)

    # 1. Work out what Azure's scores show for each weak word
    findings = []
    for word in accent["words"]:
        if not word["weak"]:
            continue
        sounds = split_sounds(word["word"])
        parts = word_parts(sounds)
        name = names.get(word["word"]) or "".join(romanize_part(sounds, p) for p in parts)
        part = weakest_part(sounds, parts, word["sounds"])

        if part:
            part_scores = [word["sounds"][n] for n in part]
            findings.append({
                "name": name, "sounds": sounds, "scores": word["sounds"], "part": part,
                "severity": sum(part_scores) / len(part_scores),
            })
        else:
            findings.append({"name": name, "part": None, "severity": word["accuracy"]})

    # 2. The biggest problem first, and at most two at a time
    findings.sort(key=lambda finding: finding["severity"])
    tips = []
    focus = []
    practice = []

    for finding in findings[:2]:
        name = finding["name"]

        if finding["part"]:
            sounds, part = finding["sounds"], finding["part"]
            part_text = romanize_part(sounds, part)
            where = f'the "{part_text}" in \'{name}\''

            # Explain the lowest sound in that part, if the guide has something useful
            lowest = min(part, key=lambda n: finding["scores"][n])
            letter = sounds[lowest]["letter"]
            if letter in SOUND_GUIDE:
                tips.append(f'Focus on {where}. The "{ROMAN[letter]}" there is {SOUND_GUIDE[letter]}')
            else:
                tips.append(f"Focus on {where}. Listen to how the Hindi audio says it and copy it.")
            focus.append(where)
            practice.append(f'"{part_text}"')
        else:
            # Azure only told us the word, so that's all we say
            tips.append(f"'{name}' sounded the least natural. Listen to how the Hindi audio says it and copy it.")
            focus.append(f"'{name}'")
            practice.append(f"'{name}'")

    if practice:
        on_own = "on its own" if len(practice) == 1 else "on their own"
        tips.append(f"Play the Slow audio, say {' and '.join(practice)} {on_own} a few times, then the whole phrase.")
    else:
        # Sounded less natural overall, but no single word stood out
        tips.append("Play the Slow audio and copy it closely, sound by sound, then say the whole phrase again.")

    what_stood_out = ", ".join(focus) or "no single word or sound, just the overall sound"
    return tips, focus, what_stood_out


# not_heard lists the words Azure couldn't find (empty when it found them all)

def accent_rules(accent, what_stood_out, not_heard):
    if not_heard:
        which = ", ".join(f"'{word}'" for word in not_heard)
        return f"""
A speech checker listened to the SOUNDS (you can't hear the recording yourself):
- It couldn't clearly hear: {which}, even if the words above look complete.
- Your "overall" sentence should gently say that. Say "we couldn't clearly hear",
  never "you didn't say": the word may have been said very differently.
- Do NOT write any tips about sounds or accent. Leave tips and focus_sounds empty.
- Never mention numbers or scores.
"""

    if accent["accuracy"] >= NATURAL_ACCURACY:
        how_it_sounded = "natural, like a Hindi speaker"
    else:
        how_it_sounded = "a little less natural than a native speaker"

    return f"""
A speech checker listened to the SOUNDS (you can't hear the recording yourself):
- Overall it sounded: {how_it_sounded}
- What stood out: {what_stood_out}

- The app adds the pronunciation tips itself. Do NOT write any tips about
  sounds, accent, vowels, the tongue or the mouth. Leave focus_sounds empty.
- Your "overall" sentence may mention what stood out, in those exact words.
  Never mention any other sound or word as a problem.
- If it sounded natural, say so warmly and don't invent refinements.
- An accent isn't a mistake: say "less natural" or "more like a native speaker", never "wrong".
- If it sounded less natural, don't say "every word came through": the checker
  sometimes fills in a word it expected, so we can't be sure.
- Never mention numbers or scores.
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
        # Azure ends sentences with "।", which can come back as a stray period
        heard = romanize_transcript(transcript, target_phrase).strip().rstrip(".।")

    # 3. MEASURE DIFFERENCE (ignoring spelling differences)
    target_clean = simplify_spelling(target_phrase)
    heard_clean = simplify_spelling(heard)

    if target_clean == "":
        raise ValueError("Please type the phrase in romanized Hindi (for example: aap kaise ho).")

    # Nothing was recognized: too quiet, cut off, or so different from Hindi
    # that no word came through. We can't tell which, so we don't guess
    # (and there's nothing for Luna to comment on).
    if heard_clean == "":
        return {
            "overall": "We couldn't make out any words this time.",
            "went_well": [],
            "tips": [
                "Stay close to your microphone and speak at a normal volume.",
                "Play the Hindi audio first, then copy how it sounds as closely as you can.",
            ],
            "focus_sounds": [],
            "better_example": target_phrase,
            "heard": "",
            "result_level": "nothing heard",
            "accent_checked": accent is not None,
            "accuracy": 0.0,
        }

    error_rate = min(jiwer.wer(target_clean, heard_clean), 1.0)

    # Words Azure couldn't find (skipped, or said too differently to recognize)
    not_heard = []
    if accent is not None:
        names = romanized_words(reference, target_phrase)
        not_heard = [names.get(word, word) for word in accent["missing"]]
    part_missing = bool(not_heard)

    # 4. PICK A RESULT (internal score stays the same every time)
    if error_rate <= 0.15 and part_missing:
        result_level = "close"
    elif error_rate <= 0.15 and accent and accent["accuracy"] < NATURAL_ACCURACY:
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
        accent_tips, accent_focus, what_stood_out = sound_tips(accent, reference, target_phrase)
        sound_rules = accent_rules(accent, what_stood_out, not_heard)

    feedback_prompt = f"""
You are a warm, encouraging Hindi pronunciation coach for Indian heritage learners.

Target phrase (intended): "{target_phrase}"
What the learner actually said (transcribed, romanized): "{heard}"
Overall result: {result_level}

IMPORTANT RULES:
- ONLY comment on REAL differences visible in the transcription. DO NOT invent issues.
- If words came out differently, start with those.
- tips: only about words that came out differently, else leave it empty.
- If every word came through and the result is "sounds natural", went_well must say so.
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
  "tips": ["see the tips rule above", "..."],
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

    # With Azure, sound tips come from its measurements, never from Luna.
    # If words came out differently, those come first, so no sound tips yet.
    if accent is not None:
        if part_missing and error_rate <= 0.15:
            result["tips"] = [
                f"We couldn't clearly hear '{word}'. Make sure you say it, and copy how the Hindi audio says it."
                for word in not_heard[:2]
            ]
            result["tips"].append("Play the Hindi audio, then try the whole phrase again.")
            result["focus_sounds"] = [f"'{word}'" for word in not_heard[:2]]
        elif error_rate <= 0.15:
            result["tips"] = accent_tips
            result["focus_sounds"] = accent_focus
        else:
            result["focus_sounds"] = []
    result["accuracy"] = round(1 - error_rate, 2)   # saved for progress tracking later, not shown
    return result


# The heading at the top of the feedback (shared by the website and Gradio)

def feedback_heading(result):
    if result["result_level"] == "sounds natural" and result.get("accent_checked"):
        return "Every word came through, and it sounds natural"

    headings = {
        "sounds natural": "Every word came through",
        # Not "every word came through": Azure sometimes fills in a word it expected
        "polish the sounds": "Now let's polish the sounds",
        "close": "Almost! A word or two was different",
        "keep practicing": "Let's try that again",
        "nothing heard": "We couldn't hear that clearly",
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
