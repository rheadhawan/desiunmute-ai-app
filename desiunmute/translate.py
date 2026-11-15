import json
from config import client, TEXT_MODEL, NATURAL_HINDI_RULES, TALKING_TO, MAX_TEXT_LENGTH
from audio import make_audio

# Translator function
# Returns a dictionary so the app can show each part separately
# and send only the Devanagari line to the voice.

def desiunmute_translate(text, gender="Female", talking_to="A friend", pronunciation="Yes"):
    if not text or text.strip() == "":
        raise ValueError("Please type an English sentence.")

    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Please keep it under {MAX_TEXT_LENGTH} characters.")

    prompt = f"""
You are a Hindi language tutor for Indian heritage learners who understand some
Hindi but cannot read Devanagari. Translate the learner's English sentence into
natural, conversational Hindi.

Rules:
{NATURAL_HINDI_RULES}
- The learner is {gender.lower()}. Use the correct verb endings for a {gender.lower()} speaker.
- {TALKING_TO[talking_to]}

Reply ONLY with JSON in this exact format:
{{
  "translation": "the Hindi translation in romanized Hindi",
  "devanagari": "the same translation in Devanagari (used only for audio)",
  "breakdown": ["word or phrase = meaning", "..."],
  "pronunciation_tips": ["tip about a tricky sound, written for English speakers", "..."],
  "alternatives": ["another natural way to say it, with when to use it", "..."],
  "common_mistakes": ["a mistake learners often make with this sentence, and the fix", "..."]
}}
"""

    # Query OpenAI
    response = client.chat.completions.create(
        model=TEXT_MODEL,
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
    )

    result = json.loads(response.choices[0].message.content)

    # Create audio from the Devanagari line (only if the learner wants it)
    result["audio"] = None
    if pronunciation == "Yes" and result.get("devanagari"):
        result["audio"] = make_audio(result["devanagari"])

    return result


# Turns the translation into nicely formatted text for the screen

def format_translation(result):
    def bullet_list(items):
        return "\n".join(f"- {item}" for item in items) or "- (none)"

    return f"""## {result["translation"]}

### Breakdown
{bullet_list(result.get("breakdown", []))}

### Pronunciation tips
{bullet_list(result.get("pronunciation_tips", []))}

### Other ways to say it
{bullet_list(result.get("alternatives", []))}

### Common mistakes
{bullet_list(result.get("common_mistakes", []))}
"""
