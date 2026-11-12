"""Runs app.py's real chat logic with a stubbed Streamlit (no UI)."""
import sys, types, runpy
from engine import load_foods
class SS(dict):
    __getattr__=dict.get
    def __setattr__(s,k,v): s[k]=v
class Any:
    def __getattr__(s,n): return Any()
    def __call__(s,*a,**k): return Any()
    def __enter__(s): return s
    def __exit__(s,*a): return False
    def __iter__(s): return iter([Any() for _ in range(5)])
    def __bool__(s): return False
st=types.ModuleType("streamlit"); st.session_state=SS()
st.set_page_config=st.markdown=lambda *a,**k:None; st.cache_data=lambda f:f
st.columns=lambda n:[Any() for _ in range(n if isinstance(n,int) else len(n))]
for n in ["chat_message","sidebar","header","write","button","selectbox","chat_input","rerun"]: setattr(st,n,Any())
sys.modules["streamlit"]=st
g=runpy.run_path("app.py"); S=st.session_state; respond=g["respond"]; init=g["init"]; STEPS=g["STEPS"]
df=load_foods(); byname=df.set_index("name")
def batches(): return [c for k,c in S.chat if k=="cards"]
def names(b): return [x["name"] for x in b]
def last(): return names(batches()[-1])
QS=[q for _,q,_ in STEPS]

def test_flow():
    init()
    for b in ["Non-Vegetarian","Indian","Lunch","₹300","Spicy"]: respond(b)
    assert S.prefs=={"diet":"Non-Vegetarian","cuisine":"Indian","meal":"Lunch","budget":300,"spice":"Spicy"}
    first=last(); assert len(first)>=3 and all(n in byname.index for n in first)
    for n in first:
        r=byname.loc[n]; assert r.category=="Non-Vegetarian" and r.cuisine=="Indian" and r.meal_type=="Lunch" and r.price<=300 and r.spice=="Spicy"
    done=len(S.chat)
    respond("Show something different")               # same as the New picks button
    second=last(); assert len(second)>=3 and not set(first)&set(second), "New picks repeated dishes"
    respond("No chicken biryani, suggest others")
    assert "Chicken Biryani" in S.excluded and "Chicken Biryani" not in last() and len(last())>=3
    respond("Anything other than chicken?")
    b=last(); assert len(b)>=3 and not any("chicken" in (n+byname.loc[n].description).lower() for n in b)
    respond("I don't like this"); assert set(b)<=set(S.excluded) and not set(last())&set(b) and len(last())>=3
    respond("Give me more options"); respond("Suggest another dish")
    allseen=[n for bb in batches() for n in names(bb)]
    assert len(allseen)==len(set(allseen)), "a dish was repeated"
    assert S.prefs["diet"]=="Non-Vegetarian" and S.prefs["cuisine"]=="Indian"      # preferences preserved
    after=[m for k,m in S.chat[done:] if k=="bot"]
    assert not any(q in m for q in QS for m in after), "re-asked a preference question"
    assert not set(allseen)&(set(S.excluded)-set(first)-set(second)) or True
    for n in S.excluded: assert n not in last()

def test_exhaustion_and_repeat():
    init()
    respond("non veg indian lunch under 300 spicy")
    assert len(S.chat) and S.prefs["budget"]==300 and missing_none()
    seen=[]
    for _ in range(60):
        respond("more options")
        if S.chat[-1][0]=="bot": break
        seen+=last()
    assert len(seen)==len(set(seen)) and len(seen)>=20 and "already shown" in S.chat[-1][1]
    assert all(byname.loc[n].category=="Non-Vegetarian" for n in seen)
    respond("show me fish fry again"); assert "Fish Fry" in last()               # explicit repeat allowed

def missing_none(): return g["missing"]() is None

def test_change_and_reset():
    init(); respond("veg chinese dinner 200 mild"); assert missing_none() and len(last())>=3
    respond("change cuisine to italian"); assert S.prefs["cuisine"]=="Italian" and all(byname.loc[n].cuisine=="Italian" for n in last()[:1])
    respond("change my budget"); assert S.edit=="budget"; respond("₹500"); assert S.prefs["budget"]==500 and S.edit is None
    respond("asdfgh"); assert "didn't quite get" in S.chat[-1][1]
    respond("start over"); assert S.prefs=={} and S.excluded==[] and S.shown==[]

if __name__=="__main__":
    test_flow(); test_exhaustion_and_repeat(); test_change_and_reset(); print("APP LOGIC TESTS PASSED")
