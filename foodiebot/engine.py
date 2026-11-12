"""Recommendation engine (no UI dependencies)."""
import random, re
from pathlib import Path
import pandas as pd

DATA = Path(__file__).parent / "data" / "foods.csv"
SPICE = {"Mild": 0, "Medium": 1, "Spicy": 2}
KEYS = ["diet", "cuisine", "meal", "budget", "spice"]
MIN_RESULTS = 3
TIERS = [("", {}),
 ("spice level", dict(spice=False)),
 ("spice level and budget", dict(spice=False, budget=False)),
 ("spice level, budget and meal type", dict(spice=False, budget=False, meal=False)),
 ("spice level, budget, meal type and cuisine", dict(spice=False, budget=False, meal=False, cuisine=False))]

def load_foods(path=DATA):
    df = pd.read_csv(path).drop_duplicates("name").reset_index(drop=True)
    need = {"name","cuisine","category","meal_type","price","spice","description"}
    if not need <= set(df.columns): raise ValueError("Dataset missing columns")
    return df

def _term_mask(df, terms):
    text = (df.name + " " + df.description).str.lower()
    m = pd.Series(False, index=df.index)
    for t in terms: m |= text.str.contains(r"\b" + re.escape(t.lower()), regex=True)
    return m

def recommend(df, prefs, exclude=(), exclude_terms=(), shown=(), limit=4, seed=0, allow_repeat=False):
    """Return (dataframe, note). Never returns excluded or already-shown dishes
    (unless allow_repeat). Diet is never relaxed. Aims for >= 3 dishes by relaxing
    spice -> budget -> meal -> cuisine, in that order."""
    base = df[~df.name.isin(list(exclude))]
    if exclude_terms: base = base[~_term_mask(base, exclude_terms)]
    if not allow_repeat: base = base[~base.name.isin(list(shown))]
    d, c, m, b, s = (prefs.get(k) for k in KEYS)
    def f(x, diet=True, cuisine=True, meal=True, budget=True, spice=True):
        if diet and d: x = x[x.category == d]
        if cuisine and c: x = x[x.cuisine == c]
        if meal and m: x = x[x.meal_type == m]
        if budget and b: x = x[x.price <= b]
        if spice and s: x = x[x.spice == s]
        return x
    rng, parts, got, exact, used = random.Random(seed), [], 0, 0, ""
    for i, (label, kw) in enumerate(TIERS):
        if i and got >= MIN_RESULTS: break
        x = f(base, **kw)
        if parts: x = x[~x.name.isin(pd.concat(parts).name)]
        if not len(x): continue
        dist = x.spice.map(SPICE).sub(SPICE[s]).abs() if s else 0
        x = x.assign(_d=dist, _r=[rng.random() for _ in range(len(x))]).sort_values(["_d", "_r"]).drop(columns=["_d", "_r"])
        x = x.head(limit if i == 0 else MIN_RESULTS - got)
        parts.append(x); got += len(x); used = label
        if i == 0: exact = got
    out = pd.concat(parts).reset_index(drop=True) if parts else df.iloc[0:0]
    tail = " I'm not repeating dishes you've already seen or rejected."
    note = ""
    if len(out) and exact == 0:
        note = f"No remaining dish matches all your preferences, so I relaxed {used}." + tail
    elif len(out) > exact:
        note = f"Only {exact} dish{'es' if exact != 1 else ''} left that match everything, so I added close alternatives by relaxing {used}." + tail
    return out, note
