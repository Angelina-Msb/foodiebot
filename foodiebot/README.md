# 🍽️ FoodieBot
A conversational food recommendation chatbot built with Streamlit + Pandas. No API keys, no paid services.

**Features:** natural-language chat ("no chicken biryani, suggest others", "anything other than chicken?", "I don't like this", "more options"), rejected-dish memory, no repeated dishes per conversation, guided chat (diet, cuisine, meal, budget, spice) with buttons or typed answers, 50-dish local dataset (`data/foods.csv`), recommendation cards, smart fallback alternatives, new picks, change preferences, reset, session state.

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```
## Test the engine
```
python test_engine.py && python test_nlu.py && python test_app_logic.py
```
## Deploy on Streamlit Community Cloud
1. Push this folder to a GitHub repo.
2. At share.streamlit.io choose **New app**, select the repo, branch `main`, main file `app.py`, then Deploy.
