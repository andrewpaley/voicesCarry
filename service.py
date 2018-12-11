import flask
from flask import request, jsonify
from flask import Blueprint
from grok import Grok
from cleaner import theCleaner
import json

g = Grok()
cleaner = theCleaner()

api = Blueprint('api', __name__)

@api.route('/api', methods=['GET'])
def home():
    return '{status: "ok"}'

@api.route('/api/get_article', methods=['POST'])
def getArticle():
    url = request.form["url"]
    guesses = g.grokStory(url)
    payload = convertGuessesToJSON(guesses, g.latestArticle)
    # breakpoint()
    return payload

@api.route('/api/create_snippet', methods=['POST'])
def createSnippet():
    snippet = request.form["snippet"]
    article = {"id": request.form["articleID"]}
    type = request.form["type"] # either quote, nonquote or paraphrase
    storedSnippet = g.storeSnippet(snippet, article, type=type, approved=0)
    # breakpoint()
    return json.dumps(storedSnippet)

# helper functions for inputs/outputs over the wire
def convertGuessesToJSON(guesses, article):
    output = {
        "guesses": [],
        "articleText": cleaner.cleanUpString(article["article_body"]),
        "articleTitle": cleaner.cleanUpString(article["article_title"]),
        "articleID": article["id"]
    }
    for guess in guesses:
        gues = {
            "guess": guess[1].text,
            "certainty": guess[0]
        }
        output["guesses"].append(gues)
    return json.dumps(output)
