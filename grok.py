import json
from datetime import datetime, timedelta
from pprint import pprint as pp
from jumbodb import JumboDB
from teacher import Teacher
from cleaner import theCleaner
from trunk import Trunk
import spacy
import sys

class Grok(object):
    def __init__(self, url=None):
        self.latestURL = url
        self.nlp = spacy.load("en")
        self.trunk = Trunk()
        self.cleaner = theCleaner()
        # get and set up teacher
        self.teacher = Teacher()
        self.teacher.loadSavedQuoteClassifier()
        self.jdb = JumboDB()
        # now a flag that can be toggled to do NONQUOTES for data collection
        self.collectQuotes = True

    def getStory(self, repeat=False):
        url = self.latestURL
        if not url:
            requestStr = "Give me a URL to ingest from: "
            if repeat == True: requestStr = "No, really. A URL please: "
            url = input(requestStr)
        if url:
            self.latestURL = url
            self.latestGuesses = self.grokStory(url)
            self.reviewGuesses()
        else:
            self.requestStory(True)

    def getSnippet(self):
        inputt = input("Give a sentence to classify: ")
        result = g.teacher.classifySnippet(inputt)
        print(result)
        self.getSnippet()

    def grokStory(self, url):
        if url != self.latestURL: self.latestURL = url
        self.latestArticle = self.trunk.getStoryByURL(url)
        if not self.latestArticle: return []

        self.latestStoryChunks = self.generateStoryChunkCandidates(self.latestArticle)
        quoteGuesses = []
        for snippet in self.latestStoryChunks:
            # representation = self.cleaner.createRepresentation(snippet.text)
            prediction = self.teacher.classifySnippet(snippet.text)
            if prediction["QUOTE"] > 0.5 and self.collectQuotes == True:
                # return it with the clean text version (?)
                quoteGuesses.append((prediction["QUOTE"], snippet))
            elif prediction["QUOTE"] < 0.5 and self.collectQuotes == False:
                quoteGuesses.append((prediction["QUOTE"], snippet))
        self.latestGuesses = quoteGuesses
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
                quoteCount = self.cleaner.cleanUpString(sentence.text).count('"')
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

    # def storeGuesses(self):
    #     storedGuesses = []
    #     for guess in self.latestGuesses:
    #         storedGuesses.append(self.storeSnippet(guess[1], self.latestArticle))
    #     return storedGuesses

    def reviewGuesses(self): # this is the command line version -- otherwise this would be behind an API
        for i, guess in enumerate(self.latestGuesses):
            self.confirmQuote(guess)

    def confirmQuote(self, guess): # part two of command-line-only version
        print("==========")
        print("QUOTE FOUND:")
        print(guess[1])
        print("Is-quote certainty: " + str(guess[0]))
        print("==========")
        confirmation = input("Is this actually a quote? (y/n) (or d to 'discard'): ")
        if not confirmation:
            self.confirmQuote(guess)
            return False
        elif confirmation == "n":
            self.storeSnippet(guess[1], self.latestArticle, type="nonquote")
            # self.toggleGuess(storedGuess)
        elif confirmation == "p":
            self.storeSnippet(guess[1], self.latestArticle, type="paraphrase")
            # self.toggleToParaphrase(storedGuess)
        elif confirmation == "y":
            self.storeSnippet(guess[1], self.latestArticle, type="quote")
        else:
            return True

    def storeSnippet(self, sentence, article, person_id=None, topic_id=None, type="quote", approved=1):
        if not isinstance(sentence, str): sentence = sentence.text
        snippet = {
            "snippet": sentence,
            "person_id": person_id,
            "topic_id": topic_id,
            "source_id": article["id"],
            "approved": approved,
            "deleted": 0,
            "is_quote": 1 if type == "quote" else 0,
            "is_paraphrase": 1 if type == "paraphrase" else 0
        }
        return self.jdb.create("snippets", snippet)


if __name__ == "__main__":
    if "-a" in sys.argv:
        aindex = sys.argv.index("-a")
        g = Grok(sys.argv[aindex+1])
        if "-nonquotes" in sys.argv: g.collectQuotes = False
        g.getStory()
    elif "-t" in sys.argv:
        g = Grok()
        g.getSnippet()
    else:
        g = Grok()
        g.getStory()
