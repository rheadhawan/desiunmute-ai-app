import gradio as gr
from openai import OpenAI
import os
import re
import jiwer

client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

# Translator function

def desilingo_translate(text, gender = "female", politeness = "casual", pronunciation = "Yes"):
    prompt = f"""
You are a Hindi language tutor. Translate the following English sentence into natural,
conversational Hindi using romanized Hindi. Make sure the pronunciation is exactly how a
native Hindi would speak.

Rules:
- Always output in romanized Hindi.
- Adjust conjugation for gender: {gender}.
- Use the politeness level: {politeness}.
- After the translation, include sections:

Translation:
Breakdown:
Pronunciation:
Alternatives:
Mistakes:

English sentence: "{text}"
"""

    # Query OpenAI
    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        temperature = 0.3,
        messages = [{"role": "system", "content": prompt}]
    )

    fullOutput = response.choices[0].message.content

    # Extract pronunciation line from output
    match = re.search(r"Pronunciation:\s*(.*)", fullOutput)
    if match:
        pronunciation_text = match.group(1).strip()
    else:
        pronunciation_text = "No pronunication found"

    # creates audio from pronunciation
    audio = client.audio.speech.create(
        model = "gpt-4o-mini-tts",
        voice = "alloy",
        input = pronunciation_text
    )

    audioBytes = audio.read()

    return fullOutput, audioBytes

# Pronunciation feedback function
def pronunciation_feedback(user_audio, target_phrase):
    if user_audio is None:
        return "Please record your pronunciation."

    if not target_phrase or target_phrase.strip() == "":
        return "Please type the Hindi phrase you were trying to say."

    file_path = user_audio  # Gradio provides a filepath

    # 1. TRANSCRIBE AUDIO
    with open(file_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=f
        ).text

    # 2. NORMALIZE TEXT (romanized Hindi comparison)
    def normalize(t):
        t = t.lower()
        t = re.sub(r"[^a-z ]", "", t)
        t = re.sub(r"\s+", " ", t)
        return t.strip()

    target_clean = normalize(target_phrase)
    transcript_clean = normalize(transcript)

    # 3. MEASURE DIFFERENCE
    wer = jiwer.wer(target_clean, transcript_clean)

    # 4. HARD GATE — IF IT MATCHES, STOP HERE
    if wer <= 0.15:
        return f"""Overall:
- Excellent pronunciation — no significant issues detected.

Key differences:
- No significant pronunciation differences.

How to practice:
- Your pronunciation is correct. Continue speaking naturally and confidently.

Better example (romanized):
- {target_phrase}
"""

    # 5. ONLY NOW generate corrective feedback
    feedback_prompt = f"""
You are a Hindi pronunciation coach.

Target phrase (intended):
"{target_phrase}"

What the learner actually said (transcribed):
"{transcript}"

IMPORTANT RULES:
- ONLY comment on REAL pronunciation differences visible in the transcription.
- DO NOT invent issues.
- Ignore softness, breathiness, accent, or volume.
- If a sound is acceptable, do NOT criticize it.
- Treat all dialects as valid Hindi.

Respond in this EXACT format:

Overall:
- One short, honest sentence summarizing pronunciation quality.

Key differences:
- 2–4 bullet points describing ONLY real phonetic differences
  (romanized Hindi only).

How to practice:
- 1–2 practical exercises.

Better example (romanized):
- Ideal pronunciation of the target phrase.
"""

    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": feedback_prompt}]
    )

    return result.choices[0].message.content

# Gradio UI tabs

with gr.Blocks() as ui:
    gr.Markdown("# **DesiLingo - Hindi AI Tutor**")

    with gr.Tabs():

        # Translation Tutor 
        with gr.Tab("Translate"):
            input_text = gr.Textbox(label = "English Sentence")
            gender = gr.Radio(["Male","Female"], label = "Gender", value = "Male")
            politeness = gr.Radio(["Casual","Formal"], label = "Politeness Level")
            pronunciation = gr.Radio(["Yes","No"], label = "Generate pronunciation?", value = "Yes")

            translate_button = gr.Button("Translate")

            translate_ouput = gr.Textbox(label = "Translation")
            translate_audio = gr.Audio(label = "Pronunciation Audio", type = "filepath")

            translate_button.click(
                desilingo_translate,
                inputs = [input_text, gender, politeness, pronunciation],
                outputs = [translate_ouput, translate_audio]
            )

        # Pronunciation Coach
        with gr.Tab("Pronunciation Coach"):
            target_phrase = gr.Textbox(
                label = "What phrase were you trying to say?",
                placeholder = "Type the Hindi phrase (e.g., 'namaste', 'aap kaise ho')"
            )

            user_audio = gr.Audio(sources = "microphone", type = "filepath", label = "Record your pronunciation")

            feedback_button = gr.Button("Get feedback!")
            feedback_output = gr.Textbox(label = "Feedback", lines = 10)

            feedback_button.click(
                pronunciation_feedback,
                inputs = [user_audio, target_phrase],
                outputs = [feedback_output]
            )

ui.launch()