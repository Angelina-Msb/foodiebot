from engine import load_foods
from nlu import parse_message as P
df=load_foods()
def test_phrases():
    r=P("No chicken biryani, suggest others",df); assert r["dishes"]==["Chicken Biryani"] and r["more"]
    assert P("Show something different",df)["more"]
    assert P("I don't like this",df)["dislike"]
    r=P("Anything other than chicken?",df); assert r["terms"]==["chicken"] and not r["dishes"]
    assert P("Give me more options",df)["more"] and P("Suggest another dish",df)["more"]
    assert P("nope",df)["dislike"] and P("this is boring",df)["dislike"]
def test_human_language():
    r=P("hey i wanna eat some spicy non veg indian lunch under rs 300",df)["prefs"]
    assert r=={"diet":"Non-Vegetarian","cuisine":"Indian","meal":"Lunch","spice":"Spicy","budget":300}, r
    assert P("veg italian dinner for 200 bucks",df)["prefs"]=={"diet":"Vegetarian","cuisine":"Italian","meal":"Dinner","budget":200}
    assert P("no chiken biriyani pls",df)["dishes"]==["Chicken Biryani"]        # typos
    assert P("I'm bored of chicken, something else",df)["terms"]==["chicken"]
    assert set(P("don't want eggs or fish",df)["terms"])=={"egg","fish"}
    assert P("not too spicy",df)["prefs"]["spice"]=="Mild" and P("make it cheap",df)["prefs"]["budget"]==100
    r=P("no meat",df); assert r["prefs"]["diet"]=="Vegetarian" and "chicken" in r["terms"]
    assert P("show me fish fry again",df)["want"]==["Fish Fry"] and P("show me fish fry again",df)["repeat"]
    assert P("change my budget",df)["change"]=="budget" and P("start over",df)["reset"]
    assert P("hello",df)["small"]=="greet" and P("thanks!",df)["small"]=="thanks"
    r=P("asdfgh",df); assert not any(r[k] for k in ("prefs","dishes","terms","more","dislike","small"))
if __name__=="__main__":
    test_phrases(); test_human_language(); print("NLU TESTS PASSED")
