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

# Every number from 1 to 100, for the tap-to-hear chart in Unit 3.
# Spellings vary between families and regions (sattaaees / sattais);
# these are common ones. DRAFT: check with a native speaker.
NUMBERS = [
    {"phrase": "ek", "english": "1", "devanagari": "एक"},
    {"phrase": "do", "english": "2", "devanagari": "दो"},
    {"phrase": "teen", "english": "3", "devanagari": "तीन"},
    {"phrase": "chaar", "english": "4", "devanagari": "चार"},
    {"phrase": "paanch", "english": "5", "devanagari": "पाँच"},
    {"phrase": "chhah", "english": "6", "devanagari": "छह"},
    {"phrase": "saat", "english": "7", "devanagari": "सात"},
    {"phrase": "aath", "english": "8", "devanagari": "आठ"},
    {"phrase": "nau", "english": "9", "devanagari": "नौ"},
    {"phrase": "das", "english": "10", "devanagari": "दस"},
    {"phrase": "gyaarah", "english": "11", "devanagari": "ग्यारह"},
    {"phrase": "baarah", "english": "12", "devanagari": "बारह"},
    {"phrase": "terah", "english": "13", "devanagari": "तेरह"},
    {"phrase": "chaudah", "english": "14", "devanagari": "चौदह"},
    {"phrase": "pandrah", "english": "15", "devanagari": "पंद्रह"},
    {"phrase": "solah", "english": "16", "devanagari": "सोलह"},
    {"phrase": "satrah", "english": "17", "devanagari": "सत्रह"},
    {"phrase": "athaarah", "english": "18", "devanagari": "अठारह"},
    {"phrase": "unnees", "english": "19", "devanagari": "उन्नीस"},
    {"phrase": "bees", "english": "20", "devanagari": "बीस"},
    {"phrase": "ikkees", "english": "21", "devanagari": "इक्कीस"},
    {"phrase": "baaees", "english": "22", "devanagari": "बाईस"},
    {"phrase": "teees", "english": "23", "devanagari": "तेईस"},
    {"phrase": "chaubees", "english": "24", "devanagari": "चौबीस"},
    {"phrase": "pachchees", "english": "25", "devanagari": "पच्चीस"},
    {"phrase": "chhabbees", "english": "26", "devanagari": "छब्बीस"},
    {"phrase": "sattaaees", "english": "27", "devanagari": "सत्ताईस"},
    {"phrase": "atthaaees", "english": "28", "devanagari": "अट्ठाईस"},
    {"phrase": "unatees", "english": "29", "devanagari": "उनतीस"},
    {"phrase": "tees", "english": "30", "devanagari": "तीस"},
    {"phrase": "ikattees", "english": "31", "devanagari": "इकतीस"},
    {"phrase": "battees", "english": "32", "devanagari": "बत्तीस"},
    {"phrase": "taintees", "english": "33", "devanagari": "तैंतीस"},
    {"phrase": "chauntees", "english": "34", "devanagari": "चौंतीस"},
    {"phrase": "paintees", "english": "35", "devanagari": "पैंतीस"},
    {"phrase": "chhattees", "english": "36", "devanagari": "छत्तीस"},
    {"phrase": "saintees", "english": "37", "devanagari": "सैंतीस"},
    {"phrase": "adtees", "english": "38", "devanagari": "अड़तीस"},
    {"phrase": "untaalees", "english": "39", "devanagari": "उनतालीस"},
    {"phrase": "chaalees", "english": "40", "devanagari": "चालीस"},
    {"phrase": "iktaalees", "english": "41", "devanagari": "इकतालीस"},
    {"phrase": "bayaalees", "english": "42", "devanagari": "बयालीस"},
    {"phrase": "taintaalees", "english": "43", "devanagari": "तैंतालीस"},
    {"phrase": "chauvaalees", "english": "44", "devanagari": "चवालीस"},
    {"phrase": "paintaalees", "english": "45", "devanagari": "पैंतालीस"},
    {"phrase": "chhiyaalees", "english": "46", "devanagari": "छियालीस"},
    {"phrase": "saintaalees", "english": "47", "devanagari": "सैंतालीस"},
    {"phrase": "adtaalees", "english": "48", "devanagari": "अड़तालीस"},
    {"phrase": "unchaas", "english": "49", "devanagari": "उनचास"},
    {"phrase": "pachaas", "english": "50", "devanagari": "पचास"},
    {"phrase": "ikyaavan", "english": "51", "devanagari": "इक्यावन"},
    {"phrase": "baavan", "english": "52", "devanagari": "बावन"},
    {"phrase": "tirpan", "english": "53", "devanagari": "तिरपन"},
    {"phrase": "chauvan", "english": "54", "devanagari": "चौवन"},
    {"phrase": "pachpan", "english": "55", "devanagari": "पचपन"},
    {"phrase": "chhappan", "english": "56", "devanagari": "छप्पन"},
    {"phrase": "sattaavan", "english": "57", "devanagari": "सत्तावन"},
    {"phrase": "atthaavan", "english": "58", "devanagari": "अट्ठावन"},
    {"phrase": "unsath", "english": "59", "devanagari": "उनसठ"},
    {"phrase": "saath", "english": "60", "devanagari": "साठ"},
    {"phrase": "iksath", "english": "61", "devanagari": "इकसठ"},
    {"phrase": "baasath", "english": "62", "devanagari": "बासठ"},
    {"phrase": "tirsath", "english": "63", "devanagari": "तिरसठ"},
    {"phrase": "chaunsath", "english": "64", "devanagari": "चौंसठ"},
    {"phrase": "painsath", "english": "65", "devanagari": "पैंसठ"},
    {"phrase": "chhiyaasath", "english": "66", "devanagari": "छियासठ"},
    {"phrase": "sadsath", "english": "67", "devanagari": "सड़सठ"},
    {"phrase": "adsath", "english": "68", "devanagari": "अड़सठ"},
    {"phrase": "unhattar", "english": "69", "devanagari": "उनहत्तर"},
    {"phrase": "sattar", "english": "70", "devanagari": "सत्तर"},
    {"phrase": "ikhattar", "english": "71", "devanagari": "इकहत्तर"},
    {"phrase": "bahattar", "english": "72", "devanagari": "बहत्तर"},
    {"phrase": "tihattar", "english": "73", "devanagari": "तिहत्तर"},
    {"phrase": "chauhattar", "english": "74", "devanagari": "चौहत्तर"},
    {"phrase": "pachhattar", "english": "75", "devanagari": "पचहत्तर"},
    {"phrase": "chhihattar", "english": "76", "devanagari": "छिहत्तर"},
    {"phrase": "satattar", "english": "77", "devanagari": "सतहत्तर"},
    {"phrase": "athattar", "english": "78", "devanagari": "अठहत्तर"},
    {"phrase": "unaasi", "english": "79", "devanagari": "उनासी"},
    {"phrase": "assi", "english": "80", "devanagari": "अस्सी"},
    {"phrase": "ikyaasi", "english": "81", "devanagari": "इक्यासी"},
    {"phrase": "bayaasi", "english": "82", "devanagari": "बयासी"},
    {"phrase": "tiraasi", "english": "83", "devanagari": "तिरासी"},
    {"phrase": "chauraasi", "english": "84", "devanagari": "चौरासी"},
    {"phrase": "pachaasi", "english": "85", "devanagari": "पचासी"},
    {"phrase": "chhiyaasi", "english": "86", "devanagari": "छियासी"},
    {"phrase": "sattaasi", "english": "87", "devanagari": "सत्तासी"},
    {"phrase": "atthaasi", "english": "88", "devanagari": "अट्ठासी"},
    {"phrase": "navaasi", "english": "89", "devanagari": "नवासी"},
    {"phrase": "nabbe", "english": "90", "devanagari": "नब्बे"},
    {"phrase": "ikyaanve", "english": "91", "devanagari": "इक्यानवे"},
    {"phrase": "baanve", "english": "92", "devanagari": "बानवे"},
    {"phrase": "tiraanve", "english": "93", "devanagari": "तिरानवे"},
    {"phrase": "chauraanve", "english": "94", "devanagari": "चौरानवे"},
    {"phrase": "pachaanve", "english": "95", "devanagari": "पचानवे"},
    {"phrase": "chhiyaanve", "english": "96", "devanagari": "छियानवे"},
    {"phrase": "sattaanve", "english": "97", "devanagari": "सत्तानवे"},
    {"phrase": "atthaanve", "english": "98", "devanagari": "अट्ठानवे"},
    {"phrase": "ninyaanve", "english": "99", "devanagari": "निन्यानवे"},
    {"phrase": "sau", "english": "100", "devanagari": "सौ"},
]


UNITS = [
    {
        "id": 1,
        "title": "Talking to elders the right way",
        "summary": "aap vs tum, respectful verbs, ji, polite requests, and blessings.",
        "available": True,
        "tutor_hint": "\"Do I use aap with my older cousin?\"",
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
        "tutor_hint": "\"What do I call my mausi's husband?\"",
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
    {
        "id": 3,
        "title": "Numbers past 20 and telling time",
        "summary": "sava, saadhe, paune, dedh, dhaai and the tricky numbers.",
        "available": True,
        "tutor_hint": "\"Is it saadhe ek or dedh?\"",
        "number_chart": True,   # shows NUMBERS as a tap-to-hear chart
        "check": [
            {
                "question": "\"saadhe teen baje\" means:",
                "options": ["3:15", "3:30", "2:45"],
                "answer": "3:30",
                "why": "saadhe means \"and a half\", so saadhe teen is three and a half: 3:30.",
            },
            {
                "question": "\"paune paanch baje\" means:",
                "options": ["4:45", "5:15", "5:45"],
                "answer": "4:45",
                "why": "paune means \"a quarter less than\", so paune paanch is a quarter to five: 4:45.",
            },
            {
                "question": "Something costs \"dedh sau rupaye\". That's:",
                "options": ["105 rupees", "150 rupees", "1,500 rupees"],
                "answer": "150 rupees",
                "why": "dedh is one and a half, and sau is a hundred: one and a half hundred, 150.",
            },
            {
                "question": "\"pachhattar\" is:",
                "options": ["57", "70", "75"],
                "answer": "75",
                "why": "pachhattar is 75. Numbers past 20 each have their own name, so they're worth learning one by one.",
            },
        ],
        "sections": [
            {
                "heading": "Why Hindi numbers are tricky",
                "text": [
                    "In English, 21 to 99 follow a pattern (twenty-one, twenty-two). In Hindi, almost every number has its own name, so most heritage speakers switch to English for numbers.",
                    "Start with the ones you'll hear most: ages, prices and years. Mixing in English numbers (\"meeting five baje hai\") is completely normal too.",
                ],
                "examples": [
                    {"phrase": "ikkees", "english": "21", "devanagari": "इक्कीस"},
                    {"phrase": "pachaas", "english": "50", "devanagari": "पचास"},
                    {"phrase": "pachhattar", "english": "75", "devanagari": "पचहत्तर"},
                    {"phrase": "ninyaanve", "english": "99", "devanagari": "निन्यानवे"},
                ],
            },
            {
                "heading": "sava, saadhe and paune",
                "text": [
                    "Hindi tells time in quarters. sava means \"and a quarter\", saadhe means \"and a half\", and paune means \"a quarter less than\".",
                ],
                "examples": [
                    {"phrase": "sava teen baje", "english": "3:15", "devanagari": "सवा तीन बजे"},
                    {"phrase": "saadhe teen baje", "english": "3:30", "devanagari": "साढ़े तीन बजे"},
                    {"phrase": "paune teen baje", "english": "2:45 (a quarter to three)", "devanagari": "पौने तीन बजे"},
                ],
            },
            {
                "heading": "dedh and dhaai",
                "text": [
                    "One and a half and two and a half get their own words: dedh and dhaai. People don't say \"saadhe ek\" or \"saadhe do\".",
                ],
                "examples": [
                    {"phrase": "dedh baje", "english": "1:30", "devanagari": "डेढ़ बजे"},
                    {"phrase": "dhaai baje", "english": "2:30", "devanagari": "ढाई बजे"},
                    {"phrase": "dedh ghanta", "english": "An hour and a half", "devanagari": "डेढ़ घंटा"},
                ],
            },
            {
                "heading": "Asking and saying the time",
                "text": [
                    "baje is \"o'clock\". To ask the time, people ask \"how many o'clock\".",
                ],
                "examples": [
                    {"phrase": "kitne baje hain?", "english": "What time is it?", "devanagari": "कितने बजे हैं?"},
                    {"phrase": "abhi paanch baj rahe hain", "english": "It's five o'clock now", "devanagari": "अभी पाँच बज रहे हैं"},
                    {"phrase": "chaar baje milte hain", "english": "Let's meet at four", "devanagari": "चार बजे मिलते हैं"},
                ],
            },
            {
                "heading": "Money and prices",
                "text": [
                    "The same words work for money: dedh sau is 150, dhaai hazaar is 2,500.",
                ],
                "examples": [
                    {"phrase": "ye kitne ka hai?", "english": "How much is this?", "devanagari": "ये कितने का है?"},
                    {"phrase": "dedh sau rupaye", "english": "150 rupees", "devanagari": "डेढ़ सौ रुपये"},
                    {"phrase": "dhaai hazaar", "english": "2,500", "devanagari": "ढाई हज़ार"},
                ],
            },
            {
                "heading": "Big numbers: hazaar, lakh and crore",
                "text": [
                    "Indian families count big numbers in lakhs and crores, not millions. One lakh is 100,000 (written 1,00,000) and one crore is 10 million (1,00,00,000).",
                    "A quick way in: 10 lakh is a million, and a crore is 100 lakh.",
                ],
                "examples": [
                    {"phrase": "do sau", "english": "200", "devanagari": "दो सौ"},
                    {"phrase": "ek hazaar", "english": "1,000", "devanagari": "एक हज़ार"},
                    {"phrase": "ek lakh", "english": "100,000 (1,00,000)", "devanagari": "एक लाख"},
                    {"phrase": "das lakh", "english": "1 million (10,00,000)", "devanagari": "दस लाख"},
                    {"phrase": "ek crore", "english": "10 million (1,00,00,000)", "devanagari": "एक करोड़"},
                ],
            },
            {
                "heading": "Years and ages",
                "text": [
                    "Years before 2000 are said in hundreds, like in English (\"nineteen ninety\"): unnees sau nabbe. Years from 2000 use hazaar.",
                ],
                "examples": [
                    {"phrase": "unnees sau nabbe", "english": "1990", "devanagari": "उन्नीस सौ नब्बे"},
                    {"phrase": "do hazaar chaubees", "english": "2024", "devanagari": "दो हज़ार चौबीस"},
                    {"phrase": "meri umar pachchees saal hai", "english": "I'm 25 years old", "devanagari": "मेरी उम्र पच्चीस साल है"},
                ],
            },
            {
                "heading": "First, second, third",
                "text": [
                    "Ordinal numbers come up for floors, children and \"the first time\". Like other describing words, they end in -i for feminine words: pehla din, pehli baar.",
                ],
                "examples": [
                    {"phrase": "pehla, doosra, teesra, chautha", "english": "First, second, third, fourth", "devanagari": "पहला, दूसरा, तीसरा, चौथा"},
                    {"phrase": "pehli baar", "english": "The first time", "devanagari": "पहली बार"},
                    {"phrase": "doosri manzil", "english": "The second floor", "devanagari": "दूसरी मंज़िल"},
                ],
            },
        ],
    },
    {
        "id": 4,
        "title": "Grammar that sounds \"off\" when wrong",
        "summary": "Noun gender, \"maine\", and the little verbs that make Hindi natural.",
        "available": True,
        "tutor_hint": "\"Why is it maine roti khayi and not khaya?\"",
        "check": [
            {
                "question": "The tea has gone cold: chai ___ ho gayi",
                "options": ["thanda", "thandi"],
                "answer": "thandi",
                "why": "chai is a feminine word, so the adjective ends in -i: thandi.",
            },
            {
                "question": "\"I ate\" (I had my food) is:",
                "options": ["main khana khaya", "maine khana khaya"],
                "answer": "maine khana khaya",
                "why": "With verbs like eating, seeing and doing in the past, Hindi uses maine, not main.",
            },
            {
                "question": "\"I ate a roti\" is:",
                "options": ["maine roti khaya", "maine roti khayi"],
                "answer": "maine roti khayi",
                "why": "With maine, the verb matches the thing, not you. roti is feminine, so it's khayi.",
            },
        ],
        "sections": [
            {
                "heading": "Every noun is masculine or feminine",
                "text": [
                    "In Hindi, things have a gender too. Words that describe them change to match: -a for masculine, -i for feminine. mera becomes meri, thanda becomes thandi.",
                    "There's no perfect rule, so learn the gender with the word. Many words ending in -i are feminine (roti, chai), but not all: paani is masculine. And kitaab is feminine even though it doesn't end in -i.",
                ],
                "examples": [
                    {"phrase": "mera ghar", "english": "My house (ghar is masculine)", "devanagari": "मेरा घर"},
                    {"phrase": "meri kitaab", "english": "My book (kitaab is feminine)", "devanagari": "मेरी किताब"},
                    {"phrase": "paani thanda hai", "english": "The water is cold", "devanagari": "पानी ठंडा है"},
                    {"phrase": "chai thandi ho gayi", "english": "The tea got cold", "devanagari": "चाय ठंडी हो गई"},
                ],
            },
            {
                "heading": "maine, not main, in the past",
                "text": [
                    "With verbs like khana (eat), dekhna (see), karna (do) and padhna (read) in the past, say maine (or humne, aapne). Saying \"main khana khaya\" is one of the most common heritage-speaker slips.",
                    "Then the verb matches the thing, not you: maine khana khaya, but maine film dekhi (film is feminine). Going and coming don't use ne: main ghar gaya or main ghar gayi.",
                ],
                "examples": [
                    {"phrase": "maine khana khaya", "english": "I ate (food)", "devanagari": "मैंने खाना खाया"},
                    {"phrase": "maine film dekhi", "english": "I watched a movie", "devanagari": "मैंने फ़िल्म देखी"},
                    {"phrase": "humne baat ki", "english": "We talked", "devanagari": "हमने बात की"},
                ],
            },
            {
                "heading": "Little helper verbs",
                "text": [
                    "Natural Hindi adds a small second verb: kha lo instead of just khao, bata do instead of just batao. The plain form isn't wrong, but the helper makes it sound softer and more natural.",
                ],
                "examples": [
                    {"phrase": "kha lo", "english": "Go ahead and eat", "devanagari": "खा लो"},
                    {"phrase": "mujhe bata dena", "english": "Let me know", "devanagari": "मुझे बता देना"},
                    {"phrase": "kaam ho gaya", "english": "The work's done", "devanagari": "काम हो गया"},
                    {"phrase": "ruk jao", "english": "Wait / stop", "devanagari": "रुक जाओ"},
                ],
            },
            {
                "heading": "Suggesting and offering",
                "text": [
                    "Short, soft forms do a lot of work in family Hindi: suggesting, asking what to do, and offering things to elders.",
                ],
                "examples": [
                    {"phrase": "chalein?", "english": "Shall we go?", "devanagari": "चलें?"},
                    {"phrase": "main kya karoon?", "english": "What should I do?", "devanagari": "मैं क्या करूँ?"},
                    {"phrase": "aap baithiye", "english": "Please sit (to an elder)", "devanagari": "आप बैठिए"},
                    {"phrase": "chai piyenge?", "english": "Will you have some tea? (to an elder)", "devanagari": "चाय पिएँगे?"},
                ],
            },
        ],
    },
    {
        "id": 5,
        "title": "Sounds English doesn't have",
        "summary": "Soft vs hard t and d, breathy sounds, long vowels.",
        "available": True,
        "tutor_hint": "\"How is the d in daal different from the d in dabba?\"",
        "check": [
            {
                "question": "In daal (lentils), the d is:",
                "options": ["Soft: tongue touching the teeth", "Hard: tongue curled back"],
                "answer": "Soft: tongue touching the teeth",
                "why": "daal has the soft d. The hard d, with the tongue curled back, is in words like dabba.",
            },
            {
                "question": "Which word has a puff of air?",
                "options": ["kal (tomorrow)", "khaana (food)"],
                "answer": "khaana (food)",
                "why": "kh is a k with a puff of air. Without the puff, khaana starts to sound like a different word.",
            },
            {
                "question": "Which one means \"work\"?",
                "options": ["kam", "kaam"],
                "answer": "kaam",
                "why": "kaam (long aa) is work. kam (short a) means less. Vowel length changes the meaning.",
            },
            {
                "question": "The r in ladka is:",
                "options": ["Like an English r", "A quick flap of the tongue"],
                "answer": "A quick flap of the tongue",
                "why": "It's a flap: curl the tongue back, then flick it forward. It's not an English r or a d.",
            },
        ],
        "sections": [
            {
                "heading": "Soft t and d vs hard t and d",
                "text": [
                    "Hindi has two kinds of t and d. Soft: the tongue touches the back of your top teeth. Hard: the tongue curls back to the roof of your mouth. English t and d sit in between, so they can sound off in Hindi.",
                    "Tap Practice on any of these to hear how close you are.",
                ],
                "examples": [
                    {"phrase": "taala", "english": "Lock (soft t)", "devanagari": "ताला"},
                    {"phrase": "tamatar", "english": "Tomato (hard t)", "devanagari": "टमाटर"},
                    {"phrase": "daal", "english": "Lentils (soft d)", "devanagari": "दाल"},
                    {"phrase": "dabba", "english": "Box (hard d)", "devanagari": "डब्बा"},
                ],
            },
            {
                "heading": "Sounds with a puff of air",
                "text": [
                    "kh, gh, chh, jh, th, dh, ph and bh are each a sound with a puff of air after it. The th in Hindi is never like the English th in \"think\": it's a soft t with a puff.",
                ],
                "examples": [
                    {"phrase": "khaana", "english": "Food (kh)", "devanagari": "खाना"},
                    {"phrase": "bhai", "english": "Brother (bh)", "devanagari": "भाई"},
                    {"phrase": "thoda", "english": "A little (th)", "devanagari": "थोड़ा"},
                    {"phrase": "ghar", "english": "Home (gh)", "devanagari": "घर"},
                ],
            },
            {
                "heading": "Short and long vowels",
                "text": [
                    "Hindi vowels come in short and long pairs, and the length can change the meaning. Keep short vowels short and relaxed, and hold long ones steady.",
                ],
                "examples": [
                    {"phrase": "kam", "english": "Less (short a)", "devanagari": "कम"},
                    {"phrase": "kaam", "english": "Work (long aa)", "devanagari": "काम"},
                    {"phrase": "mil", "english": "Meet (short i)", "devanagari": "मिल"},
                    {"phrase": "meel", "english": "Mile (long ee)", "devanagari": "मील"},
                ],
            },
            {
                "heading": "Nasal sounds",
                "text": [
                    "Some vowels go partly through the nose, without a full n at the end. maa (mother) isn't \"maan\": that's a different word.",
                ],
                "examples": [
                    {"phrase": "haan", "english": "Yes", "devanagari": "हाँ"},
                    {"phrase": "maa", "english": "Mother", "devanagari": "माँ"},
                    {"phrase": "nahin", "english": "No", "devanagari": "नहीं"},
                ],
            },
            {
                "heading": "The flapped r",
                "text": [
                    "In ladka and padhna, curl your tongue back, then flick it forward quickly. It's between an r and a d, and English doesn't have it.",
                ],
                "examples": [
                    {"phrase": "ladka", "english": "Boy", "devanagari": "लड़का"},
                    {"phrase": "padhna", "english": "To study", "devanagari": "पढ़ना"},
                    {"phrase": "badi", "english": "Big (feminine)", "devanagari": "बड़ी"},
                ],
            },
        ],
    },
    {
        "id": 6,
        "title": "Sounding natural",
        "summary": "When Hinglish sounds right, and when it sounds like an outsider.",
        "available": True,
        "tutor_hint": "\"Is it okay to say 'mera phone' or should I use a Hindi word?\"",
        "check": [
            {
                "question": "Is \"mera phone kahan hai?\" natural Hindi?",
                "options": ["Yes, phone is a normal Hindi word", "No, use a pure Hindi word for phone"],
                "answer": "Yes, phone is a normal Hindi word",
                "why": "Everyday English words like phone, office and traffic are normal Hindi. Nobody says the textbook word for phone.",
            },
            {
                "question": "Which sounds more natural?",
                "options": ["main feel kar raha hoon ki woh naraz hain", "mujhe lag raha hai ki woh naraz hain"],
                "answer": "mujhe lag raha hai ki woh naraz hain",
                "why": "English words are fine, but English sentence shape sounds translated. Hindi says \"mujhe lag raha hai\" (it seems to me).",
            },
            {
                "question": "How do you tell Nani you miss her?",
                "options": ["mujhe aapki yaad aati hai", "main aapko feel karta hoon", "mera aapko yaad hai"],
                "answer": "mujhe aapki yaad aati hai",
                "why": "Literally \"your memory comes to me\". It's warm and it's how families say it.",
            },
        ],
        "sections": [
            {
                "heading": "English words that are normal Hindi",
                "text": [
                    "Real Hindi speakers mix in English all the time: phone, office, traffic, tension, actually. You don't need to avoid them, and replacing them with textbook words sounds stranger, not better.",
                ],
                "examples": [
                    {"phrase": "mera phone kahan hai?", "english": "Where's my phone?", "devanagari": "मेरा फ़ोन कहाँ है?"},
                    {"phrase": "aaj office mein bahut kaam tha", "english": "There was a lot of work at the office today", "devanagari": "आज ऑफ़िस में बहुत काम था"},
                    {"phrase": "hum traffic mein phas gaye", "english": "We got stuck in traffic", "devanagari": "हम ट्रैफ़िक में फँस गए"},
                ],
            },
            {
                "heading": "When English sounds translated",
                "text": [
                    "The giveaway isn't English words. It's English sentence shape, like \"main feel kar raha hoon ki…\". Hindi often turns it around with mujhe: \"it seems to me\", \"it felt good to me\".",
                ],
                "examples": [
                    {"phrase": "mujhe lagta hai", "english": "I think / it seems to me", "devanagari": "मुझे लगता है"},
                    {"phrase": "mujhe accha laga", "english": "I liked it / it felt nice", "devanagari": "मुझे अच्छा लगा"},
                    {"phrase": "mujhe bura laga", "english": "I felt bad / it hurt my feelings", "devanagari": "मुझे बुरा लगा"},
                ],
            },
            {
                "heading": "Hindi fillers",
                "text": [
                    "Swapping English fillers (like, you know, so) for Hindi ones is one of the quickest ways to sound natural: accha, haan, matlab, arre. yaar is for friends and cousins, not elders.",
                ],
                "examples": [
                    {"phrase": "accha, phir kya hua?", "english": "Okay, then what happened?", "devanagari": "अच्छा, फिर क्या हुआ?"},
                    {"phrase": "arre, aap aa gaye!", "english": "Oh, you're here!", "devanagari": "अरे, आप आ गए!"},
                    {"phrase": "matlab, mujhe nahi pata", "english": "I mean, I don't know", "devanagari": "मतलब, मुझे नहीं पता"},
                ],
            },
            {
                "heading": "Feelings, the way family says them",
                "text": [
                    "Feelings are where heritage speakers most often switch to English. These are the words your family actually uses.",
                ],
                "examples": [
                    {"phrase": "mujhe aapki yaad aati hai", "english": "I miss you (to an elder)", "devanagari": "मुझे आपकी याद आती है"},
                    {"phrase": "mujhe tension ho rahi hai", "english": "I'm stressed / worried", "devanagari": "मुझे टेंशन हो रही है"},
                    {"phrase": "udaas mat ho", "english": "Don't be sad", "devanagari": "उदास मत हो"},
                ],
            },
            {
                "heading": "Talking about your life",
                "text": [
                    "When relatives ask how things are, short natural answers go a long way. English words for your work or hobbies are fine.",
                ],
                "examples": [
                    {"phrase": "mera kaam accha chal raha hai", "english": "Work is going well", "devanagari": "मेरा काम अच्छा चल रहा है"},
                    {"phrase": "aajkal bahut busy hoon", "english": "I'm really busy these days", "devanagari": "आजकल बहुत बिज़ी हूँ"},
                    {"phrase": "mujhe cooking ka shauk hai", "english": "I'm really into cooking", "devanagari": "मुझे कुकिंग का शौक है"},
                ],
            },
        ],
    },
    {
        "id": 7,
        "title": "Idioms and sayings",
        "summary": "The muhavare your elders use all the time.",
        "available": True,
        "tutor_hint": "\"When would Nani say ghar ki murgi daal barabar?\"",
        "check": [
            {
                "question": "\"ghar ki murgi daal barabar\" means:",
                "options": ["We don't value what's close to us", "Chicken costs as much as lentils", "Guests should eat first"],
                "answer": "We don't value what's close to us",
                "why": "Literally \"the chicken at home is worth just lentils\": what we have every day stops feeling special.",
            },
            {
                "question": "\"oont ke munh mein jeera\" is said when:",
                "options": ["Something is far too little for the need", "Someone eats too much", "Food is too spicy"],
                "answer": "Something is far too little for the need",
                "why": "Literally \"a cumin seed in a camel's mouth\": a tiny amount for a big need.",
            },
            {
                "question": "\"naach na jaane aangan tedha\" is about:",
                "options": ["Blaming the tools instead of yourself", "A crooked house", "Learning to dance"],
                "answer": "Blaming the tools instead of yourself",
                "why": "Literally \"can't dance, says the courtyard is crooked\": making excuses.",
            },
        ],
        "sections": [
            {
                "heading": "Sayings about home and family",
                "text": [
                    "Elders use muhavare (sayings) all the time, often half-joking. You don't have to use them yourself, but understanding them makes family conversations much easier to follow.",
                ],
                "examples": [
                    {"phrase": "ghar ki murgi daal barabar", "english": "Literally \"the chicken at home is worth just lentils\": we don't value what's close to us", "devanagari": "घर की मुर्गी दाल बराबर"},
                    {"phrase": "der aaye durust aaye", "english": "Better late than never (said when someone finally arrives)", "devanagari": "देर आए दुरुस्त आए"},
                ],
            },
            {
                "heading": "Sayings about excuses and effort",
                "text": [
                    "These two come up a lot when someone is making excuses, or when help is far too small.",
                ],
                "examples": [
                    {"phrase": "naach na jaane aangan tedha", "english": "Literally \"can't dance, says the courtyard is crooked\": blaming the tools", "devanagari": "नाच न जाने आँगन टेढ़ा"},
                    {"phrase": "oont ke munh mein jeera", "english": "Literally \"a cumin seed in a camel's mouth\": far too little", "devanagari": "ऊँट के मुँह में जीरा"},
                ],
            },
            {
                "heading": "Sayings about money and wanting",
                "text": [
                    "You'll often hear these around shopping, budgets, and the last piece of something everyone wants.",
                ],
                "examples": [
                    {"phrase": "jitni chaadar ho, utne hi pair phailao", "english": "Literally \"stretch your legs only as far as your sheet\": live within your means", "devanagari": "जितनी चादर हो, उतने ही पैर फैलाओ"},
                    {"phrase": "ek anaar sau beemaar", "english": "Literally \"one pomegranate, a hundred sick people\": one thing, too many people wanting it", "devanagari": "एक अनार सौ बीमार"},
                ],
            },
            {
                "heading": "Short everyday expressions",
                "text": [
                    "These shorter expressions turn up in everyday chat, especially when someone is teasing or complaining.",
                ],
                "examples": [
                    {"phrase": "naak mein dum kar diya", "english": "Drove me up the wall (literally \"filled my nose with breath\")", "devanagari": "नाक में दम कर दिया"},
                    {"phrase": "aankhon ka taara", "english": "The apple of someone's eye (literally \"star of the eyes\")", "devanagari": "आँखों का तारा"},
                    {"phrase": "dimaag kharaab hai kya?", "english": "Have you lost your mind? (playful, with friends)", "devanagari": "दिमाग ख़राब है क्या?"},
                ],
            },
        ],
    },
    {
        "id": 8,
        "title": "Culture in conversation",
        "summary": "Why \"khana khaya?\" means \"I care\", festivals, and phone calls.",
        "available": True,
        "tutor_hint": "\"How do I say no to more food without being rude?\"",
        "check": [
            {
                "question": "When Nani asks \"khana khaya?\", she's mostly:",
                "options": ["Showing she cares", "Asking you to cook", "Checking your diet"],
                "answer": "Showing she cares",
                "why": "\"Have you eaten?\" is one of the most common ways family says \"I care about you\".",
            },
            {
                "question": "You're full and an aunty offers more. The politest answer is:",
                "options": ["nahi", "bas, pet bhar gaya, bahut accha bana hai", "no thanks"],
                "answer": "bas, pet bhar gaya, bahut accha bana hai",
                "why": "A warm \"enough, I'm full\" plus praise for the food. A plain \"nahi\" can sound cold, and the first no is often ignored anyway.",
            },
            {
                "question": "Ending a phone call with an elder, which sounds best?",
                "options": ["ok bye", "accha ji, phir baat karte hain, apna khayal rakhiye"],
                "answer": "accha ji, phir baat karte hain, apna khayal rakhiye",
                "why": "\"Okay, let's talk again, take care of yourself.\" Elders expect a warm goodbye, not a quick bye.",
            },
        ],
        "sections": [
            {
                "heading": "Food is love",
                "text": [
                    "\"khana khaya?\" is how many families say \"I care\". Offering food again and again is normal, and the first \"no\" is often ignored. A warm \"bas\" with praise for the food works best.",
                ],
                "examples": [
                    {"phrase": "khana khaya?", "english": "Have you eaten? (often means \"I care\")", "devanagari": "खाना खाया?"},
                    {"phrase": "aur lo na", "english": "Have some more!", "devanagari": "और लो ना"},
                    {"phrase": "bas, pet bhar gaya", "english": "That's enough, I'm full", "devanagari": "बस, पेट भर गया"},
                    {"phrase": "bahut accha bana hai", "english": "It turned out really well (about the food)", "devanagari": "बहुत अच्छा बना है"},
                ],
            },
            {
                "heading": "Festival greetings",
                "text": [
                    "\"Happy Diwali\" is perfectly fine, but a Hindi greeting means a lot to elders. On Raksha Bandhan, sisters tie a rakhi on their brothers' wrists.",
                ],
                "examples": [
                    {"phrase": "Diwali ki bahut bahut badhaai", "english": "Warmest Diwali wishes", "devanagari": "दिवाली की बहुत बहुत बधाई"},
                    {"phrase": "Holi mubarak ho", "english": "Happy Holi", "devanagari": "होली मुबारक हो"},
                    {"phrase": "Eid mubarak", "english": "Happy Eid", "devanagari": "ईद मुबारक"},
                ],
            },
            {
                "heading": "Weddings",
                "text": [
                    "A shaadi has many parts: mehendi (henna), sangeet (music night), baraat (the groom's procession) and vidaai (the bride's farewell, usually emotional).",
                ],
                "examples": [
                    {"phrase": "shaadi kab hai?", "english": "When is the wedding?", "devanagari": "शादी कब है?"},
                    {"phrase": "baraat aa gayi!", "english": "The baraat is here!", "devanagari": "बारात आ गई!"},
                    {"phrase": "vidaai ke time sab ro rahe the", "english": "Everyone was crying at the vidaai", "devanagari": "विदाई के टाइम सब रो रहे थे"},
                ],
            },
            {
                "heading": "Phone calls with relatives",
                "text": [
                    "Calls with relatives follow a pattern: a warm hello, asking about everyone at home, a little news, and a slow, warm goodbye.",
                ],
                "examples": [
                    {"phrase": "namaste ji, sab theek?", "english": "Hello, is everything well?", "devanagari": "नमस्ते जी, सब ठीक?"},
                    {"phrase": "ghar pe sab kaise hain?", "english": "How is everyone at home?", "devanagari": "घर पे सब कैसे हैं?"},
                    {"phrase": "accha ji, phir baat karte hain", "english": "Okay, let's talk again soon", "devanagari": "अच्छा जी, फिर बात करते हैं"},
                    {"phrase": "apna khayal rakhiye", "english": "Take care of yourself (to an elder)", "devanagari": "अपना ख़याल रखिए"},
                ],
            },
        ],
    },
    {
        "id": 9,
        "title": "Listening to real fast speech",
        "summary": "How Hindi actually sounds at family speed.",
        "available": True,
        "tutor_hint": "\"Why does my dad say tusi instead of aap?\"",
        "check": [
            {
                "question": "\"kya kar ra hai?\" is a fast way of saying:",
                "options": ["kya kar raha hai?", "kya karega?", "kya kiya?"],
                "answer": "kya kar raha hai?",
                "why": "At family speed, raha often shrinks to ra: \"What are you doing?\"",
            },
            {
                "question": "\"nai pata\" means:",
                "options": ["I don't know", "It's new", "Not yet"],
                "answer": "I don't know",
                "why": "nai is a fast nahi, so \"nai pata\" is \"nahi pata\": I don't know.",
            },
            {
                "question": "A relative says \"tusi\" instead of \"aap\". Why?",
                "options": ["It's Punjabi influence", "It's a mistake", "It's rude"],
                "answer": "It's Punjabi influence",
                "why": "tusi is the respectful \"you\" in Punjabi. Many Punjabi families mix it into Hindi. It's completely valid.",
            },
        ],
        "sections": [
            {
                "heading": "Words that shrink",
                "text": [
                    "At family speed, common words get shorter: raha becomes ra, nahi becomes nai. Listen for them, since this is often why fast Hindi is hard to follow even when you know the words.",
                    "You don't need to talk this way yourself. Use Hear it to get used to the sound.",
                ],
                "examples": [
                    {"phrase": "kya kar ra hai?", "english": "What are you doing? (fast for kya kar raha hai?)", "devanagari": "क्या कर रा है?"},
                    {"phrase": "nai pata", "english": "I don't know (fast for nahi pata)", "devanagari": "नै पता"},
                    {"phrase": "kahan ja re ho?", "english": "Where are you going? (fast for ja rahe ho)", "devanagari": "कहाँ जा रे हो?"},
                ],
            },
            {
                "heading": "Words that get dropped",
                "text": [
                    "Questions often drop hai or the person: \"aa gaye?\" instead of \"aap aa gaye hain?\". The tone of voice tells you it's a question.",
                ],
                "examples": [
                    {"phrase": "aa gaye?", "english": "You're here? / You made it?", "devanagari": "आ गए?"},
                    {"phrase": "sab theek?", "english": "All good?", "devanagari": "सब ठीक?"},
                    {"phrase": "kaam ho gaya?", "english": "Is the work done?", "devanagari": "काम हो गया?"},
                ],
            },
            {
                "heading": "Regional flavors",
                "text": [
                    "Family Hindi carries the flavor of where your family is from. Punjabi families may say tusi for you. In UP and Bihar, many people say hum for I. Bombay Hindi has its own style, like \"kya re\". All of these are valid Hindi.",
                ],
                "examples": [
                    {"phrase": "tusi kaise ho?", "english": "How are you? (Punjabi flavor: tusi = aap)", "devanagari": "तुसी कैसे हो?"},
                    {"phrase": "hum aa rahe hain", "english": "I'm coming (UP/Bihar flavor: hum = I)", "devanagari": "हम आ रहे हैं"},
                    {"phrase": "kya re, kidhar ja raha hai?", "english": "Hey, where are you off to? (Bombay flavor)", "devanagari": "क्या रे, किधर जा रहा है?"},
                ],
            },
            {
                "heading": "When you can't keep up",
                "text": [
                    "Everyone misses things in fast conversation. Asking politely is normal, and elders are usually happy to repeat.",
                ],
                "examples": [
                    {"phrase": "phir se boliye?", "english": "Could you say that again?", "devanagari": "फिर से बोलिए?"},
                    {"phrase": "maaf kijiye, samajh nahi aaya", "english": "Sorry, I didn't catch that", "devanagari": "माफ़ कीजिए, समझ नहीं आया"},
                    {"phrase": "matlab?", "english": "Meaning? / What do you mean?", "devanagari": "मतलब?"},
                ],
            },
        ],
    },
]


# Finds a unit by its number (or None if it doesn't exist or isn't ready)

def get_unit(unit_id):
    for unit in UNITS:
        if unit["id"] == unit_id and unit["available"]:
            return unit
    return None


# The unit after this one (or None after the last unit)

def next_unit(unit):
    return get_unit(unit["id"] + 1)


# Every example phrase in the lessons, so the voice can find its Devanagari

def all_lesson_phrases():
    phrases = list(NUMBERS)
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
