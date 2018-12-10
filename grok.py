import json
from datetime import datetime, timedelta
from pprint import pprint as pp
from jumbodb import JumboDB
from teacher import Teacher
from trunk import Trunk
import spacy
import sys

class Grok(object):
    def __init__(self, url=None):
        self.latestURL = url
        self.nlp = spacy.load("en_coref_md")
        self.trunk = Trunk()
        # get and set up teacher
        self.teacher = Teacher()
        self.teacher.loadSavedQuoteClassifier()
        self.jdb = JumboDB()
        # let's do this
        self.getStory()

    def getStory(self, repeat=False):
        url = self.latestURL
        if not url:
            requestStr = "Give me a URL to ingest from: "
            if repeat == True: requestStr = "No, really. A URL please: "
            url = input(requestStr)
        if url:
            self.latestURL = url
            self.latestGuesses = self.grokStory(url)
            self.storedGuesses = self.storeGuesses()
            self.reviewGuesses()
        else:
            self.requestStory(True)

    def grokStory(self, url):
        self.latestArticle = self.trunk.getStoryByURL(url)
        self.latestStoryChunks = self.generateStoryChunkCandidates(self.latestArticle)
        quoteGuesses = []
        for snippet in self.latestStoryChunks:
            representation = self.teacher.createRepresentation(snippet.text)
            prediction = self.teacher.classifySnippet(representation)
            if prediction["QUOTE"] > 0.5:
                # return it with the clean text version (?)
                quoteGuesses.append((prediction["QUOTE"], snippet))
        return quoteGuesses

    def generateStoryChunkCandidates(self, article):
        sa = self.nlp(article["article_body"])
        sourceSentences = list(sa.sents)
        # bundle them up so we aren't weirdly splitting quotes
        sourceSentences = self.chunkSentencesByQuote(sourceSentences)
        return sourceSentences

    def chunkSentencesByQuote(self, sentences):
        # TODO: move this to grok later
        outputSentences = []
        withinQuote = False
        compoundQuote = ""
        for sentence in sentences:
            quoteTokens = [token for token in sentence if token.is_quote and token.text != "'"]
            quoteTokenCount = len(quoteTokens)
            if quoteTokenCount % 2 != 0 and withinQuote == False:
                # double check
                quoteCount = self.teacher.cleanUpString(sentence.text).count('"')
                if quoteCount % 2 == 0:
                    outputSentences.append(sentence)
                else:
                    compoundQuote += sentence.text
                    withinQuote = True
            elif quoteTokenCount == 0 and withinQuote == True:
                compoundQuote += " " + sentence.text
            elif quoteTokenCount % 2 != 0 and withinQuote == True:
                compoundQuote += " " + sentence.text
                newSent = self.nlp(compoundQuote)
                outputSentences.append(newSent)
                compoundQuote = ""
                withinQuote = False
            else:
                outputSentences.append(sentence)
        return outputSentences

    def storeGuesses(self):
        storedGuesses = []
        for guess in self.latestGuesses:
            storedGuesses.append(self.storeSnippet(guess[1], self.latestArticle))
        return storedGuesses

    def reviewGuesses(self): # this is the command line version -- otherwise this would be behind an API
        for i, guess in enumerate(self.latestGuesses):
            self.confirmQuote(guess, self.storedGuesses[i])

    def confirmQuote(self, guess, storedGuess): # part two of command-line-only version
        print("==========")
        print(guess[1])
        print(guess[0])
        print("==========")
        confirmation = input("Is this a quote? (y/n): ")
        if not confirmation:
            self.confirmQuote(guess, storedGuess)
            return False
        elif confirmation == "n":
            self.toggleGuess(storedGuess)
        elif confirmation == "p":
            self.toggleToParaphrase(storedGuess)
        else:
            return True

    def storeSnippet(self, sentence, article, person_id=None, topic_id=None, type="quote"):
        snippet = {
            "snippet": sentence.text,
            "person_id": person_id,
            "topic_id": topic_id,
            "source_id": article["id"],
            "approved": 1,
            "deleted": 0,
            "is_quote": 1 if type == "quote" else 0,
            "is_paraphrase": 1 if type == "paraphrase" else 0
        }
        return self.jdb.create("snippets", snippet)

    def toggleGuess(self, storedGuess, is_quote=0):
        self.jdb.update("snippets", storedGuess["id"], {"is_quote": is_quote})

    def toggleToParaphrase(self, storedGuess, is_paraphrase=1):
        self.jdb.update("snippets", storedGuess["id"], {"is_quote": 0, "is_paraphrase": 1})

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] in ["-a"]:
        g = Grok(sys.argv[2])
    else:
        g = Grok()
