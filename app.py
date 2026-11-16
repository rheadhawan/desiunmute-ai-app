import os
import tempfile
import gradio as gr

from config import TALKING_TO
from translate import desiunmute_translate, format_translation
from pronunciation import pronunciation_feedback, format_feedback
from conversation import SCENARIOS, conversation_practice, how_do_i_say, conversation_summary

# Helpers

# Gradio plays audio from a file, so save the audio bytes to a temporary file
def save_audio(audio_bytes):
    if audio_bytes is None:
        return None
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio_bytes)
        return f.name


# Shows a friendly message instead of crashing
def show_error(error):
    if isinstance(error, ValueError):
        raise gr.Error(str(error))
    print("ERROR:", repr(error))   # shows up in the Space logs
    raise gr.Error("Something went wrong talking to the AI. Please try again in a moment.")


# Translate tab

def translate_tab(text, gender, talking_to, pronunciation):
    try:
        result = desiunmute_translate(text, gender, talking_to, pronunciation)
    except Exception as error:
        show_error(error)

    audio_path = save_audio(result["audio"])
    return format_translation(result), audio_path, result["translation"], audio_path


# Sends the translated phrase (and its audio) to the Pronunciation Coach tab
def practice_this_phrase(last_phrase, last_audio):
    if not last_phrase:
        raise gr.Error("Translate something first!")
    return last_phrase, last_audio, gr.Tabs(selected="pronunciation")


# Pronunciation tab

def pronunciation_tab(user_audio, target_phrase):
    try:
        result = pronunciation_feedback(user_audio, target_phrase)
    except Exception as error:
        show_error(error)

    return format_feedback(result)


# Conversation tab

def conversation_tab(scenario, audio_path, history, chat):
    try:
        reply, history = conversation_practice(scenario, audio_path, history)
    except Exception as error:
        show_error(error)

    chat = chat + [
        {"role": "user", "content": reply["you_said"]},
        {"role": "assistant", "content": f"{reply['reply']}\n\n*{reply['reply_english']}*"},
    ]

    side_note = f"**Tip:** {reply['side_note']}" if reply.get("side_note") else ""

    # Clear the microphone so the learner can record the next reply
    return chat, history, save_audio(reply["audio"]), side_note, None


def how_do_i_say_tab(question, scenario):
    try:
        result = how_do_i_say(question, scenario)
    except Exception as error:
        show_error(error)

    answer = f"**Say:** {result['say_it']}\n\n{result['note']}"
    return answer, save_audio(result["audio"])


def summary_tab(scenario, history):
    try:
        result = conversation_summary(scenario, history)
    except Exception as error:
        show_error(error)

    def bullet_list(items):
        return "\n".join(f"- {item}" for item in items)

    return f"""## How it went

### What went well
{bullet_list(result.get("went_well", []))}

### What to work on
{bullet_list(result.get("work_on", []))}

### Useful phrases from this conversation
{bullet_list(result.get("useful_phrases", []))}
"""


# Starts a fresh conversation (when the scenario changes or "Start over" is clicked)
def start_over():
    return [], [], None, "", "", None


# Gradio UI

with gr.Blocks(title="DesiUnmute") as ui:
    gr.Markdown("# **DesiUnmute - Hindi AI Tutor**")
    gr.Markdown(
        "Learn natural, everyday Hindi the way your family speaks it. "
        "**Translate** a sentence and hear it, **practice** saying it, "
        "then try a **conversation**."
    )

    with gr.Tabs() as tabs:

        # Translation Tutor
        with gr.Tab("Translate", id="translate"):
            input_text = gr.Textbox(label="English sentence", placeholder="e.g. Have you eaten?")
            gender = gr.Radio(["Male", "Female"], label="I am", value="Female")
            talking_to = gr.Radio(list(TALKING_TO.keys()), label="I'm talking to", value="A friend")
            pronunciation = gr.Radio(["Yes", "No"], label="Generate pronunciation audio?", value="Yes")

            translate_button = gr.Button("Translate", variant="primary")

            translate_output = gr.Markdown()
            translate_audio = gr.Audio(label="Listen", type="filepath")
            practice_button = gr.Button("Practice saying this phrase")

            # Remembers the last translation for the "Practice" button
            last_phrase = gr.State("")
            last_audio = gr.State(None)

        # Pronunciation Coach
        with gr.Tab("Pronunciation Coach", id="pronunciation"):
            target_phrase = gr.Textbox(
                label="Phrase to practice",
                placeholder="e.g. aap kaise ho (or use 'Practice saying this phrase' on the Translate tab)",
            )
            model_audio = gr.Audio(label="Listen first", type="filepath")
            user_audio = gr.Audio(sources=["microphone"], type="filepath", label="Record yourself")

            feedback_button = gr.Button("Get feedback", variant="primary")
            feedback_output = gr.Markdown()

        # Conversation Practice Mode
        with gr.Tab("Conversation Practice", id="conversation"):
            scenario = gr.Dropdown(list(SCENARIOS.keys()), value="Phone call with Nani", label="Scenario")

            chat = gr.Chatbot(label="Conversation", height=350)
            side_note = gr.Markdown()
            reply_audio = gr.Audio(label="Their reply", type="filepath", autoplay=True)

            audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Speak your reply")
            with gr.Row():
                send_button = gr.Button("Send", variant="primary")
                summary_button = gr.Button("End conversation")
                start_over_button = gr.Button("Start over")

            with gr.Accordion("How do I say...?", open=False):
                question = gr.Textbox(label="Type it in English", placeholder="e.g. I miss you")
                ask_button = gr.Button("Ask")
                answer = gr.Markdown()
                answer_audio = gr.Audio(label="Listen", type="filepath")

            summary_output = gr.Markdown()

            # Remembers the conversation so far (for the AI)
            history = gr.State([])

    # Button actions

    translate_button.click(
        translate_tab,
        inputs=[input_text, gender, talking_to, pronunciation],
        outputs=[translate_output, translate_audio, last_phrase, last_audio],
    )

    practice_button.click(
        practice_this_phrase,
        inputs=[last_phrase, last_audio],
        outputs=[target_phrase, model_audio, tabs],
    )

    feedback_button.click(
        pronunciation_tab,
        inputs=[user_audio, target_phrase],
        outputs=[feedback_output],
    )

    send_button.click(
        conversation_tab,
        inputs=[scenario, audio_input, history, chat],
        outputs=[chat, history, reply_audio, side_note, audio_input],
    )

    ask_button.click(
        how_do_i_say_tab,
        inputs=[question, scenario],
        outputs=[answer, answer_audio],
    )

    summary_button.click(
        summary_tab,
        inputs=[scenario, history],
        outputs=[summary_output],
    )

    start_over_outputs = [chat, history, reply_audio, side_note, summary_output, audio_input]
    start_over_button.click(start_over, outputs=start_over_outputs)
    scenario.change(start_over, outputs=start_over_outputs)


if __name__ == "__main__":
    # On Render, PORT is set for us. On my Mac it falls back to 7860.
    port = int(os.getenv("PORT", 7860))

    # Beta login: only people with the username and password can use the app.
    # If BETA_PASSWORD isn't set (like on my Mac), there's no login.
    beta_login = None
    if os.getenv("BETA_PASSWORD"):
        beta_login = (os.getenv("BETA_USERNAME", "beta"), os.getenv("BETA_PASSWORD"))

    ui.launch(server_name="0.0.0.0", server_port=port, auth=beta_login)
