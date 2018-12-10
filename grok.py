import json
from datetime import datetime, timedelta
from pprint import pprint as pp
from jumbodb import JumboDB
import spacy

class Grok(object):
    def __init__(self):
        self.jdb = JumboDB()
        self.snlp = spacy.load("en_coref_md")
        # self.cnlp = corenlp.CoreNLPClient(annotators=cnlpAnnotators.split())
        self.snippetSchema = {
            "snippet":"", # text of snippet
            "article_id": 0, # articleID
            "person_id": 0, # speaker
            "topic_id": 0, # topicID
            "generated_by": "" # coreNLP, Spacy/Regex,
        }

    def getUngroked(self,count=10):
        # get articles to count
        self.rawArticles = self.jdb.find("articles", {"groked": 0}, count)
        self.grokArticles()
        return articles

    def grokArticles(self):
        # do the initial processing on the articles to provide to review UI
        self.pArtciles = []
        for article in self.rawArticles:
            self.pArtciles.append(self.grokArticle(article))

    def informedGrokArticles(self):
        # a placeholder for the future "smart grok"
        # basically the goal of this project
        return False

    def grokArticle(self, article):
        article["snippets"] = []
        # get quote snippets from coreNLP
        # UGH.

        # now set up to do get paraphrasing via some spacy and other magic
        sa = self.snlp(article["article_body"])
        article["corefed_body"] = a._.coref_resolved
        # this where you stopped
        # next up: dependency tree parsing
