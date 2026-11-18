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


def azure_is_set_up():
    return bool(AZURE_SPEECH_KEY)


# Sends a recording to Azure and returns what it heard and how Hindi it sounded.
# wav_path must be WAV, 16 kHz, mono (the browser converts recordings to this).
# reference must be in Devanagari, so Azure knows which Hindi sounds to expect.

def check_pronunciation(wav_path, reference):
    settings = {
        "ReferenceText": reference,
        "GradingSystem": "HundredMark",
        "Granularity": "Word",
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

    # Shows up in Terminal / Render's Logs, to tune NATURAL_ACCURACY
    print(f"Azure: accuracy {result['accuracy']}, weak words: {result['weak_words'] or 'none'}")
    return result


# Picks out the parts we use from Azure's answer

def read_azure_answer(answer):
    # Silence or noise: nothing was heard
    if answer.get("RecognitionStatus") != "Success" or not answer.get("NBest"):
        return {"heard": "", "accuracy": 0, "weak_words": []}

    best = answer["NBest"][0]
    # Depending on the version, the scores are either right on "best"
    # or inside "PronunciationAssessment"
    scores = best.get("PronunciationAssessment", best)

    weak_words = []
    for word in best.get("Words", []):
        word_scores = word.get("PronunciationAssessment", word)
        error_type = word_scores.get("ErrorType", "None")
        accuracy = word_scores.get("AccuracyScore", 100)

        # Missing and extra words are caught by the word check instead
        if error_type in ("Omission", "Insertion"):
            continue
        if error_type == "Mispronunciation" or accuracy < WEAK_WORD_ACCURACY:
            weak_words.append(word["Word"])

    return {
        "heard": answer.get("DisplayText") or best.get("Display", ""),
        "accuracy": scores.get("AccuracyScore", 0),
        "weak_words": weak_words,
    }
