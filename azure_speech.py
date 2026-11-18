import os
import json
import base64
import urllib.request
import urllib.error

# Microsoft Azure Pronunciation Assessment
# Checks HOW Hindi the learner sounds, not just which words came through.
#
# Why Azure: on 2026-11-17 Rhea recorded "namaste ji" twice in her natural
# accent and twice in an American accent. Azure's accuracy score told them
# apart both times (natural 90 and 93, American 74 and 76). OpenAI's
# listening models gave both versions the same marks.
#
# Settings (Render → Environment, never in the code):
#   AZURE_SPEECH_KEY     KEY 1 from Azure portal → your resource → Keys and Endpoint
#   AZURE_SPEECH_REGION  the Location/Region on that same page (Rhea's is westus3)
# Without a key, the coach goes back to checking words only (fine for local testing).

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "westus3")

# Accuracy at or above this sounds natural. From Rhea's tests: natural 90-93,
# American accent 74-76. Adjust once testers have tried it.
NATURAL_ACCURACY = 85

# A single word below this is worth listening to again
WEAK_WORD_ACCURACY = 80

# A part of a word ("na") is only pointed out when it's below this AND clearly
# lower than the word's other parts. In Rhea's American "ney-meh-ste" in
# Speech Studio, the parts scored na 9, mas 38, te 57: "na" clearly stood out.
# In another recording Azure lost track (85 0 0 0 0 0 0): nothing stood out,
# so the coach only names the word.
WEAK_SOUND_ACCURACY = 60
PART_GAP = 20

# Completeness is logged but NOT used: it also drops when a word is said
# badly (Rhea's American "aap kaisi hain", every word said: completeness 67),
# so it can't tell a missing word from an accent. Words Azure flags as
# missing ("Omission") are used instead.


def azure_is_set_up():
    return bool(AZURE_SPEECH_KEY)


# Sends a recording to Azure and returns what it heard and how Hindi it sounded.
# wav_path must be WAV, 16 kHz, mono (the browser converts recordings to this).
# reference must be in Devanagari, so Azure knows which Hindi sounds to expect.

def check_pronunciation(wav_path, reference):
    settings = {
        "ReferenceText": reference,
        "GradingSystem": "HundredMark",
        "Granularity": "Phoneme",   # scores every sound, not just every word
        "Dimension": "Comprehensive",
        "EnableMiscue": True,   # notices missing or extra words
    }

    url = (
        f"https://{AZURE_SPEECH_REGION}.stt.speech.microsoft.com"
        "/speech/recognition/conversation/cognitiveservices/v1?language=hi-IN&format=detailed"
    )
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
        "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
        "Accept": "application/json",
        "Pronunciation-Assessment": base64.b64encode(json.dumps(settings).encode()).decode(),
    }

    with open(wav_path, "rb") as f:
        request = urllib.request.Request(url, data=f.read(), headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            answer = json.loads(response.read())
    except urllib.error.HTTPError as error:
        # 401 almost always means the key or region is wrong
        raise RuntimeError(f"Azure said {error.code}: {error.read()[:300]!r}")

    result = read_azure_answer(answer)

    # Shows up in Terminal / Render's Logs, to check the feedback against
    # what Azure measured and to tune NATURAL_ACCURACY
    words = " | ".join(f"{w['word']} {w['accuracy']} {w['sounds']}" for w in result["words"])
    missing = f" | not heard: {', '.join(result['missing'])}" if result["missing"] else ""
    print(f"Azure: accuracy {result['accuracy']}, completeness {result['completeness']} | {words or 'no words'}{missing}")
    return result


# Picks out the parts we use from Azure's answer

def read_azure_answer(answer):
    # Silence or noise: nothing was heard
    if answer.get("RecognitionStatus") != "Success" or not answer.get("NBest"):
        return {"heard": "", "accuracy": 0, "completeness": 0, "words": [], "missing": []}

    best = answer["NBest"][0]
    # Depending on the version, the scores are either right on "best"
    # or inside "PronunciationAssessment"
    scores = best.get("PronunciationAssessment", best)

    words = []
    missing = []
    for word in best.get("Words", []):
        word_scores = word.get("PronunciationAssessment", word)
        error_type = word_scores.get("ErrorType", "None")
        accuracy = word_scores.get("AccuracyScore", 100)

        # Words Azure couldn't find. That can mean the learner skipped them, or
        # said them so differently they weren't recognized (Rhea's American
        # "aap" in "aap kaisi hain", 2026-11-18). We can't tell which.
        if error_type == "Omission":
            missing.append(word["Word"])
            continue
        # Extra words are caught by the word check instead
        if error_type == "Insertion":
            continue

        # One score per sound, in order. For Hindi, Azure doesn't say which
        # sound is which, so sounds.py works that out.
        sounds = []
        for sound in word.get("Phonemes", []):
            sound_scores = sound.get("PronunciationAssessment", sound)
            sounds.append(sound_scores.get("AccuracyScore", 100))

        words.append({
            "word": word["Word"],
            "accuracy": accuracy,
            "weak": error_type == "Mispronunciation" or accuracy < WEAK_WORD_ACCURACY,
            "sounds": sounds,
        })

    return {
        "heard": answer.get("DisplayText") or best.get("Display", ""),
        "accuracy": scores.get("AccuracyScore", 0),
        # How much of the phrase was said (100 = all of it)
        "completeness": scores.get("CompletenessScore", 100),
        "words": words,
        "missing": missing,
    }
