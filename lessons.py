import json
from config import client, TEXT_MODEL, NATURAL_HINDI_RULES, MAX_TEXT_LENGTH

# Heritage Gaps lessons
# The things heritage speakers usually miss. Full plan:
# claude/heritage-gaps-curriculum.md in the project.
#
# The lesson content below is the "textbook": fixed, and checked by a native
# speaker before real learners see it. The AI only does the teaching around it
# (examples about your own family, and answering questions).
#
# DRAFT: everything here still needs native-speaker review.
# The Devanagari is only for the voice. Learners never see it.

UNITS = [
    {
        "id": 1,
        "title": "Talking to elders the right way",
        "summary": "aap vs tum, respectful verbs, ji, polite requests, and blessings.",
        "available": True,
        "check": [
            {
                "question": "You're greeting your Nani. Which fits best?",
                "options": ["tum kaisi ho?", "aap kaisi hain?", "tu kaisi hai?"],
                "answer": "aap kaisi hain?",
                "why": "Elders get aap, plus the respectful verb hain. And because Nani is a woman, it's kaisi, not kaise.",
            },
            {
                "question": "Dadi ji aa rahi ___ (Dadi is coming)",
                "options": ["hai", "hain"],
                "answer": "hain",
                "why": "For elders, Hindi uses the plural verb as a sign of respect, even for one person.",
            },
            {
                "question": "Your Mama ji asks if you've eaten. The most respectful yes is:",
                "options": ["haan", "haan ji", "yes"],
                "answer": "haan ji",
                "why": "Adding ji to haan makes it polite. Plain haan can sound too casual with elders.",
            },
            {
                "question": "You touch your Dada's feet and he says \"jeete raho!\" What does it mean?",
                "options": ["Live long (a blessing)", "Keep walking", "Go and play"],
                "answer": "Live long (a blessing)",
                "why": "It's a blessing, literally \"keep living\". You don't need to say anything back. A smile is enough.",
            },
        ],
        "sections": [
            {
                "heading": "tu, tum or aap?",
                "text": [
                    "Hindi has three ways to say \"you\". Many heritage speakers use tum with everyone, because that's how their parents talked to them. But with elders it can sound a little rude.",
                    "aap: elders, parents' friends, anyone you want to respect. tum: friends, cousins your age, younger family. tu: very close friends or little kids. Never elders.",
                ],
                "examples": [
                    {"phrase": "Dadi ji, aap kaisi hain?", "english": "Dadi, how are you?", "devanagari": "दादी जी, आप कैसी हैं?"},
                    {"phrase": "Dada ji, aap kaise hain?", "english": "Dada, how are you?", "devanagari": "दादा जी, आप कैसे हैं?"},
                    {"phrase": "tum kaise ho?", "english": "How are you? (to a cousin or friend)", "devanagari": "तुम कैसे हो?"},
                ],
            },
            {
                "heading": "Respectful verbs",
                "text": [
                    "When you talk about an elder, the verb becomes plural, even though it's one person. This is what makes Hindi sound respectful.",
                ],
                "examples": [
                    {"phrase": "Dadi ji aa rahi hain", "english": "Dadi is coming", "devanagari": "दादी जी आ रही हैं"},
                    {"phrase": "Papa kahan gaye?", "english": "Where did Papa go?", "devanagari": "पापा कहाँ गए?"},
                    {"phrase": "Nana ji so rahe hain", "english": "Nana is sleeping", "devanagari": "नाना जी सो रहे हैं"},
                ],
            },
            {
                "heading": "ji makes everything polite",
                "text": [
                    "Add ji after names, relations and short answers. It's the easiest way to sound respectful.",
                ],
                "examples": [
                    {"phrase": "haan ji", "english": "Yes (polite)", "devanagari": "हाँ जी"},
                    {"phrase": "nahi ji, shukriya", "english": "No, thank you (polite)", "devanagari": "नहीं जी, शुक्रिया"},
                    {"phrase": "accha ji", "english": "Okay (polite)", "devanagari": "अच्छा जी"},
                ],
            },
            {
                "heading": "Asking politely",
                "text": [
                    "With elders, requests end in -iye or use a soft question. This is how people really ask, not textbook Hindi.",
                ],
                "examples": [
                    {"phrase": "ek minute rukiye", "english": "Please wait a minute", "devanagari": "एक मिनट रुकिए"},
                    {"phrase": "aap bata denge?", "english": "Could you tell me?", "devanagari": "आप बता देंगे?"},
                    {"phrase": "thoda dheere boliye", "english": "Please speak a little slower", "devanagari": "थोड़ा धीरे बोलिए"},
                ],
            },
            {
                "heading": "Greetings and blessings",
                "text": [
                    "Many families touch elders' feet (pair chhoona) as a greeting. Elders answer with a blessing. You don't have to reply. A smile or a quiet \"ji\" is perfect.",
                ],
                "examples": [
                    {"phrase": "pranaam Nana ji", "english": "Respectful greeting to Nana", "devanagari": "प्रणाम नाना जी"},
                    {"phrase": "khush raho, beta", "english": "Be happy, my child (a blessing you'll hear)", "devanagari": "खुश रहो, बेटा"},
                    {"phrase": "jeete raho", "english": "Live long (a blessing you'll hear)", "devanagari": "जीते रहो"},
                ],
            },
        ],
    },
    {
        "id": 2,
        "title": "The family map",
        "summary": "Exactly who's who: chacha, mama, mausi, bua and more.",
        "available": True,
        "check": [
            {
                "question": "Your mom's brother is your:",
                "options": ["chacha", "mama", "mausa"],
                "answer": "mama",
                "why": "Mom's side: mama is her brother, mausi is her sister.",
            },
            {
                "question": "Your dad's sister is your:",
                "options": ["bua", "mausi", "chachi"],
                "answer": "bua",
                "why": "Dad's sister is bua. Mausi is mom's sister. Chachi is your chacha's wife.",
            },
            {
                "question": "Your dad's older brother is your:",
                "options": ["chacha", "tau ji", "mama"],
                "answer": "tau ji",
                "why": "Dad's older brother is tau ji. His younger brother is chacha.",
            },
            {
                "question": "What do you usually call an older girl cousin?",
                "options": ["Her first name", "didi", "bhabhi"],
                "answer": "didi",
                "why": "Older cousins are didi and bhaiya, just like older siblings. Bhabhi is your brother's wife.",
            },
        ],
        "sections": [
            {
                "heading": "Dad's side",
                "text": [
                    "English just says \"uncle\" and \"aunt\". Hindi tells you exactly which side and which relationship.",
                    "Families vary (Punjabi families might say chacha ji, phuphi or bhua). Use whatever your family uses.",
                ],
                "examples": [
                    {"phrase": "dada, dadi", "english": "Dad's father, dad's mother", "devanagari": "दादा, दादी"},
                    {"phrase": "chacha, chachi", "english": "Dad's younger brother, and his wife", "devanagari": "चाचा, चाची"},
                    {"phrase": "tau ji, tai ji", "english": "Dad's older brother, and his wife", "devanagari": "ताऊ जी, ताई जी"},
                    {"phrase": "bua, phupha ji", "english": "Dad's sister, and her husband", "devanagari": "बुआ, फूफा जी"},
                ],
            },
            {
                "heading": "Mom's side",
                "text": [
                    "A quick trick: mom's side starts with \"n\" or \"m\" (nana, nani, mama, mausi).",
                ],
                "examples": [
                    {"phrase": "nana, nani", "english": "Mom's father, mom's mother", "devanagari": "नाना, नानी"},
                    {"phrase": "mama, mami", "english": "Mom's brother, and his wife", "devanagari": "मामा, मामी"},
                    {"phrase": "mausi, mausa ji", "english": "Mom's sister, and her husband", "devanagari": "मौसी, मौसा जी"},
                ],
            },
            {
                "heading": "Siblings, cousins and in-laws",
                "text": [
                    "Older cousins are called bhaiya and didi, the same as older brothers and sisters.",
                    "You'll also hear: devar (husband's younger brother), jeth (husband's older brother), nanad (husband's sister), saas and sasur (mother- and father-in-law).",
                ],
                "examples": [
                    {"phrase": "bhaiya, didi", "english": "Older brother, older sister (and older cousins)", "devanagari": "भैया, दीदी"},
                    {"phrase": "bhabhi", "english": "Your brother's wife", "devanagari": "भाभी"},
                    {"phrase": "jija ji", "english": "Your sister's husband", "devanagari": "जीजा जी"},
                ],
            },
            {
                "heading": "Call elders by relation, not name",
                "text": [
                    "You'd never call your Mama by his first name. Use the relation, often with ji. When you talk about them, the verb is respectful too.",
                ],
                "examples": [
                    {"phrase": "ye meri mausi hain", "english": "This is my mausi", "devanagari": "ये मेरी मौसी हैं"},
                    {"phrase": "mere chacha Delhi mein rehte hain", "english": "My chacha lives in Delhi", "devanagari": "मेरे चाचा दिल्ली में रहते हैं"},
                    {"phrase": "Mama ji, aap kab aayenge?", "english": "Mama ji, when will you come?", "devanagari": "मामा जी, आप कब आएँगे?"},
                ],
            },
        ],
    },
    # Coming soon (content is planned in the curriculum doc)
    {"id": 3, "title": "Numbers past 20 and telling time", "summary": "sava, saadhe, paune, dedh, dhaai and the tricky numbers.", "available": False},
    {"id": 4, "title": "Grammar that sounds \"off\" when wrong", "summary": "Noun gender, \"maine\", and the little verbs that make Hindi natural.", "available": False},
    {"id": 5, "title": "Sounds English doesn't have", "summary": "Soft vs hard t and d, breathy sounds, long vowels.", "available": False},
    {"id": 6, "title": "Sounding natural", "summary": "When Hinglish sounds right, and when it sounds like an outsider.", "available": False},
    {"id": 7, "title": "Idioms and sayings", "summary": "The muhavare your elders use all the time.", "available": False},
    {"id": 8, "title": "Culture in conversation", "summary": "Why \"khana khaya?\" means \"I care\", festivals, and phone calls.", "available": False},
    {"id": 9, "title": "Listening to real fast speech", "summary": "How Hindi actually sounds at family speed.", "available": False},
]


# Finds a unit by its number (or None if it doesn't exist or isn't ready)

def get_unit(unit_id):
    for unit in UNITS:
        if unit["id"] == unit_id and unit["available"]:
            return unit
    return None


# Every example phrase in the lessons, so the voice can find its Devanagari

def all_lesson_phrases():
    phrases = []
    for unit in UNITS:
        for section in unit.get("sections", []):
            phrases.extend(section["examples"])
    return phrases


# The main points of a unit, written out for the AI prompts

def unit_key_points(unit):
    lines = []
    for section in unit["sections"]:
        examples = ", ".join(example["phrase"] for example in section["examples"])
        lines.append(f"- {section['heading']}: {examples}")
    return "\n".join(lines)


# "Do you know this?" check
# Returns which answers were right, without any score.

def check_answers(unit, answers):
    results = []
    for number, item in enumerate(unit["check"]):
        picked = answers.get(f"q{number}", "")
        results.append({
            "question": item["question"],
            "picked": picked,
            "answer": item["answer"],
            "right": picked == item["answer"],
            "why": item["why"],
        })

    knows_it = all(result["right"] for result in results)
    return results, knows_it


# "Make it about my family"
# The AI writes new examples for this unit using the learner's own relatives.

def personalize_lesson(unit, family, gender="Female"):
    if not family or family.strip() == "":
        raise ValueError("Tell us a little about your family first (for example: my Nani lives in Jaipur).")

    if len(family) > MAX_TEXT_LENGTH:
        raise ValueError(f"Please keep it under {MAX_TEXT_LENGTH} characters.")

    prompt = f"""
You are a warm Hindi tutor for Indian heritage learners who understand some
Hindi but can't read Devanagari.

The learner is studying this lesson: "{unit["title"]}"
Key points of the lesson:
{unit_key_points(unit)}

Write 4 short example sentences that use these key points, about the
learner's own family (described by the learner in the next message).

Rules:
{NATURAL_HINDI_RULES}
- The learner is {gender.lower()}. Use the correct verb endings when the learner talks about themself.
- Verbs and adjectives must match the gender of the person being talked to or
  about: Nani, Dadi, Mausi, Bua are women (kaisi, rahi, gayi); Nana, Dada,
  Mama, Chacha are men (kaise, rahe, gaye). Check every sentence for this.
- Use the respectful plural forms from the lesson for elders, also in the
  past tense: hain, the (men), thin (women). "Nani ji Jaipur mein rehti thin",
  "Dada ji Delhi gaye the".
- The note must be true for the sentence. Only say "respectful verbs" if the
  sentence actually uses them.
- Use the family details exactly as given. Don't invent new relatives.
- Notes are one short sentence in simple English.

Reply ONLY with JSON in this exact format:
{{
  "examples": [
    {{"phrase": "sentence in romanized Hindi", "english": "English meaning", "note": "which lesson point it shows"}}
  ]
}}
"""

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": family},
        ],
    )

    return json.loads(response.choices[0].message.content)["examples"]


# "Ask the tutor"
# Answers the learner's question about this lesson in simple English.

def ask_tutor(unit, question):
    if not question or question.strip() == "":
        raise ValueError("Type a question first.")

    if len(question) > MAX_TEXT_LENGTH:
        raise ValueError(f"Please keep your question under {MAX_TEXT_LENGTH} characters.")

    prompt = f"""
You are a warm, patient Hindi tutor for Indian heritage learners who
understand some Hindi but can't read Devanagari.

The learner is studying this lesson: "{unit["title"]}"
Key points of the lesson:
{unit_key_points(unit)}

Answer the learner's question (in the next message).

Rules:
- Answer in simple English, in 2-5 short sentences.
- Write any Hindi in romanized Hindi, never Devanagari.
- Give one short example when it helps.
- Families and regions say things differently. Treat all of them as valid.
- If the question has nothing to do with Hindi or Indian family life,
  kindly steer back to the lesson.
{NATURAL_HINDI_RULES}

Reply ONLY with JSON: {{"answer": "..."}}
"""

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
    )

    return json.loads(response.choices[0].message.content)["answer"]
