import json
import time
import random
from config import client, TEXT_MODEL, CONVERSATION_REASONING, NATURAL_HINDI_RULES, MAX_CONVERSATION_TURNS, MAX_TEXT_LENGTH
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

# Short descriptions shown to the learner when choosing a conversation
SCENARIO_INTROS = {
    "Phone call with Nani": "Nani calls from India. She wants to know if you've eaten, how you are, and when you're visiting.",
    "Talking to family": "Your Mausi catches you at a family get-together, full of questions.",
    "Ordering food": "You're at a dhaba in Delhi. Order something good.",
    "Introducing yourself": "A family friend meets you at a wedding and wants to know all about you.",
    "Talking about your day": "Your older cousin wants to hear about your day.",
}


# How each character opens the call. Ready-made, so "Start the call" needs
# no AI and the audio can be made once and reused (it used to take 5-10 s).
# Written so they work for any learner (no "kaise/kaisi" about them).
# DRAFT: to be reviewed by a native speaker, like the lessons.
OPENING_LINES = {
    "Phone call with Nani": [
        {"reply": "Hello beta! Sab theek? Khana kha liya?", "reply_devanagari": "हैलो बेटा! सब ठीक? खाना खा लिया?", "reply_english": "Hello dear! All well? Have you eaten?"},
        {"reply": "Arre beta, bahut din ho gaye! Sab theek hai na?", "reply_devanagari": "अरे बेटा, बहुत दिन हो गए! सब ठीक है ना?", "reply_english": "Oh dear, it's been so long! Everything okay?"},
        {"reply": "Hello beta, Nani bol rahi hoon. Khana khaya?", "reply_devanagari": "हैलो बेटा, नानी बोल रही हूँ। खाना खाया?", "reply_english": "Hello dear, it's Nani. Have you eaten?"},
    ],
    "Talking to family": [
        {"reply": "Arre beta, aao aao! Kitne dinon baad mile hain! Sab theek?", "reply_devanagari": "अरे बेटा, आओ आओ! कितने दिनों बाद मिले हैं! सब ठीक?", "reply_english": "Oh dear, come in, come in! It's been so long! All well?"},
        {"reply": "Beta, aajkal kya chal raha hai? Padhai kaisi chal rahi hai?", "reply_devanagari": "बेटा, आजकल क्या चल रहा है? पढ़ाई कैसी चल रही है?", "reply_english": "Dear, what's going on these days? How are your studies going?"},
    ],
    "Ordering food": [
        {"reply": "Haan ji, boliye, kya laaun?", "reply_devanagari": "हाँ जी, बोलिए, क्या लाऊँ?", "reply_english": "Yes, tell me, what can I bring you?"},
        {"reply": "Namaste ji! Aaj kya khaayenge?", "reply_devanagari": "नमस्ते जी! आज क्या खाएँगे?", "reply_english": "Hello! What would you like to eat today?"},
    ],
    "Introducing yourself": [
        {"reply": "Namaste! Aap ladke waalon ki taraf se hain ya ladki waalon ki?", "reply_devanagari": "नमस्ते! आप लड़के वालों की तरफ़ से हैं या लड़की वालों की?", "reply_english": "Hello! Are you from the groom's side or the bride's side?"},
        {"reply": "Namaste! Aapko pehle kabhi nahi dekha. Aapka naam kya hai?", "reply_devanagari": "नमस्ते! आपको पहले कभी नहीं देखा। आपका नाम क्या है?", "reply_english": "Hello! I don't think I've seen you before. What's your name?"},
    ],
    "Talking about your day": [
        {"reply": "Aur sunao, aaj ka din kaisa raha?", "reply_devanagari": "और सुनाओ, आज का दिन कैसा रहा?", "reply_english": "So tell me, how was your day?"},
        {"reply": "Kya haal hai? Aaj poore din kya kiya?", "reply_devanagari": "क्या हाल है? आज पूरे दिन क्या किया?", "reply_english": "How's it going? What did you do all day?"},
    ],
}


# Starts a conversation: the character speaks first, like a real call.
# Picks one of the ready-made openers (no AI). The website adds the audio.
# Returns the opening line (a dictionary) and the history so far.

def start_conversation(scenario):
    if scenario not in SCENARIOS:
        raise ValueError("Please pick a conversation.")

    reply = dict(random.choice(OPENING_LINES[scenario]))
    history = [{"role": "assistant", "content": reply["reply"]}]
    return reply, history


# Conversation Mode function
# history is the list of messages so far, so the AI remembers the conversation.
# Returns the reply (a dictionary) and the updated history.

def conversation_practice(scenario, audio_path, history):
    if scenario not in SCENARIOS:
        raise ValueError("Please pick a conversation.")

    if audio_path is None:
        raise ValueError("Please record something.")

    if len(history) >= MAX_CONVERSATION_TURNS * 2:
        raise ValueError("This conversation is getting long! Start a new one to keep practicing.")

    # Timing for each step shows up in Render's Logs, to see what's slow
    started = time.perf_counter()

    # 1. Transcribe speech to text
    user_text = transcribe_audio(audio_path)
    heard_at = time.perf_counter()

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
        reasoning_effort=CONVERSATION_REASONING,   # faster replies (see config.py)
        response_format={"type": "json_object"},
        messages=messages,
    )

    reply = json.loads(response.choices[0].message.content)
    replied_at = time.perf_counter()

    # 3. Remember this turn
    new_history = history + [
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": reply["reply"]},
    ]

    # 4. Make the character's reply into speech
    reply["audio"] = make_audio(reply["reply_devanagari"])
    done_at = time.perf_counter()

    print(
        f"Conversation reply timing: listening {heard_at - started:.1f}s, "
        f"writing the reply {replied_at - heard_at:.1f}s, voice {done_at - replied_at:.1f}s"
    )
    return reply, new_history


# "How do I say...?" helper
# The learner asks in English mid-conversation without breaking the flow.

def how_do_i_say(question, scenario):
    if not question or question.strip() == "":
        raise ValueError("Type what you want to say in English.")

    if len(question) > MAX_TEXT_LENGTH:
        raise ValueError(f"Please keep it under {MAX_TEXT_LENGTH} characters.")

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
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": prompt}],
    )

    return json.loads(response.choices[0].message.content)
