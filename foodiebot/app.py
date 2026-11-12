import html, random, re
import streamlit as st
from engine import load_foods, recommend
from nlu import parse_message

st.set_page_config(page_title="FoodieBot", page_icon="🍽️", layout="centered")

STEPS = [
 ("diet","Are you vegetarian or non-vegetarian?",["Vegetarian","Non-Vegetarian"]),
 ("cuisine","Which cuisine are you craving?",["Indian","Chinese","Italian","Mexican"]),
 ("meal","Which meal is this for?",["Breakfast","Lunch","Dinner","Snacks"]),
 ("budget","What's your budget per dish?",[100,200,300,500]),
 ("spice","How spicy do you like it?",["Mild","Medium","Spicy"]),
]
LABEL = lambda k,v: f"₹{v}" if k=="budget" else str(v)
EMOJI = {"Indian":"🍛","Chinese":"🥡","Italian":"🍕","Mexican":"🌮"}
GRAD = {"Indian":"#F4A259,#E4572E","Chinese":"#F25C54,#B23A48","Italian":"#8DB255,#4F772D","Mexican":"#FFB703,#FB8500"}

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&family=Playfair+Display:wght@700&display=swap');
html,body,[class*="css"]{font-family:'Poppins',sans-serif}
.stApp{background:#FFF8F0}
.hero{background:linear-gradient(135deg,#E4572E,#F4A259);color:#fff;padding:1.6rem 1.8rem;border-radius:22px;
 box-shadow:0 8px 24px rgba(228,87,46,.25);margin-bottom:1.2rem}
.hero h1{font-family:'Playfair Display',serif;margin:0;font-size:2.1rem;color:#fff}
.hero p{margin:.3rem 0 0;opacity:.95}
.card{background:#fff;border-radius:18px;box-shadow:0 4px 16px rgba(60,30,10,.10);margin:.7rem 0;overflow:hidden;color:#3B2A20}
.card .top{height:78px;display:flex;align-items:center;justify-content:space-between;padding:0 1.2rem;color:#fff}
.card .top .em{font-size:2.6rem}.card .top .pr{font-weight:700;font-size:1.4rem}
.card .body{padding:.9rem 1.2rem 1.1rem}
.card h3{margin:0 0 .3rem;font-size:1.15rem;color:#3B2A20}
.card p{margin:.2rem 0 .6rem;color:#6B5A4E;font-size:.92rem}
.tag{display:inline-block;padding:.18rem .65rem;border-radius:999px;font-size:.75rem;font-weight:600;margin:0 .3rem .3rem 0;background:#FDECD8;color:#8A4B16}
.tag.veg{background:#DFF3DC;color:#2B7A2B}.tag.nonveg{background:#FBDDDA;color:#B3261E}
.tag.sp{background:#FFE3D3;color:#C2410C}
.stButton>button{border-radius:999px;border:1.5px solid #E4572E;color:#E4572E;background:#fff;font-weight:600}
.stButton>button:hover{background:#E4572E;color:#fff;border-color:#E4572E}
@media(max-width:600px){.hero h1{font-size:1.6rem}}
</style>""", unsafe_allow_html=True)

@st.cache_data
def foods(): return load_foods()
df = foods()

S = st.session_state
def init():
    S.update(prefs={}, seed=0, edit=None, pending=False, shown=[], excluded=[], terms=[], last=[], chat=[
        ("bot","👋 Hi, I'm **FoodieBot**! Tell me what you're craving in your own words — e.g. *\"non-veg Indian lunch under ₹300, spicy\"* — or just use the buttons.\n\n"+STEPS[0][1])])
if "chat" not in S: init()

def say(t): S.chat.append(("bot", t))
def missing(): return next((k for k,_,_ in STEPS if k not in S.prefs), None)
def ask(k): return next(q for kk,q,_ in STEPS if kk==k)
def summary():
    p = S.prefs; return f"{p['diet']} · {p['cuisine']} · {p['meal']} · up to ₹{p['budget']} · {p['spice']}"

def show(prefix="", want=()):
    S.seed += 1
    r, note = recommend(df, S.prefs, exclude=S.excluded, exclude_terms=S.terms, shown=S.shown, seed=S.seed)
    rows = df[df.name.isin(want)].to_dict("records") + [x for x in r.to_dict("records") if x["name"] not in want]
    if not rows:
        say(prefix+"I've already shown you every dish I have for these preferences (and I'm skipping the ones you rejected) 🍽️ "
            "Say *show them again*, or change a preference — try another cuisine or a bigger budget."); return
    S.shown += [x["name"] for x in rows if x["name"] not in S.shown]
    S.last = [x["name"] for x in rows]
    say(f"{prefix}Here are {len(rows)} dishes for **{summary()}** 🍽️" + (f"\n\n⚠️ {note}" if note else ""))
    S.chat.append(("cards", rows))

HINT = ("You can say things like *more options*, *something different*, *no chicken biryani*, "
        "*anything other than chicken?*, *I don't like this*, or *change my budget to ₹200*.")

def respond(text):
    S.chat.append(("user", text))
    p = parse_message(text, df)
    if p["reset"]: init(); return
    acts = p["prefs"] or p["dishes"] or p["terms"] or p["want"] or p["more"] or p["repeat"] or p["dislike"]
    miss = missing()
    if p["small"] and not acts:
        say({"greet":"Hello! 👋 ","thanks":"You're welcome! 😊 ","bye":"Bye! Enjoy your meal 🍽️ ",
             "help":"I suggest dishes from your preferences and learn what you don't like. "+HINT+" "}[p["small"]]
            + (ask(miss) if miss and p["small"]!="bye" else "")); return
    if p["change"] and not p["prefs"]:
        if p["change"] in ("diet","cuisine","meal","budget","spice"): S.edit = p["change"]; say("Sure! "+ask(p["change"]))
        else: S.pending = True; say("Sure! Pick what you'd like to change below 👇")
        return
    ack = ""
    if p["prefs"]:
        ack = "Got it — " + ", ".join(f"{k} → {LABEL(k,v)}" for k,v in p["prefs"].items()) + ". "
        S.prefs.update(p["prefs"])
        if S.edit in p["prefs"]: S.edit = None
        S.pending = False
    if p["want"]: S.excluded = [x for x in S.excluded if x not in p["want"]]
    new = [d for d in p["dishes"] if d not in S.excluded]; S.excluded += new
    nt = [t for t in p["terms"] if t not in S.terms]; S.terms += nt
    if new: ack += "No problem, I'll skip " + ", ".join(new) + ". "
    if nt: ack += "Okay, no more " + "/".join(nt) + " dishes. "
    if p["dislike"] and not p["dishes"] and not p["terms"]:
        gone = [x for x in S.last if x not in S.excluded]
        if gone: S.excluded += gone; ack += "Sorry about that! I'll skip " + ", ".join(gone) + " from now on. "
        else: ack += "Noted. "
    miss = missing()
    if miss:
        say((ack or "") + ("" if acts else "Hmm, I didn't catch that 🤔 ") + ask(miss)); return
    if not acts: say("Hmm, I didn't quite get that 🤔 " + HINT); return
    want = p["want"] or ([x for x in S.last if x not in S.excluded] if p["repeat"] else [])
    show(ack or ("Fresh ideas coming up! " if p["more"] else ""), want)

def card(r):
    veg = r["category"]=="Vegetarian"
    e = html.escape
    return f"""<div class="card"><div class="top" style="background:linear-gradient(135deg,{GRAD[r['cuisine']]})">
<span class="em">{EMOJI[r['cuisine']]}</span><span class="pr">₹{int(r['price'])}</span></div><div class="body">
<h3>{e(r['name'])}</h3><p>{e(r['description'])}</p>
<span class="tag {'veg' if veg else 'nonveg'}">{'🟢 Veg' if veg else '🔴 Non-Veg'}</span>
<span class="tag">{e(r['cuisine'])}</span><span class="tag sp">🌶️ {e(r['spice'])}</span>
<span class="tag">🕐 {e(r['meal_type'])}</span></div></div>"""

st.markdown('<div class="hero"><h1>🍽️ FoodieBot</h1><p>Your personal food discovery assistant</p></div>', unsafe_allow_html=True)

for kind, content in S.chat:
    if kind=="cards":
        with st.chat_message("assistant", avatar="🍽️"):
            for r in content: st.markdown(card(r), unsafe_allow_html=True)
    else:
        with st.chat_message("user" if kind=="user" else "assistant", avatar=None if kind=="user" else "🍽️"):
            st.markdown(content)

key = S.edit or missing()
if key:
    opts = next(o for k,_,o in STEPS if k==key)
    for c,o in zip(st.columns(len(opts)), opts):
        if c.button(LABEL(key,o), key=f"o_{key}_{o}", use_container_width=True):
            respond(LABEL(key,o)); st.rerun()
else:
    c1,c2,c3 = st.columns(3)
    if c1.button("🔄 New picks", use_container_width=True): respond("Show me something different"); st.rerun()
    if c2.button("✏️ Change prefs", use_container_width=True): S.pending = True; st.rerun()
    if c3.button("♻️ Reset", use_container_width=True): init(); st.rerun()
    if S.pending:
        pick = st.selectbox("What would you like to change?", [k for k,_,_ in STEPS],
            format_func=lambda k: {"diet":"Diet","cuisine":"Cuisine","meal":"Meal type","budget":"Budget","spice":"Spice level"}[k])
        if st.button("Change it"):
            S.edit, S.pending = pick, False; say(ask(pick)); st.rerun()

with st.sidebar:
    st.header("Your preferences")
    for k,_,_ in STEPS:
        v = S.prefs.get(k); st.write(f"**{k.title()}:** {LABEL(k,v) if v else '—'}")
    if S.excluded or S.terms:
        st.write("**Skipping:** " + ", ".join(S.excluded + S.terms))
    if st.button("♻️ Reset conversation", key="sb_reset"): init(); st.rerun()

if txt := st.chat_input("Type anything, e.g. “no chicken biryani, suggest others”…"):
    respond(txt); st.rerun()
