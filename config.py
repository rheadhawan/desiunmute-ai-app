import os
from openai import OpenAI

# Shared settings for all of DesiUnmute

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# AI models
# OpenAI is retiring all of these. When they do, only change the names here.
#   - gpt-4o-mini-tts:    shuts down Jan 6, 2027
#   - gpt-4o-mini:        shuts down Jan 14, 2027
#   - gpt-4o-transcribe:  shuts down Feb 26, 2027
# gpt-6-luna replaced gpt-4o-mini (retiring Jan 14, 2027) on 2026-11-16.
# Rhea compared gpt-4o-mini, gpt-6-luna and gpt-6.1-terra with try_models.py:
# Luna and Terra both got Hindi gender and respect forms right, and Luna
# costs about a tenth of Terra.
TEXT_MODEL = "gpt-6-luna"

# How much Luna "thinks" before answering (none, low, medium, high...).
# The default is medium. Conversation replies use low, because a short chat
# reply doesn't need much thinking and waiting for Nani felt slow (2026-11-24).
# If gender/respect mistakes come back in conversations, set this to "medium".
CONVERSATION_REASONING = "low"
# gpt-4o-mini-tts shuts down Jan 6, 2027. Rhea compared voices with try_voices.py
# on 2026-11-17 and picked Marin from gpt-realtime-2.1-mini (see audio.py).
VOICE_MODEL = "gpt-realtime-2.1-mini"
VOICE_NAME = "marin"
# Listening (speech to text). gpt-4o-transcribe shuts down Feb 26, 2027;
# OpenAI's replacement for recorded files is gpt-transcribe (switched 2026-11-24).
# To go back while it's still running, set this to "gpt-4o-transcribe".
TRANSCRIBE_MODEL = "gpt-transcribe"

# Limits (to protect the OpenAI budget)
MAX_TEXT_LENGTH = 300           # characters a learner can type
MAX_CONVERSATION_TURNS = 20     # replies per conversation before starting over

# Natural Hindi rules
# Every prompt that writes Hindi uses these, so the whole app sounds the same.
NATURAL_HINDI_RULES = """
- Use natural, conversational Hindi exactly how families speak it at home.
- Never use textbook or shuddh Hindi (for example: avoid "kripya", and avoid
  "dhanyavaad" in casual speech).
- Everyday English words that Hindi speakers use (phone, office, traffic,
  tension) are normal Hindi. Keep them.
- Everyday Urdu-origin words (shukriya, zaroor, mushkil, dost) are normal Hindi.
- Use natural fillers when they fit (accha, haan, yaar, arre, matlab).
- Write Hindi in simple romanized spelling, the way people text
  (aap kaise ho, main theek hoon). Never show Devanagari unless asked.
"""

# Respect levels in Hindi depend on who you are talking to
TALKING_TO = {
    "A friend": "Use 'tum' and casual verb forms, like talking to a friend or cousin your age.",
    "An elder": "Use 'aap', respectful plural verbs, and 'ji' where natural, like talking to a parent, grandparent, aunt or uncle.",
    "A child": "Use 'tum' with a warm, simple tone, like talking to a younger child in the family.",
}

# Whether the learner is a woman or a man, for Conversation Practice.
# Hindi changes for them: Nani says "thak gayi hogi" to a granddaughter and
# "thak gaye hoge" to a grandson. Without it, Luna guessed "gaye" for
# everyone (Rhea's test, 2026-11-24).
LEARNER = {
    "A woman": "The learner is a woman. Whenever words change for her, use feminine forms (thak gayi hogi, kaisi ho, aa gayi, main kar rahi hoon).",
    "A man": "The learner is a man. Whenever words change for him, use masculine forms (thak gaye hoge, kaise ho, aa gaye, main kar raha hoon).",
    "": "We don't know if the learner is a woman or a man. Avoid words that change for them: say \"thakaan ho gayi hogi\" instead of \"thak gaye/gayi hoge\", and \"sab theek?\" instead of \"kaise/kaisi ho?\".",
}


# Whether the person you're talking to is a woman or a man.
# Hindi changes words for them too: "aap kaisi hain?" to Nani, "aap kaise hain?" to Nana.
LISTENER = {
    "A woman": "The person being spoken to is a woman. Use feminine forms for her (aap kaisi hain, tum kaisi ho, aap kahan gayi thin).",
    "A man": "The person being spoken to is a man. Use masculine forms for him (aap kaise hain, tum kaise ho, aap kahan gaye the).",
    "Not sure": "We don't know if the person being spoken to is a woman or a man. If the sentence changes for them (like kaise/kaisi), use the masculine form in \"translation\" and put the feminine form first in \"alternatives\", marked \"(to a woman)\".",
}
