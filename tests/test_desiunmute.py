import json
from unittest.mock import MagicMock
import pytest

import translate
import pronunciation
import conversation
import audio
import azure_speech


# Fake OpenAI helpers (so tests don't cost money or need an API key)

def fake_chat_reply(data):
    response = MagicMock()
    response.choices[0].message.content = json.dumps(data)
    return response


def fake_client(*chat_replies):
    client = MagicMock()
    client.chat.completions.create.side_effect = [fake_chat_reply(d) for d in chat_replies]
    return client


# Translate tests

def test_translate_returns_romanized_text_and_audio(monkeypatch):
    client = fake_client({
        "translation": "aap kaise hain?",
        "devanagari": "आप कैसे हैं?",
        "breakdown": ["aap = you (respectful)"],
        "pronunciation_tips": [],
        "alternatives": [],
        "common_mistakes": [],
    })
    monkeypatch.setattr(translate, "client", client)
    monkeypatch.setattr(translate, "make_audio", lambda text: b"audio for " + text.encode())

    result = translate.desiunmute_translate("How are you?", "Female", "An elder", "Yes")

    assert result["translation"] == "aap kaise hain?"
    assert result["audio"] == "audio for आप कैसे हैं?".encode()   # voice gets Devanagari
    prompt = client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert "aap" in prompt                 # elder respect rule is in the prompt
    assert "female" in prompt


def test_translate_skips_audio_when_turned_off(monkeypatch):
    monkeypatch.setattr(translate, "client", fake_client({"translation": "haan", "devanagari": "हाँ"}))
    make_audio = MagicMock()
    monkeypatch.setattr(translate, "make_audio", make_audio)

    result = translate.desiunmute_translate("Yes", pronunciation="No")

    assert result["audio"] is None
    make_audio.assert_not_called()


def test_translate_rejects_empty_and_long_text():
    with pytest.raises(ValueError):
        translate.desiunmute_translate("   ")
    with pytest.raises(ValueError):
        translate.desiunmute_translate("a" * 1000)


def test_format_translation_shows_learner_friendly_headings():
    text = translate.format_translation({"translation": "haan", "breakdown": ["haan = yes"]})
    assert "## haan" in text
    assert "Common mistakes" in text
    assert "Devanagari" not in text


# Pronunciation tests

def test_spelling_variants_count_as_the_same():
    assert pronunciation.simplify_spelling("Aap kese ho?") == pronunciation.simplify_spelling("aap kaise ho")
    assert pronunciation.simplify_spelling("main theek hoon") == pronunciation.simplify_spelling("main thik hun".replace("hun", "hoon"))
    assert pronunciation.simplify_spelling("nai") == pronunciation.simplify_spelling("nahi")


def test_hai_and_hain_stay_different():
    # hain (respectful) vs hai is a real difference, so it must still count
    assert pronunciation.simplify_spelling("aap kaise hain") != pronunciation.simplify_spelling("aap kaise hai")


def run_pronunciation(monkeypatch, heard):
    client = fake_client(
        {"romanized": heard},
        {"overall": "Nice!", "went_well": ["clear"], "tips": [], "focus_sounds": [], "better_example": "aap kaise ho"},
    )
    monkeypatch.setattr(pronunciation, "client", client)
    monkeypatch.setattr(pronunciation, "transcribe_audio", lambda path: "आप कैसे हो")
    return pronunciation.pronunciation_feedback("recording.wav", "aap kaise ho")


def test_correct_devanagari_transcript_sounds_natural(monkeypatch):
    # This was the old bug: Devanagari got deleted and nobody ever got "Excellent"
    result = run_pronunciation(monkeypatch, "aap kaise ho")
    assert result["result_level"] == "sounds natural"
    assert result["accuracy"] == 1.0


def test_spelling_difference_is_not_a_mistake(monkeypatch):
    result = run_pronunciation(monkeypatch, "aap kese ho")
    assert result["result_level"] == "sounds natural"


def test_wrong_words_are_caught(monkeypatch):
    result = run_pronunciation(monkeypatch, "tum kahan ho")
    assert result["result_level"] == "keep practicing"


def test_coaching_happens_even_on_good_attempts(monkeypatch):
    result = run_pronunciation(monkeypatch, "aap kaise ho")
    assert result["overall"] == "Nice!"
    assert "Every word came through" in pronunciation.format_feedback(result)


def test_pronunciation_needs_audio_and_phrase():
    with pytest.raises(ValueError):
        pronunciation.pronunciation_feedback(None, "aap kaise ho")
    with pytest.raises(ValueError):
        pronunciation.pronunciation_feedback("recording.wav", "")


def test_devanagari_target_gets_a_helpful_message(monkeypatch):
    monkeypatch.setattr(pronunciation, "client", fake_client({"romanized": "aap kaise ho"}))
    monkeypatch.setattr(pronunciation, "transcribe_audio", lambda path: "आप कैसे हो")
    with pytest.raises(ValueError, match="romanized"):
        pronunciation.pronunciation_feedback("recording.wav", "आप कैसे हो")


# Conversation tests

def nani_reply(text):
    return {
        "you_said": text,
        "reply": "khana khaya beta?",
        "reply_devanagari": "खाना खाया बेटा?",
        "reply_english": "Did you eat, dear?",
        "side_note": "",
    }


def test_conversation_remembers_previous_turns(monkeypatch):
    client = fake_client(nani_reply("namaste nani"), nani_reply("haan nani"))
    monkeypatch.setattr(conversation, "client", client)
    monkeypatch.setattr(conversation, "transcribe_audio", lambda path: "नमस्ते नानी")
    monkeypatch.setattr(conversation, "make_audio", lambda text: b"mp3")

    reply, history = conversation.conversation_practice("Phone call with Nani", "a.wav", [])
    assert len(history) == 2
    assert reply["audio"] == b"mp3"

    reply, history = conversation.conversation_practice("Phone call with Nani", "b.wav", history)
    assert len(history) == 4
    # The second request includes the first turn, so the AI remembers it
    second_messages = client.chat.completions.create.call_args.kwargs["messages"]
    assert len(second_messages) == 4   # system + 2 earlier + new


def test_conversation_stops_when_too_long():
    long_history = [{"role": "user", "content": "x"}] * 100
    with pytest.raises(ValueError):
        conversation.conversation_practice("Phone call with Nani", "a.wav", long_history)


def test_summary_needs_a_conversation():
    with pytest.raises(ValueError):
        conversation.conversation_summary("Phone call with Nani", [])


# Audio tests

import array
import base64
import contextlib
import types


# Makes pretend audio: speech is a loud tone, a pause is silence (24,000 samples a second)
def pretend_audio(*parts):
    samples = array.array("h")
    for kind, seconds in parts:
        count = int(24000 * seconds)
        if kind == "speech":
            samples.extend(8000 if i % 20 < 10 else -8000 for i in range(count))
        else:
            samples.extend(0 for i in range(count))
    return samples.tobytes()


SMOOTH = pretend_audio(("speech", 1.0), ("pause", 0.2), ("speech", 1.0))
ODD_PAUSE = pretend_audio(("speech", 1.0), ("pause", 0.6), ("speech", 1.0))


# A pretend realtime connection. takes = [(audio, words it says it spoke), ...]
def pretend_voice(monkeypatch, takes):
    sessions = []

    class Connection:
        def __init__(self):
            self.session = types.SimpleNamespace(update=lambda **kwargs: sessions.append(kwargs["session"]))
            self.conversation = types.SimpleNamespace(item=types.SimpleNamespace(create=lambda **kwargs: None))
            self.response = types.SimpleNamespace(create=lambda **kwargs: None)

        def __iter__(self):
            pcm, words = takes.pop(0)
            yield types.SimpleNamespace(type="response.output_audio.delta", delta=base64.b64encode(pcm).decode())
            yield types.SimpleNamespace(type="response.output_audio_transcript.delta", delta=words)
            yield types.SimpleNamespace(type="response.done")

    @contextlib.contextmanager
    def connect(model):
        assert model == "gpt-realtime-2.1-mini"
        yield Connection()

    client = MagicMock()
    client.realtime.connect = connect
    monkeypatch.setattr(audio, "client", client)
    return sessions


def test_voice_uses_marin_and_hindi_read_aloud_rules(monkeypatch):
    sessions = pretend_voice(monkeypatch, [(SMOOTH, "नमस्ते जी")])
    audio.make_audio("नमस्ते जी")
    session = sessions[0]
    assert session["audio"]["output"]["voice"] == "marin"
    assert "word for word" in session["instructions"]
    assert "Indian accent" in session["instructions"]


def test_smooth_take_is_kept_and_turned_into_mp3(monkeypatch):
    pretend_voice(monkeypatch, [(SMOOTH, "नमस्ते जी।")])     # punctuation differences are fine
    result = audio.make_audio("नमस्ते जी")
    assert result[:3] == b"ID3" or result[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")   # an MP3
    assert len(result) < len(SMOOTH) / 3                                                 # much smaller


def test_odd_pause_is_re_recorded(monkeypatch):
    takes = [(ODD_PAUSE, "नानी जी"), (SMOOTH, "नानी जी")]
    pretend_voice(monkeypatch, takes)
    audio.make_audio("नानी जी")
    assert takes == []          # both takes were used: the odd one, then a smooth one


def test_keeps_smoothest_take_after_three_tries(monkeypatch):
    longer_pause = pretend_audio(("speech", 1.0), ("pause", 0.9), ("speech", 1.0))
    pretend_voice(monkeypatch, [(longer_pause, "नानी जी"), (ODD_PAUSE, "नानी जी"), (longer_pause, "नानी जी")])
    result = audio.make_audio("नानी जी")
    assert result == audio.to_mp3(ODD_PAUSE)      # 0.6s beats 0.9s


def test_take_that_changes_the_words_is_not_kept(monkeypatch):
    pretend_voice(monkeypatch, [(SMOOTH, "हेलो"), (ODD_PAUSE, "नमस्ते जी"), (ODD_PAUSE, "नमस्ते जी")])
    result = audio.make_audio("नमस्ते जी")
    assert result == audio.to_mp3(ODD_PAUSE)      # a pause is better than the wrong words


def test_longest_pause_measures_the_middle_only():
    with_edges = pretend_audio(("pause", 1.0), ("speech", 0.5), ("pause", 0.3), ("speech", 0.5), ("pause", 1.0))
    assert abs(audio.longest_pause(with_edges) - 0.3) < 0.05


def test_no_audio_is_an_error(monkeypatch):
    pretend_voice(monkeypatch, [(b"", "")])
    with pytest.raises(RuntimeError):
        audio.make_audio("नमस्ते")


# Lesson content checks (catch typos in lessons.py)

import lessons


def test_every_check_answer_is_one_of_the_options():
    for unit in lessons.UNITS:
        for item in unit.get("check", []):
            assert item["answer"] in item["options"], item["question"]


def test_every_lesson_phrase_has_devanagari_for_the_voice():
    for example in lessons.all_lesson_phrases():
        assert example["devanagari"].strip(), example["phrase"]
        assert example["english"].strip(), example["phrase"]


def test_personalize_lesson_prompt_includes_lesson_and_gender(monkeypatch):
    client = fake_client({"examples": [{"phrase": "x", "english": "y", "note": "z"}]})
    monkeypatch.setattr(lessons, "client", client)

    lessons.personalize_lesson(lessons.get_unit(1), "My Nani lives in Jaipur", "Male")

    prompt = client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert "Talking to elders the right way" in prompt
    assert "male" in prompt


def test_text_features_use_gpt_6_luna():
    import config
    assert config.TEXT_MODEL == "gpt-6-luna"


def test_coach_is_told_it_cannot_hear_accents(monkeypatch):
    monkeypatch.setattr(pronunciation, "transcribe_audio", lambda path: "नमस्ते जी")
    monkeypatch.setattr(pronunciation, "romanize_transcript", lambda transcript, target: "namaste ji")
    client = fake_client({"overall": "x", "went_well": [], "tips": [], "focus_sounds": [], "better_example": "namaste ji"})
    monkeypatch.setattr(pronunciation, "client", client)

    pronunciation.pronunciation_feedback("a.wav", "namaste ji")

    prompt = client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert "not how they sounded" in prompt
    assert "Never say their" in prompt


# Azure accent check

# Rhea's American "ney-meh-ste ji" in Speech Studio (2026-11-18):
# नमस्ते scored 41, its 7 sounds (n a m a s t e) scored 18 0 14 52 48 75 38
AMERICAN_NAMASTE = [18, 0, 14, 52, 48, 75, 38]


def azure_answer(accuracy, words):
    return {
        "RecognitionStatus": "Success",
        "DisplayText": "नमस्ते जी।",
        "NBest": [{
            "Display": "नमस्ते जी।",
            "AccuracyScore": accuracy,
            "Words": [
                {"Word": w, "AccuracyScore": a, "ErrorType": e, "Phonemes": [{"Phoneme": "", "AccuracyScore": n} for n in sounds]}
                for w, a, e, sounds in words
            ],
        }],
    }


def test_azure_answer_keeps_word_and_sound_scores():
    answer = azure_answer(55, [
        ("नमस्ते", 41, "Mispronunciation", AMERICAN_NAMASTE),
        ("जी", 95, "None", [96, 94]),
        ("आप", 0, "Omission", []),
    ])
    result = azure_speech.read_azure_answer(answer)
    assert result["heard"] == "नमस्ते जी।"
    assert result["accuracy"] == 55
    assert result["missing"] == ["आप"]
    assert result["words"] == [
        {"word": "नमस्ते", "accuracy": 41, "weak": True, "sounds": AMERICAN_NAMASTE},
        {"word": "जी", "accuracy": 95, "weak": False, "sounds": [96, 94]},
    ]


def test_azure_answer_with_scores_inside_pronunciation_assessment():
    answer = {
        "RecognitionStatus": "Success",
        "DisplayText": "नमस्ते",
        "NBest": [{
            "PronunciationAssessment": {"AccuracyScore": 93},
            "Words": [{
                "Word": "नमस्ते",
                "PronunciationAssessment": {"AccuracyScore": 70, "ErrorType": "None"},
                "Phonemes": [{"Phoneme": "", "PronunciationAssessment": {"AccuracyScore": 60}}],
            }],
        }],
    }
    result = azure_speech.read_azure_answer(answer)
    assert result["accuracy"] == 93
    assert result["words"][0]["weak"] is True
    assert result["words"][0]["sounds"] == [60]


def test_azure_heard_nothing():
    result = azure_speech.read_azure_answer({"RecognitionStatus": "NoMatch"})
    assert result == {"heard": "", "accuracy": 0, "completeness": 0, "words": [], "missing": []}


def test_azure_request_asks_for_sound_scores(monkeypatch, tmp_path):
    import base64
    sent = {}

    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return json.dumps(azure_answer(93, [])).encode()

    def fake_urlopen(request, timeout):
        sent["url"] = request.full_url
        sent["headers"] = dict(request.header_items())
        return FakeResponse()

    monkeypatch.setattr(azure_speech.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(azure_speech, "AZURE_SPEECH_KEY", "test-key")
    wav = tmp_path / "recording.wav"
    wav.write_bytes(b"RIFF")

    result = azure_speech.check_pronunciation(str(wav), "नमस्ते जी")

    assert result["accuracy"] == 93
    assert sent["url"].startswith("https://westus3.stt.speech.microsoft.com/")
    assert "language=hi-IN" in sent["url"]
    settings = json.loads(base64.b64decode(sent["headers"]["Pronunciation-assessment"]))
    assert settings["ReferenceText"] == "नमस्ते जी"
    assert settings["Granularity"] == "Phoneme"


# Splitting words into sounds (must match how Azure counts them)

def test_namaste_has_the_same_7_sounds_as_azure():
    import sounds
    split = sounds.split_sounds("नमस्ते")
    assert [s["letter"] for s in split] == ["न", "अ", "म", "अ", "स", "त", "ए"]
    parts = sounds.word_parts(split)
    assert [sounds.romanize_part(split, p) for p in parts] == ["na", "mas", "te"]


@pytest.mark.parametrize("word, spoken", [
    ("आप", "aap"),           # no "a" at the end
    ("बोलना", "bol·naa"),    # no "a" in the middle
    ("समझ", "sa·majh"),
    ("कैसे", "kai·se"),
    ("जी", "jee"),
    ("प्रणाम", "pra·naam"),
    ("थोड़ा", "tho·daa"),
])
def test_words_split_the_way_they_are_spoken(word, spoken):
    import sounds
    split = sounds.split_sounds(word)
    assert "·".join(sounds.romanize_part(split, p) for p in sounds.word_parts(split)) == spoken


def word(text, accuracy, sounds, weak=None):
    return {"word": text, "accuracy": accuracy, "sounds": sounds, "weak": accuracy < 80 if weak is None else weak}


def run_with_azure(monkeypatch, accuracy, words=(), heard="namaste ji", completeness=100, missing=()):
    client = fake_client(
        {"romanized": heard},
        {"overall": "Nice!", "went_well": ["Both words came through"], "tips": ["Luna's own tip"],
         "focus_sounds": ["Luna's own sound"], "better_example": "namaste ji"},
    )
    monkeypatch.setattr(pronunciation, "client", client)
    monkeypatch.setattr(pronunciation, "check_pronunciation", lambda path, reference: {
        "heard": "नमस्ते जी", "accuracy": accuracy, "completeness": completeness,
        "words": list(words), "missing": list(missing),
    })
    result = pronunciation.pronunciation_feedback("a.wav", "namaste ji", "नमस्ते जी")
    prompt = client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    return result, prompt


def test_natural_accent_sounds_natural(monkeypatch):
    # Rhea's natural "namaste ji" got 90 and 93
    result, prompt = run_with_azure(monkeypatch, 93, [word("नमस्ते", 92, [90] * 7), word("जी", 95, [95, 95])])
    assert result["result_level"] == "sounds natural"
    assert result["accent_checked"] is True
    assert result["tips"] == [] and result["focus_sounds"] == []
    assert pronunciation.feedback_heading(result) == "Every word came through, and it sounds natural"
    assert "natural, like a Hindi speaker" in prompt


def test_american_na_is_pointed_out_not_the_t(monkeypatch):
    # The bug Rhea found: the coach talked about the "t", but she changed the "na"
    result, prompt = run_with_azure(monkeypatch, 76, [word("नमस्ते", 41, AMERICAN_NAMASTE), word("जी", 90, [90, 90])])

    assert result["result_level"] == "polish the sounds"
    assert pronunciation.feedback_heading(result) == "Now let's polish the sounds"
    assert "don't say \"every word came through\"" in prompt
    assert result["focus_sounds"] == ["the \"na\" in 'namaste'"]
    assert result["tips"][0].startswith("Focus on the \"na\" in 'namaste'. The \"a\" there is short and relaxed")
    assert "Play the Slow audio, say \"na\"" in result["tips"][-1]
    assert "Luna's own tip" not in result["tips"]          # Luna can't add sound tips
    assert not any("tongue" in tip for tip in result["tips"])   # nothing about the "t"
    assert "the \"na\" in 'namaste'" in prompt
    assert "soft \"t\"" not in prompt                     # no example tips to copy


def test_different_mistakes_get_different_tips(monkeypatch):
    american_t = [90, 90, 90, 90, 85, 20, 88]                 # only the "t" was off
    result, _ = run_with_azure(monkeypatch, 76, [word("नमस्ते", 60, american_t)])
    assert result["focus_sounds"] == ["the \"te\" in 'namaste'"]
    assert "tongue" in result["tips"][0]


def test_only_the_word_is_named_when_sound_scores_dont_line_up(monkeypatch):
    result, _ = run_with_azure(monkeypatch, 76, [word("नमस्ते", 41, [18, 0, 14])])
    assert result["focus_sounds"] == ["'namaste'"]
    assert result["tips"][0] == "'namaste' sounded the least natural. Listen to how the Hindi audio says it and copy it."


def test_no_weak_word_gives_general_practice_only(monkeypatch):
    result, prompt = run_with_azure(monkeypatch, 80, [word("नमस्ते", 85, [85] * 7), word("जी", 82, [80, 84])])
    assert result["focus_sounds"] == []
    assert result["tips"] == ["Play the Slow audio and copy it closely, sound by sound, then say the whole phrase again."]
    assert "no single word or sound" in prompt


def test_wrong_words_come_first_even_with_azure(monkeypatch):
    result, _ = run_with_azure(monkeypatch, 60, [word("नमस्ते", 41, AMERICAN_NAMASTE)], heard="kya haal hai")
    assert result["result_level"] == "keep practicing"
    assert result["tips"] == ["Luna's own tip"]               # word tips only, no sound tips yet
    assert result["focus_sounds"] == []


def test_nothing_heard_skips_romanizing(monkeypatch):
    client = fake_client({"overall": "x", "went_well": [], "tips": [], "focus_sounds": [], "better_example": "namaste ji"})
    monkeypatch.setattr(pronunciation, "client", client)
    monkeypatch.setattr(pronunciation, "check_pronunciation", lambda path, reference: {"heard": "", "accuracy": 0, "completeness": 0, "words": [], "missing": []})
    result = pronunciation.pronunciation_feedback("a.wav", "namaste ji", "नमस्ते जी")
    # Rhea's "ney-meh-ste" once came back with no words: say so, don't judge the accent
    assert result["result_level"] == "nothing heard"
    assert pronunciation.feedback_heading(result) == "We couldn't hear that clearly"
    assert "natural" not in result["overall"]
    assert client.chat.completions.create.call_count == 0   # nothing for Luna to say


def test_stray_period_is_removed(monkeypatch):
    result, _ = run_with_azure(monkeypatch, 93, heard="namaste ji.")
    assert result["heard"] == "namaste ji"


def test_muddled_sound_scores_only_name_the_word(monkeypatch):
    # Rhea's site test (2026-11-18): Azure lost track of "ney-ma-ste"
    muddled = [85, 0, 0, 0, 0, 0, 0]
    result, _ = run_with_azure(monkeypatch, 60, [word("नमस्ते", 51, muddled)])
    assert result["focus_sounds"] == ["'namaste'"]
    assert result["tips"][0].startswith("'namaste' sounded the least natural")


def test_sounds_with_nothing_useful_to_say_just_say_listen(monkeypatch):
    # "ji" is one part, so there's nothing to compare: just name the word
    result, _ = run_with_azure(monkeypatch, 70, [word("जी", 50, [40, 40])])
    assert result["tips"][0] == "'ji' sounded the least natural. Listen to how the Hindi audio says it and copy it."
    assert "plain" not in " ".join(result["tips"])


def test_biggest_problem_comes_first(monkeypatch):
    result, _ = run_with_azure(monkeypatch, 60, [
        word("नमस्ते", 55, [18, 0, 14, 52, 48, 75, 38]),   # "na" averages 9
        word("जी", 50, [40, 40]),                          # only the word, 50
    ])
    assert result["focus_sounds"] == ["the \"na\" in 'namaste'", "'ji'"]


def test_low_completeness_alone_is_not_a_missing_word(monkeypatch):
    # Rhea's American "aap kaisi hain", every word said: completeness 67 anyway.
    # Completeness drops for badly said words too, so it isn't used.
    result, _ = run_with_azure(
        monkeypatch, 71,
        [word("नमस्ते", 50, [48, 31, 40, 40, 40, 40, 40]), word("जी", 63, [83, 40])],
        completeness=67,
    )
    assert result["result_level"] == "polish the sounds"
    assert not any("couldn't clearly hear" in tip for tip in result["tips"])


def test_word_azure_couldnt_find_is_named(monkeypatch):
    # Rhea's American "aap kaisi hain": Azure couldn't find "aap" (completeness 67)
    result, prompt = run_with_azure(
        monkeypatch, 50, [word("जी", 90, [90, 90])], completeness=67, missing=["नमस्ते"],
    )
    assert result["result_level"] == "close"
    assert result["tips"][0] == "We couldn't clearly hear 'namaste'. Make sure you say it, and copy how the Hindi audio says it."
    assert result["focus_sounds"] == ["'namaste'"]
    assert "couldn't clearly hear: 'namaste'" in prompt
    assert "never \"you didn't say\"" in prompt
