import time
import lessons
from config import client

# Model comparison
# Runs "Make it about my family" with each model so we can compare the Hindi
# side by side. Run it with:  python try_models.py
# It costs a fraction of a cent.

MODELS_TO_TRY = ["gpt-4o-mini", "gpt-6-luna", "gpt-6.1-terra"]

FAMILY = "My nani was born in Dhariwal and moved to Hisar. My dada lives in Delhi."
GENDER = "Female"


# Newer models may not accept a "temperature" setting, so this
# removes it for them and keeps everything else the same
original_create = client.chat.completions.create

def create_without_temperature(**kwargs):
    if not lessons.TEXT_MODEL.startswith("gpt-4"):
        kwargs.pop("temperature", None)
    return original_create(**kwargs)

client.chat.completions.create = create_without_temperature


unit = lessons.get_unit(1)

for model in MODELS_TO_TRY:
    lessons.TEXT_MODEL = model
    print(f"\n===== {model} =====")

    start = time.time()
    try:
        examples = lessons.personalize_lesson(unit, FAMILY, GENDER)
    except Exception as error:
        print("Didn't work:", error)
        continue

    for example in examples:
        print("-", example["phrase"])
        print("   ", example["english"], "|", example.get("note", ""))

    print(f"({time.time() - start:.1f} seconds)")
