from newsapi import NewsApiClient
import json
from datetime import datetime, timedelta
from pprint import pprint as pp
from random import randint
from time import sleep
from newspaper import Article
import os
from jumbodb import JumboDB

newsAPIKey = os.getenv("newsAPIKey")

# a helper object for querying/loading stories into JumboDB
class Trunk(object):
    def __init__(self):
        self.newsapi = NewsApiClient(api_key=newsAPIKey)
        self.jdb = JumboDB()
        self.keywordSets = self.buildOutQuerySets()

    def print(self, statement):
        print(statement)

    def suckUp(self, timeFrame="lastTwoDays"):
        if timeFrame == "lastTwoDays":
            self.loadDataFromLastTwoDays()

    def loadDataFromLastTwoDays(self):
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
        for keywordSet in self.keywordSets:
        # for keywordSet in self.keywordSets[0:1]:
            self.loadStoriesFor(self.queryBuilder(keywordSet), keywordSet, yesterday, today)
            # don't overload the api...sleep for 1 to 3 seconds between each call
            # sleep(randint(0,1))

    def loadDataSinceLastRun(self):
        # TODO: find the last date there are articles for in the articles table, and run all the days since then
        return False

    def buildOutQuerySets(self):
        topics = self.jdb.getAll("topics")
        people = self.jdb.getAll("people")
        querySet = []
        for person in people:
            pstring = person["first_name"]+" "+person["last_name"]
            for topic in topics:
                querySet.append({"person_name": pstring, "topic": topic["topic"], "person_details": person, "topic_details": topic})
        return querySet

    def queryBuilder(self, keywords):
        query = ""
        for key, value in keywords.items():
            if key != "person_details" and key != "topic_details":
                query += '&"'+value+'"'
        return query

    def loadStoriesFor(self, query, keywordSet, from_date, to_date):
        self.print("\n\n ============================================== \n\n")
        self.print("Getting stories for: "+str(query))
        stories = self.getStoriesFor(query, from_date, to_date)
        self.print("Got this many stories for "+str(query)+": "+str(len(stories)))
        if not stories: return None
        for story in stories:
            if story["article_body"] != "" and story["url"] != None:
                story = self.translateSchemaOfStory(story)
                article = self.jdb.create("articles", story)
                self.createLinksToArticle(keywordSet, article)

    def getStoriesFor(self, query, from_date, to_date):
        # date format is like 2018-10-12
        payload = self.queryNewsAPI(query, from_date, to_date)
        if not payload: return None
        payload = payload["articles"]
        self.print("In total, I got this many stories: "+str(len(payload)))
        self.print("now getting full text for each story...")
        for story in payload:
            # sleep(randint(0,1))
            story["article_body"] = self.getFullStory(story["url"])
        return payload

    def getFullStory(self, url):
        self.print("Seeing if I have full story for: "+str(url))
        # first, see if we already have this article
        # if so, just return it and the create call downstream will prevent duplication
        matches = self.jdb.find("articles", {"source_link": url})
        if len(matches) > 0:
            self.print("I already have a story for this link. No call to the api necessary.")
            return matches[0]["article_body"]
        try:
            self.print("Don't already have the full story...will try to get it...")
            article = Article(url)
            article.download()
            article.parse()
            self.print("...got it!")
            return article.text
        except:
            self.print("...didn't get it. Moving on!")
            return ""

    def translateSchemaOfStory(self, story):
        outputStory = {}
        outputStory["article_title"] = story["title"]
        outputStory["article_description"] = story["description"]
        outputStory["article_summary"] = story["content"]
        outputStory["article_body"] = story["article_body"]
        outputStory["source_name"] = story["source"]["name"]
        outputStory["source_link"] = story["url"]
        outputStory["published_date"] = story["publishedAt"]
        return outputStory

    def queryNewsAPI(self, query, from_date, to_date):
        # check the cached_newsapi_queries table to see if you already have results for this one
        self.print("Going to return some stories about: "+str(query)+" between "+str(from_date)+" and "+str(to_date))
        self.print("First off, do I already have them?")
        existingPayloads = self.jdb.find("cached_newsapi_queries", {"query": query, "from_date": from_date, "to_date": to_date})
        if FORCE_NEWSAPI_REFRESH == False and len(existingPayloads) > 0 and existingPayloads[0]["payload"] != None:
            self.print("I do! I won't bother calling the api then.")
            return json.loads(existingPayloads[0]["payload"])
        self.print("Either I don't, or I'm being told to force a refresh...here we go...")
        try:
            self.print("Calling NewsAPI...")
            newPayload = self.newsapi.get_everything(q=query, from_param=from_date, to=to_date, language='en', sort_by='relevancy')
        except:
            self.print("NewsAPI failed for some reason...moving on!")
            return None
        self.print("Got stuff back from NewsAPI!")
        if len(existingPayloads) > 0:
            # update the existing result rather than make a new entry
            self.jdb.update("cached_newsapi_queries", existingPayloads[0]["id"], {"payload": json.dumps(newPayload)})
        else:
            self.jdb.create("cached_newsapi_queries", {"query": query, "from_date": from_date, "to_date": to_date, "payload": json.dumps(newPayload)})
        return newPayload

    def createLinksToArticle(self, keywordSet, article):
        topicId = keywordSet["topic_details"]["id"]
        self.jdb.linkArticleAndTopic(article["id"], topicId)
        personId = keywordSet["person_details"]["id"]
        self.jdb.linkArticleAndPerson(article["id"], personId)
