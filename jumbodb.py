import sqlite3
from newsapi import NewsApiClient
from collections import OrderedDict
import json
from datetime import datetime, timedelta
from pprint import pprint as pp
from random import randint
from time import sleep

# eventually this next thing will be useless, but for training, these are the people to return:
peopleForTraining = [
    {"first_name": "Elizabeth", "last_name": "Warren" , "party": "D"},
    {"first_name": "Bernard", "last_name": "Sanders" , "party": "D"},
    {"first_name": "Donald", "last_name": "Trump" , "party": "R"},
    {"first_name": "Sarah", "last_name": "Huckabee Sanders" , "party": "R"},
    {"first_name": "Marco", "last_name": "Rubio" , "party": "R"},
    {"first_name": "Lisa", "last_name": "Murkowski" , "party": "R"},
    {"first_name": "Mitch", "last_name": "McConnell" , "party": "R"},
    {"first_name": "Ted", "last_name": "Cruz" , "party": "R"},
    {"first_name": "Maxine", "last_name": "Waters" , "party": "D"},
    {"first_name": "Nancy", "last_name": "Pelosi" , "party": "D"},
    {"first_name": "Paul", "last_name": "Ryan" , "party": "R"},
]


class JumboDB(object):
    def __init__(self, db="horton.db"):
        self.db = db
        self.conn = None
        self.c = None
        self.personSchema = OrderedDict({
            "first_name": "",
            "last_name": "",
            "party": "",
            "state": "",
            "district": "",
            "role": "",
            "ranking_role": "",
            "in_office": 1,
            "member_of": "",
            "gender": "",
            "twitter": "",
            "birthdate": "",
            "deleted": 0
        })
        self.articlePersonSchema = OrderedDict({
            "article_id": "",
            "person_id": ""
        })
        self.topicSchema = OrderedDict({
            "topic": "",
            "additional_terms": ""
        })
        self.articleTopicSchema = OrderedDict({
            "article_id": "",
            "topic_id": ""
        })
        self.articleSchema = OrderedDict({
            "article_title": "",
            "article_description": "",
            "article_summary": "",
            "article_body": "",
            "source_name": "",
            "source_link": "",
            "published_date": "",
            "approved": 0,
            "extracted": 0,
            "discarded": 0
        })
        self.tableSchemaMap = {
            "people": self.personSchema,
            "article_person": self.articlePersonSchema,
            "article_topic": self.articleTopicSchema,
            "topics": self.topicSchema,
            "articles": self.articleSchema
        }
        self.uniqueKeyMap = {
            "people": ["first_name", "last_name", "party"],
            "topics": ["topic"],
            "articles": ["source_link"],
            "article_topic": ["article_id", "topic_id"],
            "article_person": ["article_id", "person_id"]
        }

    def _schemaResolver(self, schema, payload):
        # takes a schema and a dict of values and combines them to get an ordered dict
        # safe guarded by getting the scema from the internal representation
        output = OrderedDict()
        for key, val in schema.items():
            if key in payload:
                output[key] = payload[key]
        return output

    def _queryToJSON(self, cursor, one=False):
        r = [dict((cursor.description[i][0], value) \
          for i, value in enumerate(row)) for row in cursor.fetchall()]
        return (r[0] if r else None) if one else r

    def _openDatabase(self):
        if self.conn:
            return False
        self.conn = sqlite3.connect(self.db)
        self.c = self.conn.cursor()
        return self.c

    def _closeDatabase(self):
        if not self.conn:
            return False
        self.conn.commit()
        self.conn.close()
        self.conn = None

    def _createRow(self, tn):
        self._openDatabase()
        self.c.execute("INSERT INTO "+tn+" DEFAULT VALUES")
        return self.c.lastrowid

    def _numberValCheck(self, x):
        try:
            return 0 == x*0
        except:
            return False

    def _existanceCheck(self, tn, vals):
        exists = False
        keys = self.uniqueKeyMap[tn]
        matchVals = {}
        for key in keys:
            matchVals[key] = vals[key]
        matchSet = self.find(tn, matchVals)
        if len(matchSet) > 0: exists = True
        return exists, matchSet

    # public functions
    def batchCreate(self, type, listOfLists):
        for row in listOfLists:
            self.create(type, row)

    def getAll(self, tn):
        if tn == "people":
            return self.trainingPeopleOnly()
        self._openDatabase()
        loadedCursor = self.c.execute("SELECT * FROM "+tn)
        payload = self._queryToJSON(loadedCursor)
        self._closeDatabase()
        return payload

    def trainingPeopleOnly(self):
        # HACK! TEMPORARY!
        # This is a hack for early development
        # Eventually we'll cover all people
        # Until then, let's focus on a few key figures
        # Do this as db query results so no one else has to care this is different
        global peopleForTraining
        foundPeople = []
        for personInfo in peopleForTraining:
            foundPerson = self.find("people", personInfo)
            if foundPerson:
                foundPeople.append(foundPerson[0])
        return foundPeople

    def getOne(self, tn, id):
        if not id: return False
        self._openDatabase()
        loadedCursor = self.c.execute("SELECT * FROM "+tn+" WHERE id="+str(id))
        payload = self._queryToJSON(loadedCursor, True)
        self._closeDatabase()
        return payload

    def find(self, tn, vals):
        if not id: return False
        self._openDatabase()
        queryStr = "SELECT * FROM "+tn+" WHERE "
        counter = 0
        valList = []
        for key, val in vals.items():
            queryStr += key + "=?"
            valList.append(val)
            if counter < len(vals)-1: queryStr += " AND "
            counter += 1
        loadedCursor = self.c.execute(queryStr, tuple(valList))
        payload = self._queryToJSON(loadedCursor)
        self._closeDatabase()
        return payload

    def create(self, tn, vals):
        if not vals: return False
        self._openDatabase()
        exists, matchSet = self._existanceCheck(tn, vals)
        if exists == True:
            # TODO: maybe also flip deleted to false if it's been deleted but is trying to be recreated?
            return matchSet[0]
        newId = self._createRow(tn)
        return self.update(tn, newId, vals)

    def delete(self, tn, id):
        if not id: return False
        # not a real delete so much as a demotion
        return self.update(tn, id, {"deleted": 1})

    def update(self, tn, id, vals={}):
        if not id: return False
        self._openDatabase()
        # vals can be partial updates
        schema = self.tableSchemaMap[tn]
        schemaed = self._schemaResolver(schema, vals)
        for key, val in schemaed.items():
            updateStr = "UPDATE "+tn+" SET "+key+"=(?) WHERE id=(?)"
            self.c.execute(updateStr, (val, id))
            self.conn.commit()
        self._closeDatabase()
        return self.getOne(tn, id)

    # convenience functions for standard stuff
    def linkArticleAndPerson(self, aid, pid):
        result = self.create("article_person", {"article_id": aid, "person_id": pid})
        return result

    def linkArticleAndTopic(self, aid, tid):
        result = self.create("article_topic", {"article_id": aid, "topic_id": tid})
        return result

    def getTopicsByArticle(self, aid):
        rows = self.find("article_topic", {"article_id": aid})
        topics = []
        for row in rows:
            topics.append(self.getOne("topics", row["topic_id"]))
        return topics

    def getPeopleByArticle(self, aid):
        rows = self.find("article_person", {"article_id": aid})
        people = []
        for row in rows:
            people.append(self.getOne("people", row["person_id"]))
        return people

    def getArticlesByTopic(self, tid):
        rows = self.find("article_topic", {"topic_id": tid})
        articles = []
        for row in rows:
            articles.append(self.getOne("articles", row["article_id"]))
        return articles

    def getArticlesByPerson(self, pid):
        rows = self.find("article_person", {"person_id": pid})
        articles = []
        for row in rows:
            people.append(self.getOne("people", row["article_id"]))
        return articles

# a helper object for querying/loading stories into JumboDB
class Trunk(object):
    def __init__(self):
        self.newsapi = NewsApiClient(api_key='b9faafb8977145a8a9a32d797792dc65')
        self.jdb = JumboDB()

        self.keywordSets = self.buildOutQuerySets()

    def loadDataFromLastTwoDays(self):
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
        for keywordSet in self.keywordSets:
            self.loadStoriesFor(self.queryBuilder(keywordSet), keywordSet, yesterday, today)
            # don't overload the api...sleep for 1 to 3 seconds between each call
            sleep(randint(1,3))

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
        stories = self.getStoriesFor(query, from_date, to_date)
        for story in stories["articles"]:
            story = self.translateSchemaOfStory(story)
            article = self.jdb.create("articles", story)
            self.createLinksToArticle(keywordSet, article)

    def getStoriesFor(self, query, from_date, to_date):
        # date format is like 2018-10-12
        return self.newsapi.get_everything(q=query, from_param=from_date, to=to_date, language='en', sort_by='relevancy')

    def translateSchemaOfStory(self, story):
        outputStory = {}
        outputStory["article_title"] = story["title"]
        outputStory["article_description"] = story["description"]
        outputStory["article_summary"] = story["content"]
        outputStory["article_body"] = ""
        outputStory["source_name"] = story["source"]["name"]
        outputStory["source_link"] = story["url"]
        outputStory["published_date"] = story["publishedAt"]
        return outputStory

    def createLinksToArticle(self, keywordSet, article):
        topicId = keywordSet["topic_details"]["id"]
        self.jdb.linkArticleAndTopic(article["id"], topicId)

        person = self.jdb.find("people",keywordSet["person_details"])
        if not person: return False
        personId = person[0]["id"]
        self.jdb.linkArticleAndPerson(article["id"], personId)
