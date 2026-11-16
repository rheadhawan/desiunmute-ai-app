import json
from unittest.mock import MagicMock
import pytest

import translate
import pronunciation
import conversation
import audio


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
    assert "Sounds natural" in pronunciation.format_feedback(result)


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

def test_voice_gets_hindi_accent_instructions(monkeypatch):
    client = MagicMock()
    client.audio.speech.create.return_value.read.return_value = b"mp3"
    monkeypatch.setattr(audio, "client", client)

    assert audio.make_audio("नमस्ते") == b"mp3"
    kwargs = client.audio.speech.create.call_args.kwargs
    assert kwargs["input"] == "नमस्ते"
    assert "Hindi" in kwargs["instructions"]


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
