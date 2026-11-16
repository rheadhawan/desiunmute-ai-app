from config import client, VOICE_MODEL, VOICE_NAME, TRANSCRIBE_MODEL

# Text to speech function
# Always give this Hindi written in Devanagari, not romanized Hindi.
# Romanized text looks like English to the voice, so it reads it with an
# American accent (especially short phrases). Learners never see the Devanagari.

def make_audio(devanagari_text):
    audio = client.audio.speech.create(
        model=VOICE_MODEL,
        voice=VOICE_NAME,
        input=devanagari_text,
        instructions=(
            "Speak in natural, conversational Hindi with a native Indian accent, "
            "like a warm family member talking. Speak clearly at a relaxed pace "
            "so a learner can follow."
        ),
    )
    return audio.read()


# Speech to text function
# language="hi" tells the model to expect Hindi, so it doesn't translate it.
# It usually returns Devanagari, so callers romanize it afterwards.

def transcribe_audio(file_path):
    with open(file_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model=TRANSCRIBE_MODEL,
            file=f,
            language="hi",
        )
    return transcript.text
