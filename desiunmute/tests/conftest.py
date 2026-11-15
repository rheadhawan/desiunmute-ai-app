import os

# Tests never call OpenAI, but the client needs a key to start
os.environ.setdefault("OPENAI_API_KEY", "test-key")
