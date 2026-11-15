import json
from config import client, TEXT_MODEL, NATURAL_HINDI_RULES, MAX_CONVERSATION_TURNS
from audio import transcribe_audio, make_audio

# Conversation scenarios
# Each one has a character the AI plays and how they talk to the learner.
SCENARIOS = {
    "Phone call with Nani": "You are the learner's Nani (maternal grandmother) calling from India. You are warm, a little emotional, ask if they've eaten, about school or work, and give blessings. You call the learner 'beta' and use 'tum'. The learner should use 'aap' with you.",
    "Talking to family": "You are the learner's mausi (mother's sister) at a family get-together. Friendly, curious, a little teasing. You use 'tum' with the learner.",
    "Ordering food": "You are a friendly waiter at a dhaba in Delhi. You use 'aap' with the learner and suggest dishes.",
    "Introducing yourself": "You are a friendly family friend meeting the learner for the first time at a wedding. You use 'aap' and ask about their name, family, and life.",
    "Talking about your day": "You are the learner's older cousin chatting in the evening. Casual and fun. You use 'tum'.",
}


# Conversation Mode function
# history is the list of messages so far, so the AI remembers the conversation.
# Returns the reply (a dictionary) and the updated history.

def conversation_practice(scenario, audio_path, history):
    if audio_path is None:
        raise ValueError("Please record something.")

    if len(history) >= MAX_CONVERSATION_TURNS * 2:
        raise ValueError("This conversation is getting long! Start a new one to keep practicing.")

    # 1. Transcribe speech to text
    user_text = transcribe_audio(audio_path)

    # 2. Get the character's reply
    prompt = f"""
You are a character in a Hindi speaking practice app for Indian heritage learners.
The learner understands some Hindi but cannot read Devanagari.

Your character: {SCENARIOS[scenario]}

Rules:
{NATURAL_HINDI_RULES}
- Stay in character and keep the conversation going naturally.
- Keep replies short (1-3 sentences) so the learner can follow.
- If the learner struggles, use simpler Hindi. If they do well, sound more natural.
- If the learner made a mistake, do NOT interrupt the conversation. Put one
  gentle tip in "side_note" instead (or leave it empty if there's nothing important).
- If the learner used 'tum' or 'tu' with an elder, mention it kindly in "side_note".

Reply ONLY with JSON in this exact format:
{{
  "you_said": "what the learner said, in romanized Hindi",
  "reply": "your reply in romanized Hindi",
  "reply_devanagari": "the same reply in Devanagari (used only for audio)",
  "reply_english": "the English meaning of your reply",
  "side_note": "one short gentle tip in simple English, or empty"
}}
"""

    messages = [{"role": "system", "content": prompt}]
    messages = messages + history
    messages.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        temperature=0.7,
        response_format={"type": "json_object"},
        messages=messages,
    )

    reply = json.loads(response.choices[0].message.content)

    # 3. Remember this turn
    new_history = history + [
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": reply["reply"]},
    ]

    # 4. Make the character's reply into speech
    reply["audio"] = make_audio(reply["reply_devanagari"])

    return reply, new_history


# "How do I say...?" helper
# The learner asks in English mid-conversation without breaking the flow.

def how_do_i_say(question, scenario):
    if not question or question.strip() == "":
        raise ValueError("Type what you want to say in English.")

    prompt = f"""
A Hindi learner is in this conversation: {SCENARIOS[scenario]}
They want to know how to say something. Give the natural way to say it in this
situation, using the right respect level for who they are talking to.

Rules:
{NATURAL_HINDI_RULES}

Reply ONLY with JSON: {{"say_it": "romanized Hindi", "devanagari": "same in Devanagari", "note": "one short tip"}}
"""

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
    )

    result = json.loads(response.choices[0].message.content)
    result["audio"] = make_audio(result["devanagari"])
    return result


# End-of-conversation summary

def conversation_summary(scenario, history):
    if len(history) == 0:
        raise ValueError("Have a conversation first!")

    transcript = "\n".join(
        f"{'Learner' if m['role'] == 'user' else 'Character'}: {m['content']}"
        for m in history
    )

    prompt = f"""
You are a warm Hindi tutor. Here is a practice conversation ({scenario}).

{transcript}

Write a short, encouraging summary for the learner in simple English. No scores or grades.
Rules:
{NATURAL_HINDI_RULES}

Reply ONLY with JSON in this exact format:
{{
  "went_well": ["specific things they did well", "..."],
  "work_on": ["2-3 specific things to work on", "..."],
  "useful_phrases": ["romanized phrase = English meaning", "..."]
}}
"""

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": prompt}],
    )

    return json.loads(response.choices[0].message.content)
