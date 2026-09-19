"""Fun API commands."""
from ..api.jokes import fetch_joke
from ..api.quotes import fetch_advice
from ..api.facts import fetch_fact
from ..api.trivia import fetch_bored_activity, fetch_yesno
from ..api.topics import fetch_recipe

def get_advice_card():
    return fetch_advice()

def get_joke_card():
    return fetch_joke()

def get_fact_card():
    return fetch_fact()

def get_bored_card():
    return fetch_bored_activity()

def get_yesno_card():
    return fetch_yesno()

def get_recipe_card():
    return fetch_recipe()
