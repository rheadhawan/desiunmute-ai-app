---
title: DesiUnmute
emoji: 🌍
colorFrom: indigo
colorTo: red
sdk: gradio
sdk_version: 6.11.0
python_version: "3.10"
app_file: app.py
pinned: false
---

# DesiUnmute — Hindi AI Tutor (beta v2)

_Understand it already? Now speak it._

Learn natural, everyday Hindi the way your family speaks it.

## Files

| File | What it does |
|---|---|
| `app.py` | The Gradio website (tabs, buttons, layout). Only screen code lives here. |
| `config.py` | Shared settings: AI model names, limits, natural-Hindi rules, respect levels. |
| `audio.py` | Text-to-speech (Hindi voice) and speech-to-text. |
| `translate.py` | English → natural romanized Hindi, with breakdown and audio. |
| `pronunciation.py` | Scores your recording and gives coaching feedback. |
| `conversation.py` | Conversation characters, "How do I say...?", and the end summary. |
| `tests/` | Automatic checks that use a fake AI (free, no API key needed). |

## Run it on your computer

```
pip install gradio==6.11.0 -r requirements.txt
export OPENAI_API_KEY=your-key-here
python app.py
```

## Run the tests

```
pip install pytest
pytest
```

## When OpenAI retires a model

Change the model name in `config.py`. Nothing else needs to change.
