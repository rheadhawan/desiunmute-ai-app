# Hindi sounds: splits a word into its sounds and explains how to say each one
#
# Why: for Hindi, Azure scores every sound in a word but doesn't say which
# sound is which. In Rhea's test (2026-11-18), "नमस्ते" came back with 7 scores,
# one for each sound in order: n a m a s t e. So if we split the word into the
# same sounds ourselves, we know exactly which part was off.
#
# If our split ever has a different number of sounds than Azure's scores,
# we don't guess: the coach only names the word.


# How to say each sound, in plain English (heritage learners, no jargon).
# Sounds that are the same as in English (j, m, s, b...) aren't here, because
# "a plain j" doesn't help anyone. For those, the coach says "listen and copy".
# DRAFT: to be reviewed by a native speaker (Rhea's mom), like the lessons.
SOUND_GUIDE = {
    # Vowels
    "अ": "short and relaxed, like the \"u\" in \"but\". Don't stretch it into \"ay\" or \"eh\".",
    "आ": "long and open, like the \"a\" in \"father\".",
    "इ": "short, like the \"i\" in \"sit\".",
    "ई": "long and steady, like the \"ee\" in \"see\".",
    "उ": "short, like the \"u\" in \"put\".",
    "ऊ": "long, like the \"oo\" in \"food\".",
    "ए": "one pure sound, like the start of \"say\". Don't let it slide into \"ee\" at the end.",
    "ऐ": "like the \"e\" in \"bed\", held a little longer.",
    "ओ": "one pure sound, like the start of \"go\". Don't let it slide into \"oo\" at the end.",
    "औ": "like the \"aw\" in \"law\".",
    # Sounds made with the tongue on the teeth (softer than English)
    "त": "a soft \"t\": touch the back of your top teeth with your tongue, with no puff of air.",
    "थ": "the soft \"t\" (tongue on your teeth) with a small puff of air after it.",
    "द": "a soft \"d\": touch the back of your top teeth with your tongue.",
    "ध": "the soft \"d\" (tongue on your teeth) with a breathy puff after it.",
    "न": "an \"n\" with your tongue touching your top teeth.",
    "ल": "a light \"l\" with your tongue near your top teeth, not the heavy English \"l\" in \"ball\".",
    # Sounds made with the tongue curled back
    "ट": "a hard \"t\": curl your tongue back to the roof of your mouth.",
    "ठ": "the hard \"t\" (tongue curled back) with a puff of air.",
    "ड": "a hard \"d\": curl your tongue back to the roof of your mouth.",
    "ढ": "the hard \"d\" (tongue curled back) with a breathy puff.",
    "ड़": "curl your tongue back, then flick it forward quickly.",
    "र": "a quick tap of the tongue, like the \"tt\" in an American \"butter\". Never the English \"r\".",
    # Plain sounds vs. sounds with a puff of air
    "क": "a plain \"k\" with no puff of air.",
    "ख": "a \"k\" with a strong puff of air.",
    "घ": "a \"g\" with a breathy puff.",
    "च": "a \"ch\" with no puff of air.",
    "छ": "a \"ch\" with a strong puff of air.",
    "झ": "a \"j\" with a breathy puff.",
    "प": "a \"p\" with no puff of air (English adds one).",
    "फ": "a \"p\" with a strong puff of air.",
    "भ": "a \"b\" with a breathy puff.",
    # Others
    "ह": "a clear \"h\", even in the middle of a word.",
    "व": "between a \"v\" and a \"w\": your lips barely touch.",
}

# How each sound is written in romanized Hindi
ROMAN = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo", "ऋ": "ri",
    "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऑ": "o",
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh", "ष": "sh", "स": "s", "ह": "h",
    "क़": "q", "ख़": "kh", "ग़": "g", "ज़": "z", "ड़": "d", "ढ़": "rh", "फ़": "f",
}

# Vowel signs (the marks added to a letter) and the vowel each one is
VOWEL_SIGNS = {
    "ा": "आ", "ि": "इ", "ी": "ई", "ु": "उ", "ू": "ऊ", "ृ": "ऋ",
    "े": "ए", "ै": "ऐ", "ो": "ओ", "ौ": "औ", "ॉ": "ऑ",
}
VOWELS = {"अ", "आ", "इ", "ई", "उ", "ऊ", "ऋ", "ए", "ऐ", "ओ", "औ", "ऑ"}

HALANT = "्"        # joins two consonants (no vowel in between)
NUKTA = "़"         # the dot that turns ज into ज़, ड into ड़
DOT_NASAL = "ं"     # the dot on top (हैं, हिंदी)
MOON_NASAL = "ँ"    # the moon on top (हाँ, हूँ)


def is_consonant(letter):
    return "क" <= letter[0] <= "ह" or "क़" <= letter[0] <= "य़"


# Splits a Devanagari word into its sounds, the way they're spoken.
# Each sound is {"letter": "न", "vowel": False, "silent_a": False}.

def split_sounds(word):
    sounds = []
    letters = [c for c in word if "ऀ" <= c <= "ॿ" and c not in "।॥"]
    i = 0

    while i < len(letters):
        letter = letters[i]

        if is_consonant(letter):
            if i + 1 < len(letters) and letters[i + 1] == NUKTA:
                letter += NUKTA
                i += 1
            sounds.append({"letter": letter, "vowel": False})

            following = letters[i + 1] if i + 1 < len(letters) else ""
            if following in VOWEL_SIGNS:
                sounds.append({"letter": VOWEL_SIGNS[following], "vowel": True})
                i += 1
            elif following == HALANT:
                i += 1
            else:
                # Every consonant has a hidden short "a" unless something removes it
                sounds.append({"letter": "अ", "vowel": True, "hidden": True})

        elif letter in VOWELS:
            sounds.append({"letter": letter, "vowel": True})

        elif letter == DOT_NASAL and i + 1 < len(letters) and is_consonant(letters[i + 1]):
            # Before a consonant, the dot is a real "n" or "m" (हिंदी = hindi)
            sounds.append({"letter": "न", "vowel": False})

        # The moon, and the dot at the end of a word, only make the vowel
        # nasal: no extra sound

        i += 1

    return drop_silent_a(sounds)


# Hindi speakers skip some hidden "a"s: always at the end of a word
# (आप is "aap", not "aapa"), and in the middle when it sits between
# vowel-consonant and consonant-vowel (बोलना is "bolna", not "bolana").

def drop_silent_a(sounds):
    def is_hidden_a(n):
        return 0 <= n < len(sounds) and sounds[n].get("hidden")

    # 1. The end of the word (but keep it in a one-letter word like न)
    if len(sounds) > 2 and is_hidden_a(len(sounds) - 1):
        sounds = sounds[:-1]

    # 2. The middle, checking from the end of the word to the start
    n = len(sounds) - 3
    while n >= 2:
        if (
            is_hidden_a(n)
            and sounds[n - 2]["vowel"] and not sounds[n - 1]["vowel"]
            and not sounds[n + 1]["vowel"] and n + 2 < len(sounds) and sounds[n + 2]["vowel"]
        ):
            sounds = sounds[:n] + sounds[n + 1:]
            n -= 2
        n -= 1

    return sounds


# Groups sounds into the parts a learner would say ("na", "ma", "ste")

def word_parts(sounds):
    parts = []
    current = []

    for number, sound in enumerate(sounds):
        current.append(number)
        if sound["vowel"]:
            parts.append(current)
            current = []

    # Consonants at the end belong to the last part ("aap", not "aa" + "p")
    if current:
        if parts:
            parts[-1] += current
        else:
            parts.append(current)

    # Two consonants together in the middle are split between the parts,
    # the way people say them ("bol·naa", "nam·as·te" -> "na·mas·te")
    for n in range(1, len(parts)):
        if len(parts[n]) >= 3 and not sounds[parts[n][0]]["vowel"] and not sounds[parts[n][1]]["vowel"]:
            parts[n - 1].append(parts[n].pop(0))

    return parts


def romanize_part(sounds, part):
    text = "".join(ROMAN.get(sounds[n]["letter"], "") for n in part)
    return text.replace("chchh", "cch")   # अच्छा is usually written "accha"
