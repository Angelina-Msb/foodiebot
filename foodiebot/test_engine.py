import itertools
from engine import *
df = load_foods(); assert len(df) >= 40 and df.name.is_unique
assert set(df.cuisine)=={"Indian","Chinese","Italian","Mexican"} and set(df.meal_type)=={"Breakfast","Lunch","Dinner","Snacks"}
P = dict(diet="Non-Vegetarian",cuisine="Indian",meal="Lunch",budget=300,spice="Spicy")

def test_filters():
    for k,v,col in [("diet","Vegetarian","category"),("diet","Non-Vegetarian","category"),("cuisine","Italian","cuisine"),
                    ("meal","Snacks","meal_type"),("spice","Mild","spice")]:
        r,_=recommend(df,{k:v}); assert (r[col]==v).all() and len(r)
    r,_=recommend(df,dict(budget=100)); assert (r.price<=100).all() and len(r)

def test_multiple_recommendations():
    r,n=recommend(df,P); assert len(r)>=3 and not n
    assert (r.category=="Non-Vegetarian").all() and (r.cuisine=="Indian").all() and (r.meal_type=="Lunch").all()
    assert (r.price<=300).all() and (r.spice=="Spicy").all() and r.name.is_unique
    assert {"Chicken Tikka","Chicken Curry Meals","Egg Biryani","Fish Fry"} & set(r.name)

def test_no_duplicates_across_batches():
    seen=set()
    for s in range(1,30):
        r,_=recommend(df,P,shown=seen,seed=s)
        if not len(r): break
        assert not (set(r.name)&seen), "duplicate recommended"; seen|=set(r.name)
    assert len(seen)>=20
    r,_=recommend(df,P,shown=seen,allow_repeat=True); assert len(r)  # explicit repeat allowed

def test_rejected_dishes_and_terms():
    r,_=recommend(df,P,exclude=["Chicken Biryani"]); assert "Chicken Biryani" not in set(r.name) and len(r)>=3
    r,_=recommend(df,P,exclude_terms=["chicken"]); assert len(r)>=3 and not r.name.str.lower().str.contains("chicken").any()
    r,_=recommend(df,P,exclude_terms=["chicken","egg"]); assert not (r.name+r.description).str.lower().str.contains(r"\bchicken|\begg").any()

def test_relaxation_never_returns_excluded():
    ex=list(df[(df.category=="Non-Vegetarian")&(df.cuisine=="Indian")&(df.meal_type=="Lunch")].name)
    r,n=recommend(df,P,exclude=ex); assert len(r)>=3 and n and not set(r.name)&set(ex) and (r.category=="Non-Vegetarian").all()
    r,n=recommend(df,dict(diet="Non-Vegetarian",cuisine="Italian",meal="Breakfast",budget=100,spice="Spicy")); assert len(r)>=3 and n
    r,n=recommend(df,P,exclude=list(df.name)); assert len(r)==0

def test_all_combinations():
    for combo in itertools.product(["Vegetarian","Non-Vegetarian"],["Indian","Chinese","Italian","Mexican"],["Breakfast","Lunch","Dinner","Snacks"],[100,200,300,500],["Mild","Medium","Spicy"]):
        r,n=recommend(df,dict(zip(KEYS,combo))); assert len(r)>=3 and (r.category==combo[0]).all() and r.name.is_unique, combo

if __name__=="__main__":
    for k,f in list(globals().items()):
        if k.startswith("test_"): f(); print("ok",k)
    print("ENGINE TESTS PASSED")
