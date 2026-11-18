# DesiUnmute

_Understand it already? Now speak it._

AI-powered Hindi learning for Indian heritage learners, built with Python, FastAPI and the OpenAI API. Learn natural, everyday Hindi the way your family speaks it, all in romanized Hindi.

## Features

- Translates English into natural, conversational Hindi (romanized), with a word breakdown, alternatives, and common mistakes
- Hindi audio for every translation
- Pronunciation coach: record yourself and get friendly feedback in simple English, including how natural your accent sounds (Microsoft Azure)
- Conversation practice with AI characters (like a phone call with Nani), with spoken replies and an end-of-conversation summary
- Respect levels: talking to a friend, an elder, or a child

The website has Translate, the Pronunciation Coach, Heritage Gaps (Units 1 and 2, drafts) and Conversation Practice.

## Tech Stack

- Python
- FastAPI (website), Jinja templates and HTMX (pages)
- OpenAI API (text, text-to-speech, and speech-to-text)
- Microsoft Azure Pronunciation Assessment (accent check, Hindi)
- jiwer (checking the words)
- pytest
- Gradio (the original beta app, kept for local testing)

## How It Works

User input → processed through the OpenAI API → translation, audio, and feedback displayed in the app

## Files

| File | What it does |
|---|---|
| `main.py` | The website: pages, the invite code, and what happens when you click a button. |
| `templates/` | The HTML for each page. `base.html` is the shared header and footer. |
| `templates/partials/` | Small pieces HTMX drops into a page (like a translation result). |
| `static/` | The styles (`style.css`), HTMX, the tab icon, and `desiunmute.js` (recording, conversations and the Slow button). |
| `config.py` | Shared settings: AI model names, limits, natural-Hindi rules, respect levels. |
| `audio.py` | Text-to-speech (Hindi voice) and speech-to-text. |
| `translate.py` | English → natural romanized Hindi, with breakdown and audio. |
| `pronunciation.py` | Scores your recording and gives coaching feedback. |
| `azure_speech.py` | Sends a recording to Azure to check the accent. |
| `lessons.py` | Heritage Gaps lessons (the reviewed content), plus the AI for family examples and the tutor. |
| `conversation.py` | Conversation characters, "How do I say...?", and the end summary. |
| `try_models.py` | Compares AI models side by side on the same Hindi task. |
| `app.py` | The original Gradio beta app (for local testing only). |
| `tests/` | Automatic checks that use a fake AI (free, no API key needed). |

## Run the website on your computer

```
pip install -r requirements-dev.txt
export OPENAI_API_KEY=your-key-here
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000. The beta invite code is set with `INVITE_CODE` (default: `namaste`).

## Settings on Render

Set these in Render → your service → Environment. Never put them in the code.

| Setting | What it is |
|---|---|
| `OPENAI_API_KEY` | A separate OpenAI key just for the live site |
| `INVITE_CODE` | The private code testers type to get in |
| `SECRET_KEY` | A long random string that protects logins |
| `AZURE_SPEECH_KEY` | KEY 1 from Azure (Keys and Endpoint). Turns on the accent check |
| `AZURE_SPEECH_REGION` | The region on that same page (`westus3`) |
| `DAILY_LIMIT_PER_PERSON` | Optional. OpenAI calls per tester per day (default 90) |
| `DAILY_LIMIT_TOTAL` | Optional. OpenAI calls for everyone per day (default 600) |
| `DAILY_LIMIT_VOICE` | Optional. Voice (text-to-speech) calls per day (default 250) |
| `DAILY_LIMIT_LISTEN` | Optional. Listening calls per day, OpenAI and Azure together (default 250) |

Limits count OpenAI calls (one click can make up to 3) and reset at midnight Pacific.
They're kept in memory, so they also reset when Render restarts. Keep OpenAI's
auto-recharge off as the backup. Every AI use is printed in Render's Logs.

Build command: `pip install -r requirements.txt`
Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Run the tests

```
pytest
```

## Original beta

https://huggingface.co/spaces/rhead1998/desilingo

## Coming soon

desiunmute.com
