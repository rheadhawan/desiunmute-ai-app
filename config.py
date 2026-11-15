import os
from openai import OpenAI

# Shared settings for all of DesiUnmute

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# AI models
# OpenAI is retiring all of these. When they do, only change the names here.
#   - gpt-4o-mini-tts:    shuts down Jan 6, 2027
#   - gpt-4o-mini:        shuts down Jan 14, 2027
#   - gpt-4o-transcribe:  shuts down Feb 26, 2027
TEXT_MODEL = "gpt-4o-mini"
VOICE_MODEL = "gpt-4o-mini-tts"
VOICE_NAME = "alloy"
TRANSCRIBE_MODEL = "gpt-4o-transcribe"

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
