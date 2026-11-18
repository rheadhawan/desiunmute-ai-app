import os
import json
import base64
import tempfile
import secrets
import threading
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from config import TALKING_TO, MAX_TEXT_LENGTH, MAX_CONVERSATION_TURNS
from translate import desiunmute_translate
from pronunciation import pronunciation_feedback, feedback_heading, phrase_to_devanagari, saved_devanagari, PRACTICE_PHRASES
from audio import make_audio
from azure_speech import azure_is_set_up
from conversation import SCENARIOS, SCENARIO_INTROS, start_conversation, conversation_practice, how_do_i_say, conversation_summary
from lessons import UNITS, get_unit, check_answers, personalize_lesson, ask_tutor

# The DesiUnmute website
# This file only handles pages and buttons. All the AI work stays in
# translate.py, pronunciation.py and conversation.py, same as the Gradio app.

app = FastAPI()

# Sessions remember that a tester already typed the invite code.
# SECRET_KEY signs the cookie so nobody can fake it. Set a real one on Render.
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "dev-only-secret"))

# On Render, RENDER is set automatically. Refuse to start with the
# made-up local settings, so the live site never uses them by accident.
if os.getenv("RENDER") and (not os.getenv("SECRET_KEY") or not os.getenv("INVITE_CODE")):
    raise RuntimeError("Set SECRET_KEY and INVITE_CODE in Render's Environment settings.")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Beta testers need this code to get in (protects the OpenAI bill)
INVITE_CODE = os.getenv("INVITE_CODE", "namaste")


# Daily AI limits (protects the OpenAI bill during the beta)
# We count every call to OpenAI, not every click, because one click can make
# up to 3 calls (for example: listen to you + write a reply + speak it).
#   text   = gpt-6-luna (cheapest)
#   voice  = gpt-realtime-2.1-mini (most expensive, so it gets its own cap)
#   listen = gpt-4o-transcribe, or Azure for the Pronunciation Coach (also its own cap)
# Change any of these on Render (Environment) without touching the code.
DAILY_LIMIT_PER_PERSON = int(os.getenv("DAILY_LIMIT_PER_PERSON", "90"))   # all calls, one tester
DAILY_LIMIT_TOTAL = int(os.getenv("DAILY_LIMIT_TOTAL", "600"))            # all calls, everyone
DAILY_LIMIT_VOICE = int(os.getenv("DAILY_LIMIT_VOICE", "250"))            # voice calls, everyone
DAILY_LIMIT_LISTEN = int(os.getenv("DAILY_LIMIT_LISTEN", "250"))          # listening calls, everyone

# Today's counts. Kept in memory, so they also reset when Render restarts.
# (OpenAI's prepaid credit with auto-recharge off is the backup for that.)
ai_uses = {"date": None, "total": 0, "voice": 0, "listen": 0, "people": {}}

# The website answers several people at the same time (in "threads").
# The lock makes sure only one of them updates the counts at a time,
# so two clicks at the same moment can't both sneak past a limit.
ai_lock = threading.Lock()


# Today's date in California, so limits reset at midnight Pacific time
# (Render's own clock is in UTC, which would reset at 4 PM).
def today_pacific():
    return datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()


# Audio for lesson and ready-made phrases, made once and reused.
# They're the same for everyone, so this saves a lot of voice calls.
# {devanagari: audio bytes}, emptied when Render restarts.
saved_audio = {}


# Recordings bigger than this are refused. The browser stops at 15 seconds,
# which is well under this, so only made-up uploads get stopped here.
MAX_RECORDING_BYTES = 750 * 1024


# Helpers

def is_invited(request):
    return request.session.get("invited") is True


# Sends people without the invite code to the invite page.
# HTMX requests need a special header instead of a normal redirect.
def go_to_invite(request):
    if request.headers.get("HX-Request"):
        return HTMLResponse("", headers={"HX-Redirect": "/invite"})
    return RedirectResponse("/invite", status_code=303)


# Counts the OpenAI calls an action is about to make, or stops if that would
# go over a limit. Raises ValueError so the friendly-error code shows the message.
# Call it only after the learner's input has passed its checks, so mistakes
# like an empty box don't use up anyone's practice.
def count_ai_use(request, action, text=0, voice=0, listen=0):
    calls = text + voice + listen

    with ai_lock:
        # 1. A new day starts with fresh counts
        today = today_pacific()
        if ai_uses["date"] != today:
            ai_uses["date"] = today
            ai_uses["total"] = 0
            ai_uses["voice"] = 0
            ai_uses["listen"] = 0
            ai_uses["people"] = {}

        # 2. Check every limit before counting anything
        # (each tester gets an id when they enter the invite code)
        person = request.session.get("person", "unknown")
        used = ai_uses["people"].get(person, 0)

        if used + calls > DAILY_LIMIT_PER_PERSON:
            raise ValueError("You've practiced a lot today! The beta has a daily limit, so come back tomorrow.")

        if (
            ai_uses["total"] + calls > DAILY_LIMIT_TOTAL
            or ai_uses["voice"] + voice > DAILY_LIMIT_VOICE
            or ai_uses["listen"] + listen > DAILY_LIMIT_LISTEN
        ):
            raise ValueError("DesiUnmute has reached its daily beta limit. Please come back tomorrow!")

        # 3. Count it
        ai_uses["people"][person] = used + calls
        ai_uses["total"] += calls
        ai_uses["voice"] += voice
        ai_uses["listen"] += listen
        totals = f"total {ai_uses['total']}/{DAILY_LIMIT_TOTAL}, voice {ai_uses['voice']}/{DAILY_LIMIT_VOICE}, listen {ai_uses['listen']}/{DAILY_LIMIT_LISTEN}"

    # 4. Shows up in Render's Logs, so you can see how DesiUnmute is being used
    print(f"AI use: {action} | person {person[:6]} used {used + calls}/{DAILY_LIMIT_PER_PERSON} | today {totals}")


# Checks typed text before any AI is used (the AI files check again, that's fine)
def check_typed_text(text, empty_message):
    if not text or text.strip() == "":
        raise ValueError(empty_message)
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Please keep it under {MAX_TEXT_LENGTH} characters.")


# Shows a friendly message instead of a crash.
# ValueErrors are our own messages (like "Please record first"), so show them.
# Anything else is technical, so print it for us and keep it simple for learners.
def show_error(request, error):
    if isinstance(error, ValueError):
        message = str(error)
    else:
        print("ERROR:", repr(error))   # shows up in Terminal / the Render logs
        message = "Something went wrong talking to the AI. Please try again in a moment."
    return templates.TemplateResponse(request, "partials/error.html", {"message": message})


# Saves an uploaded recording to a temporary file and returns its path.
# The transcriber needs a real file. Callers delete it right after.
def save_recording(recording):
    if recording is None:
        raise ValueError("Please record yourself first.")

    audio_bytes = recording.file.read()

    if len(audio_bytes) == 0:
        raise ValueError("The recording was empty. Please try again.")

    if len(audio_bytes) > MAX_RECORDING_BYTES:
        raise ValueError("That recording is too long. Please keep it under 15 seconds.")

    # Chrome records .webm and Safari records .mp4. The file ending
    # tells OpenAI which kind it is, so keep the right one.
    content_type = recording.content_type or ""
    if "mp4" in content_type:
        suffix = ".mp4"
    elif "ogg" in content_type:
        suffix = ".ogg"
    elif "wav" in content_type:
        suffix = ".wav"
    else:
        suffix = ".webm"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_bytes)
        return f.name


# Turns audio bytes into something an <audio> tag can play directly,
# so we don't have to save files anywhere
def audio_to_data_url(audio_bytes):
    if audio_bytes is None:
        return None
    encoded = base64.b64encode(audio_bytes).decode()
    return f"data:audio/mpeg;base64,{encoded}"


# Browsers ask for /favicon.ico on their own, so point them to our icon
@app.get("/favicon.ico")
def favicon():
    return RedirectResponse("/static/favicon.svg")


# Invite page

@app.get("/invite")
def invite_page(request: Request):
    return templates.TemplateResponse(request, "invite.html", {"error": None})


@app.post("/invite")
def check_invite(request: Request, code: str = Form("")):
    if code.strip().lower() != INVITE_CODE.lower():
        return templates.TemplateResponse(
            request,
            "invite.html",
            {"error": "That code didn't work. Check the spelling and try again."},
        )

    request.session["invited"] = True
    request.session["person"] = secrets.token_hex(8)   # for the daily limits
    return RedirectResponse("/", status_code=303)


# Home page

@app.get("/")
def home_page(request: Request):
    if not is_invited(request):
        return go_to_invite(request)
    return templates.TemplateResponse(request, "home.html", {})


# Translate page

@app.get("/translate")
def translate_page(request: Request):
    if not is_invited(request):
        return go_to_invite(request)
    return templates.TemplateResponse(request, "translate.html", {"talking_to_options": TALKING_TO.keys()})


# Runs when the learner clicks "Translate". HTMX swaps the result into the page.
@app.post("/translate")
def translate_result(
    request: Request,
    text: str = Form(""),
    gender: str = Form("Female"),
    talking_to: str = Form("A friend"),
    audio: str = Form("No"),
):
    if not is_invited(request):
        return go_to_invite(request)

    # Don't let anyone send a respect level we don't have
    if talking_to not in TALKING_TO:
        talking_to = "A friend"

    try:
        check_typed_text(text, "Please type something in English to translate.")
        count_ai_use(request, "translate", text=1, voice=1 if audio == "Yes" else 0)
        result = desiunmute_translate(text, gender, talking_to, audio)
    except Exception as error:
        return show_error(request, error)

    return templates.TemplateResponse(
        request,
        "partials/translate_result.html",
        {"result": result, "audio_url": audio_to_data_url(result["audio"])},
    )


# Pronunciation Coach page
# "?phrase=..." fills in the phrase, so other pages can link here
# (like the "Practice saying this" link under a translation).

@app.get("/pronunciation")
def pronunciation_page(request: Request, phrase: str = ""):
    if not is_invited(request):
        return go_to_invite(request)
    return templates.TemplateResponse(
        request,
        "pronunciation.html",
        {"phrase": phrase, "practice_phrases": PRACTICE_PHRASES, "accent_check": azure_is_set_up()},
    )


# Plays the phrase out loud so the learner hears it before trying
@app.post("/pronunciation/hear")
def hear_phrase(request: Request, phrase: str = Form("")):
    if not is_invited(request):
        return go_to_invite(request)

    try:
        check_typed_text(phrase, "Type or pick a phrase first.")
        saved = saved_devanagari(phrase)

        if saved and saved in saved_audio:
            # Already made this one: no AI needed, nothing to count
            audio_bytes = saved_audio[saved]
        elif saved:
            # A lesson or ready-made phrase: make the audio once, then reuse it
            count_ai_use(request, "hear (saved phrase)", voice=1)
            audio_bytes = make_audio(saved)
            saved_audio[saved] = audio_bytes
        else:
            # A phrase the learner typed: write it in Devanagari, then speak it
            count_ai_use(request, "hear (typed phrase)", text=1, voice=1)
            devanagari = phrase_to_devanagari(phrase)
            audio_bytes = make_audio(devanagari)
    except Exception as error:
        return show_error(request, error)

    return templates.TemplateResponse(
        request,
        "partials/audio_player.html",
        {"audio_url": audio_to_data_url(audio_bytes)},
    )


# Runs when the learner clicks "Get feedback" after recording
@app.post("/pronunciation/feedback")
def pronunciation_result(
    request: Request,
    target_phrase: str = Form(""),
    recording: UploadFile | None = File(None),
):
    if not is_invited(request):
        return go_to_invite(request)

    if target_phrase.strip() == "":
        return show_error(request, ValueError("Please type the phrase in romanized Hindi."))

    # We never keep recordings: save for a moment, use it, delete it
    try:
        audio_path = save_recording(recording)
    except ValueError as error:
        return show_error(request, error)

    try:
        # Azure checks the accent too. It needs the phrase in Devanagari and a
        # WAV recording (the browser makes one; if that ever fails, we just
        # check the words with OpenAI like before).
        if azure_is_set_up() and audio_path.endswith(".wav"):
            saved = saved_devanagari(target_phrase)
            # romanize + coach, plus writing a typed phrase in Devanagari
            text_calls = 2 if saved else 3
            count_ai_use(request, "pronunciation feedback (Azure)", text=text_calls, listen=1)
            reference = saved or phrase_to_devanagari(target_phrase)
            result = pronunciation_feedback(audio_path, target_phrase, reference)
        else:
            count_ai_use(request, "pronunciation feedback", text=2, listen=1)
            result = pronunciation_feedback(audio_path, target_phrase)
    except Exception as error:
        return show_error(request, error)
    finally:
        os.remove(audio_path)

    return templates.TemplateResponse(
        request,
        "partials/pronunciation_result.html",
        {"result": result, "heading": feedback_heading(result)},
    )


# Heritage Gaps: list of units

@app.get("/lessons")
def lessons_page(request: Request):
    if not is_invited(request):
        return go_to_invite(request)
    return templates.TemplateResponse(request, "lessons.html", {"units": UNITS})


# One unit (lesson page)

@app.get("/lessons/{unit_id}")
def lesson_page(request: Request, unit_id: int):
    if not is_invited(request):
        return go_to_invite(request)

    unit = get_unit(unit_id)
    if unit is None:
        return RedirectResponse("/lessons", status_code=303)

    return templates.TemplateResponse(request, "lesson.html", {"unit": unit})


# "Do you know this?" check
# async because reading a form with any number of questions needs "await"
@app.post("/lessons/{unit_id}/check")
async def lesson_check(request: Request, unit_id: int):
    if not is_invited(request):
        return go_to_invite(request)

    unit = get_unit(unit_id)
    if unit is None:
        return show_error(request, ValueError("That lesson isn't ready yet."))

    answers = await request.form()
    results, knows_it = check_answers(unit, answers)

    return templates.TemplateResponse(
        request,
        "partials/check_result.html",
        {"unit": unit, "results": results, "knows_it": knows_it},
    )


# "Make it about my family"
@app.post("/lessons/{unit_id}/family")
def lesson_family(request: Request, unit_id: int, family: str = Form(""), gender: str = Form("Female")):
    if not is_invited(request):
        return go_to_invite(request)

    unit = get_unit(unit_id)
    if unit is None:
        return show_error(request, ValueError("That lesson isn't ready yet."))

    try:
        check_typed_text(family, "Tell us a little about your family first (for example: my Nani lives in Jaipur).")
        count_ai_use(request, "family examples", text=1)
        examples = personalize_lesson(unit, family, gender)
    except Exception as error:
        return show_error(request, error)

    return templates.TemplateResponse(request, "partials/family_examples.html", {"examples": examples})


# "Ask the tutor"
@app.post("/lessons/{unit_id}/ask")
def lesson_ask(request: Request, unit_id: int, question: str = Form("")):
    if not is_invited(request):
        return go_to_invite(request)

    unit = get_unit(unit_id)
    if unit is None:
        return show_error(request, ValueError("That lesson isn't ready yet."))

    try:
        check_typed_text(question, "Type a question first.")
        count_ai_use(request, "ask the tutor", text=1)
        answer = ask_tutor(unit, question)
    except Exception as error:
        return show_error(request, error)

    return templates.TemplateResponse(
        request,
        "partials/tutor_answer.html",
        {"question": question, "answer": answer},
    )


# Conversation Practice

# Web addresses for each conversation: "Phone call with Nani" -> "phone-call-with-nani"
SCENARIO_SLUGS = {name.lower().replace(" ", "-"): name for name in SCENARIOS}


# The conversation so far lives in the learner's browser and comes back
# with every request. This checks it's in the shape the AI expects.
def read_history(history_text):
    try:
        history = json.loads(history_text or "[]")
    except json.JSONDecodeError:
        raise ValueError("Something went wrong with this conversation. Please start over.")

    # The longest real conversation: the opening line + 20 replies each way
    if not isinstance(history, list) or len(history) > MAX_CONVERSATION_TURNS * 2 + 1:
        raise ValueError("Something went wrong with this conversation. Please start over.")

    for message in history:
        if (
            not isinstance(message, dict)
            or message.get("role") not in ("user", "assistant")
            or not isinstance(message.get("content"), str)
            or len(message["content"]) > 1000
        ):
            raise ValueError("Something went wrong with this conversation. Please start over.")

    return history


# Conversation turns are sent back as JSON: the new chat bubbles (HTML)
# plus the updated history for the browser to keep.
def chat_response(template_name, context, history=None):
    html = templates.get_template(template_name).render(context)
    return JSONResponse({"html": html, "history": history})


def chat_error(error):
    if isinstance(error, ValueError):
        message = str(error)
    else:
        print("ERROR:", repr(error))
        message = "Something went wrong talking to the AI. Please try again in a moment."
    return chat_response("partials/error.html", {"message": message})


# List of conversations
@app.get("/conversation")
def conversation_list_page(request: Request):
    if not is_invited(request):
        return go_to_invite(request)

    scenarios = [
        {"name": name, "slug": slug, "intro": SCENARIO_INTROS[name]}
        for slug, name in SCENARIO_SLUGS.items()
    ]
    return templates.TemplateResponse(request, "conversation_list.html", {"scenarios": scenarios})


# One conversation
@app.get("/conversation/{slug}")
def conversation_page(request: Request, slug: str):
    if not is_invited(request):
        return go_to_invite(request)

    if slug not in SCENARIO_SLUGS:
        return RedirectResponse("/conversation", status_code=303)

    name = SCENARIO_SLUGS[slug]
    return templates.TemplateResponse(
        request,
        "conversation.html",
        {"name": name, "slug": slug, "intro": SCENARIO_INTROS[name]},
    )


# The character speaks first
@app.post("/conversation/{slug}/start")
def conversation_start(request: Request, slug: str):
    if not is_invited(request):
        return go_to_invite(request)

    if slug not in SCENARIO_SLUGS:
        return chat_error(ValueError("Please pick a conversation."))

    try:
        count_ai_use(request, "conversation start", text=1, voice=1)
        reply, history = start_conversation(SCENARIO_SLUGS[slug])
    except Exception as error:
        return chat_error(error)

    return chat_response(
        "partials/chat_turn.html",
        {"reply": reply, "audio_url": audio_to_data_url(reply["audio"])},
        history,
    )


# The learner answers out loud, the character replies
@app.post("/conversation/{slug}/reply")
def conversation_reply(
    request: Request,
    slug: str,
    history: str = Form("[]"),
    recording: UploadFile | None = File(None),
):
    if not is_invited(request):
        return go_to_invite(request)

    if slug not in SCENARIO_SLUGS:
        return chat_error(ValueError("Please pick a conversation."))

    try:
        past_history = read_history(history)
        if len(past_history) >= MAX_CONVERSATION_TURNS * 2:
            raise ValueError("This conversation is getting long! Start a new one to keep practicing.")
        audio_path = save_recording(recording)
    except ValueError as error:
        return chat_error(error)

    try:
        count_ai_use(request, "conversation reply", text=1, voice=1, listen=1)
        reply, new_history = conversation_practice(SCENARIO_SLUGS[slug], audio_path, past_history)
    except Exception as error:
        return chat_error(error)
    finally:
        os.remove(audio_path)

    return chat_response(
        "partials/chat_turn.html",
        {"reply": reply, "audio_url": audio_to_data_url(reply["audio"])},
        new_history,
    )


# "How do I say...?" (HTMX)
@app.post("/conversation/{slug}/say")
def conversation_say(request: Request, slug: str, question: str = Form("")):
    if not is_invited(request):
        return go_to_invite(request)

    if slug not in SCENARIO_SLUGS:
        return show_error(request, ValueError("Please pick a conversation."))

    try:
        check_typed_text(question, "Type what you want to say in English.")
        count_ai_use(request, "how do I say", text=1, voice=1)
        result = how_do_i_say(question, SCENARIO_SLUGS[slug])
    except Exception as error:
        return show_error(request, error)

    return templates.TemplateResponse(
        request,
        "partials/say_it.html",
        {"result": result, "audio_url": audio_to_data_url(result["audio"])},
    )


# End of conversation summary
@app.post("/conversation/{slug}/summary")
def conversation_end(request: Request, slug: str, history: str = Form("[]")):
    if not is_invited(request):
        return go_to_invite(request)

    try:
        past_history = read_history(history)
        # Only count conversations where the learner actually said something
        if not any(message["role"] == "user" for message in past_history):
            raise ValueError("Say something first! Then you'll get a summary.")
        count_ai_use(request, "conversation summary", text=1)
        summary = conversation_summary(SCENARIO_SLUGS.get(slug, ""), past_history)
    except Exception as error:
        return show_error(request, error)

    return templates.TemplateResponse(request, "partials/conversation_summary.html", {"summary": summary})
