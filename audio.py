import re
import math
import array
import base64
import lameenc
from config import client, VOICE_MODEL, VOICE_NAME, TRANSCRIBE_MODEL

# Text to speech
# Always give this Hindi written in Devanagari, not romanized Hindi.
# Romanized text looks like English to the voice, so it reads it with an
# American accent (especially short phrases). Learners never see the Devanagari.
#
# Since November 2026 this uses gpt-realtime-2.1-mini with the Marin voice,
# because gpt-4o-mini-tts shuts down on January 6, 2027. Rhea compared them
# with try_voices.py. The new model is a conversation model, so:
#   - we tell it to read our text word for word
#   - it can say a sentence a little differently each time, and sometimes
#     pauses in odd places, so we measure the pauses and re-record if needed

MAX_VOICE_TRIES = 3          # re-record up to 2 more times if a take sounds off
LONGEST_OK_PAUSE = 0.45      # seconds; natural comma pauses are ~0.4

READ_ALOUD_RULES = """
You are a text-to-speech voice for a Hindi learning app.
Read the user's text out loud EXACTLY as written, word for word.
Speak natural, everyday Hindi with a native Indian accent, like a warm family
member talking, at a calm and clear pace so a learner can follow.
Speak smoothly in one natural flow. Only pause briefly at commas and full stops.
Never pause in the middle of a phrase.
Do not translate, answer, explain, add or change anything. Only read it.
"""


# tries: how many takes it may record. Conversations use 1: each take is
# ~4 s, a pause between sentences is natural in a call, and 3 takes made
# Nani's replies take 11.5 s (Rhea's log, 2026-11-24). Lessons and Translate
# keep 3, because that audio is short, saved and replayed.

def make_audio(devanagari_text, tries=MAX_VOICE_TRIES):
    best_take = None
    best_pause = 99

    for attempt in range(1, tries + 1):
        pcm_bytes, spoken_words = read_aloud(devanagari_text)
        pause = longest_pause(pcm_bytes)
        same_words = only_letters(spoken_words) == only_letters(devanagari_text)

        # Shows up in Render's Logs, so you can see how often it re-records
        print(f"Voice take {attempt}: longest pause {pause:.2f}s, same words: {same_words}")

        # Never keep a take that changed the words (unless nothing better comes)
        if same_words and pause <= LONGEST_OK_PAUSE:
            return to_mp3(pcm_bytes)
        if same_words and pause < best_pause:
            best_take, best_pause = pcm_bytes, pause
        if best_take is None and attempt == tries:
            best_take = pcm_bytes

    return to_mp3(best_take)


# Asks the voice to read the text once. Returns (raw audio, the words it says it spoke).
# The audio comes back in small pieces until the answer is done.

def read_aloud(text):
    audio_bytes = b""
    spoken_words = ""

    with client.realtime.connect(model=VOICE_MODEL) as connection:
        connection.session.update(session={
            "type": "realtime",
            "instructions": READ_ALOUD_RULES,
            "output_modalities": ["audio"],
            "audio": {"output": {"voice": VOICE_NAME, "format": {"type": "audio/pcm", "rate": 24000}}},
        })
        connection.conversation.item.create(item={
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": text}],
        })
        connection.response.create()

        for event in connection:
            if event.type == "response.output_audio.delta":
                audio_bytes += base64.b64decode(event.delta)
            elif event.type == "response.output_audio_transcript.delta":
                spoken_words += event.delta
            elif event.type == "error":
                raise RuntimeError(f"Voice error: {event.error.message}")
            elif event.type == "response.done":
                break

    if audio_bytes == b"":
        raise RuntimeError("The voice didn't send any audio.")

    return audio_bytes, spoken_words


# Finds the longest silence in the middle of the audio (not at the start or end).
# The audio is 16-bit, 24,000 samples a second. We look at it in 20 ms pieces.

def longest_pause(pcm_bytes):
    samples = array.array("h", pcm_bytes)
    piece = 480                          # 20 ms
    loud = []
    for start in range(0, len(samples) - piece, piece):
        chunk = samples[start:start + piece]
        rms = math.sqrt(sum(s * s for s in chunk) / piece) / 32768
        loud.append(rms > 0.01)          # about -40 dB, quieter than speech

    if True not in loud:
        return 0.0

    first = loud.index(True)
    last = len(loud) - 1 - loud[::-1].index(True)

    longest = 0
    quiet_run = 0
    for is_loud in loud[first:last + 1]:
        quiet_run = 0 if is_loud else quiet_run + 1
        longest = max(longest, quiet_run)
    return longest * 0.02


# Keeps only the Hindi letters, so "नमस्ते जी।" and "नमस्ते जी" count as the same words
def only_letters(text):
    return re.sub(r"[^ऀ-ॣ०-ॿ]", "", text)


# The voice sends raw audio, about 5 times bigger than an MP3.
# lameenc turns it into a small MP3 so pages stay quick on phones.
def to_mp3(pcm_bytes):
    encoder = lameenc.Encoder()
    encoder.set_bit_rate(64)
    encoder.set_in_sample_rate(24000)
    encoder.set_channels(1)
    encoder.set_quality(2)               # 2 = high quality
    return encoder.encode(pcm_bytes) + encoder.flush()


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
