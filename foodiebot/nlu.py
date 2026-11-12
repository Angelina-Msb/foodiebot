"""Rule-based natural-language understanding for FoodieBot (free, no APIs)."""
import re, difflib

OPTS = [100, 200, 300, 500]
GENERIC = set("""the a an and or of with in on to for some any me my i im ive it its is are be do dont want like give show
suggest recommend try please pls food foods dish dishes item items anything something stuff thing things else other
others another more again just now too very really much style meals meal plate bowl combo one ones this that these those
there you can could would let lets get have has also only bit little instead options option ideas idea from than at as
so but if then what about how by up eat wanna gonna need""".split())
DROP = set("indian chinese italian mexican veg vegetarian veggie mild breakfast lunch dinner snacks hot sour nonveg".split())
REF = {"this", "that", "it", "these", "those", "one", "ones", "them"}
SYN = {"meat": ["chicken", "mutton", "fish", "prawn", "keema", "lamb"], "seafood": ["fish", "prawn"]}
CUES = sorted(["anything other than", "something other than", "anything but", "other than", "apart from", "fed up with",
 "tired of", "sick of", "bored of", "stop suggesting", "dont want", "dont like", "do not want", "do not like", "dont",
 "do not", "without", "except", "excluding", "exclude", "skip", "avoid", "hate", "never", "remove", "besides",
 "but not", "not", "no"], key=len, reverse=True)
BOUND = "suggest|show|give|recommend|try|instead|something|others|other|more|please|but|again"
NEGSEG = re.compile(r"\b(?:%s)\b\s*(.*?)(?=\b(?:%s)\b|[,.;!?]|$)" % ("|".join(CUES), BOUND), re.S)
R = lambda p: re.compile(p)
MORE = R(r"\b(more|another|different|else|other|others|new|fresh|next|alternatives?|options?|ideas?|variety|surprise|suggest\w*|recommend\w*|show|give|something|anything|what about|how about|hungry|feed|pick|choose|try)\b")
DISLIKE = R(r"\b(dont like|do not like|dislike|hate|not (a fan|interested|for me|my (thing|taste))|yuck|ew|boring|no thanks|not this|not that|not these|dont want (this|that|it|these)|wrong|bad)\b|^(no|nope|nah)$")
REPEAT = R(r"\b(repeat|bring back|go back|same (ones|dishes)|(them|those|these|previous|earlier) again|show again)\b")
RESET = R(r"\b(reset|start over|start again|restart|begin again|from scratch|clear everything)\b")
CHANGE = R(r"\b(change|update|edit|modify|switch)\b")
KEYWORDS = {"diet": "diet", "cuisine": "cuisine", "meal": "meal", "budget": "budget", "spice": "spice", "spicy": "spice"}

def norm(text):
    t = text.lower().replace("\u2019", "'").replace("'", "")
    t = re.sub(r"non[\s\-]*veg(?:etarian)?", "nonveg", t).replace("\u20b9", " rs ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9,.;!?\s]", " ", t)).strip()

tok = lambda s: re.findall(r"[a-z0-9]+", s)

def _vocab(names):
    v = {w for nt in names.values() for w in nt if len(w) >= 3 and w not in GENERIC and w not in DROP}
    return v | set(SYN)

def canon(w, vocab):
    if w in vocab: return w
    for c in (w[:-1] if w.endswith("s") else "", w + "s"):
        if c and c in vocab: return c
    if len(w) >= 5:
        m = difflib.get_close_matches(w, vocab, 1, 0.84)
        if m: return m[0]
    return w

def _hits(toks, names):
    out = []
    for L in (4, 3, 2):
        for i in range(len(toks) - L + 1):
            w = set(toks[i:i + L]); out += [n for n, nt in names.items() if w <= nt]
    return list(dict.fromkeys(out))

def parse_message(text, df):
    t = norm(text)
    names = {n: set(tok(norm(n))) for n in df.name}
    vocab = _vocab(names)
    clean = lambda s: [canon(w, vocab) for w in tok(s) if w not in GENERIC]
    split = lambda s: re.split(r"\b(?:and|or|nor)\b|&|,", s)
    segs = [m.group(1) for m in NEGSEG.finditer(t)]
    pos = NEGSEG.sub(" ", t)
    prefs, dishes, terms = {}, [], []
    for seg in segs:
        if "nonveg" in seg: prefs["diet"] = "Vegetarian"
        elif re.search(r"\bveg", seg): prefs["diet"] = "Non-Vegetarian"
        if re.search(r"\bspic", seg) or seg.strip() in ("hot", "too hot"): prefs["spice"] = "Mild"
        for part in split(seg):
            toks = clean(part); h = _hits(toks, names)
            if h: dishes += h
            else: terms += [w for w in toks if w in vocab]
    terms = list(dict.fromkeys(x for w in terms for x in SYN.get(w, [w])))
    if "meat" in " ".join(segs): prefs["diet"] = "Vegetarian"
    want = list(dict.fromkeys(h for part in split(pos) for h in _hits(clean(part), names)))
    # positive preferences
    if "nonveg" in pos or re.search(r"\b(meat|chicken|mutton|fish|prawns?|eggs?|lamb|seafood|keema|kebab)\b", pos): prefs["diet"] = "Non-Vegetarian"
    elif re.search(r"\bveg\w*", pos): prefs["diet"] = "Vegetarian"
    for pat, k, val in [(r"\bindian|\bdesi\b", "cuisine", "Indian"), (r"\bchin\w*", "cuisine", "Chinese"),
        (r"\bital\w*", "cuisine", "Italian"), (r"\bmex\w*", "cuisine", "Mexican"),
        (r"\bbreakfast|\bbrunch|\bmorning", "meal", "Breakfast"), (r"\blunch|\bafternoon", "meal", "Lunch"),
        (r"\bdinner|\bsupper|\btonight", "meal", "Dinner"), (r"\bsnack\w*|\bstarters?\b|\bappetizer|\bevening|\bmunch\w*", "meal", "Snacks"),
        (r"\bmild\b|\bbland\b|\bless spic\w*|\blow spice|\bnot spic\w*", "spice", "Mild"), (r"\bmedium\b|\bmoderate", "spice", "Medium"),
        (r"\bspic(?:y|ey|ier)\b|\bhot\b(?! and sour)|\bfiery\b|\bchatpata", "spice", "Spicy")]:
        if re.search(pat, pos) and not (k == "spice" and k in prefs and val != "Mild" and prefs[k] == "Mild" and segs):
            if k == "spice" and "spice" in prefs and prefs["spice"] == "Mild": continue
            prefs.setdefault(k, val) if k == "spice" and val != "Mild" and k in prefs else prefs.__setitem__(k, val)
    n = re.search(r"(?<!\d)(\d{2,4})(?!\d)", t)
    if n and int(n.group(1)) >= 50:
        v = int(n.group(1)); prefs["budget"] = max([o for o in OPTS if o <= v], default=100)
    elif re.search(r"\b(cheap\w*|affordable|economical|low budget|tight budget)\b", t): prefs["budget"] = 100
    elif re.search(r"\b(premium|expensive|fancy|splurge|any budget|unlimited)\b", t): prefs["budget"] = 500
    ref_neg = any(set(tok(s)) & REF for s in segs)
    small = None
    if re.match(r"^(hi|hello|hey|hola|namaste|yo|sup|good (morning|afternoon|evening))\b", t): small = "greet"
    elif re.search(r"\b(thanks|thank you|thx)\b", t): small = "thanks"
    elif re.search(r"\b(bye|goodbye|see you)\b", t): small = "bye"
    elif re.search(r"\b(help|what can you do|how does this work|who are you)\b", t): small = "help"
    change = None
    if CHANGE.search(t):
        change = next((v for k, v in KEYWORDS.items() if re.search(r"\b%s\b" % k, t)), "any" if re.search(r"pref|setting|choice", t) else None)
    return dict(prefs=prefs, dishes=dishes, terms=terms, want=want, small=small, change=change,
                reset=bool(RESET.search(t)), repeat=bool(REPEAT.search(t) or (want and re.search(r"\bagain\b", t))),
                dislike=bool(DISLIKE.search(t)) or ref_neg,
                more=bool(MORE.search(t)) or bool(segs and (dishes or terms)))
