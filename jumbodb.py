import sqlite3
from collections import OrderedDict
import json
from pprint import pprint as pp

# eventually this next thing will be useless, but for training, these are the people to return:
peopleForTraining = [
    {"first_name": "Elizabeth", "last_name": "Warren" , "party": "D"},
    {"first_name": "Joe", "last_name": "Biden" , "party": "D"},
    {"first_name": "Michael", "last_name": "Bloomberg" , "party": "D"},
    {"first_name": "Bernard", "last_name": "Sanders" , "party": "D"},
    {"first_name": "Donald", "last_name": "Trump" , "party": "R"},
    {"first_name": "Sarah", "last_name": "Huckabee Sanders" , "party": "R"},
    {"first_name": "Marco", "last_name": "Rubio" , "party": "R"},
    {"first_name": "Lisa", "last_name": "Murkowski" , "party": "R"},
    {"first_name": "Mitch", "last_name": "McConnell" , "party": "R"},
    {"first_name": "Ted", "last_name": "Cruz" , "party": "R"},
    {"first_name": "Maxine", "last_name": "Waters" , "party": "D"},
    {"first_name": "Adam", "last_name": "Schiff" , "party": "D"},
    {"first_name": "Sherrod", "last_name": "Brown" , "party": "D"},
    {"first_name": "Nancy", "last_name": "Pelosi" , "party": "D"},
    {"first_name": "Paul", "last_name": "Ryan" , "party": "R"},
    {"first_name": "Ocasio Cortez", "last_name": "Alexandria" , "party": "D"},
    {"first_name": "Kellyanne", "last_name": "Conway" , "party": "R"},
    {"first_name": "Barack", "last_name": "Obama" , "party": "D"},
    {"first_name": "George", "last_name": "Bush" , "party": "R"},
    {"first_name": "Rand", "last_name": "Paul" , "party": "R"},
    {"first_name": "James", "last_name": "Comey" , "party": "R"},
    {"first_name": "Michael", "last_name": "Cohen" , "party": "R"},
    {"first_name": "Chris", "last_name": "Christie" , "party": "R"},
    {"first_name": "Jeff", "last_name": "Flake" , "party": "R"},
    {"first_name": "Rudy", "last_name": "Giuliani" , "party": "R"},
    {"first_name": "White House", "last_name": "Spokesperson" , "party": "R"},
    {"first_name": "Jared", "last_name": "Kushner" , "party": "R"},
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
            "groked": 0,
            "discarded": 0,
            "shepherded": 0
        })
        self.roughSnippetSchema = OrderedDict({
            "snippet": "",
            "person_id": "",
            "topic_id": "",
            "source_id": "",
            "reviewed": 0,
            "approved": 0,
            "deleted": 0
        })
        self.trainingSnippetSchema = OrderedDict({
            "snippet": "",
            "person_id": "",
            "topic_id": "",
            "source_id": "",
            "generated_by": "",
            "approved": 0,
            "deleted": 0
        })
        self.snippetSchema = OrderedDict({
            "snippet": "",
            "person_id": "",
            "topic_id": "",
            "source_id": "",
            "approved": 0,
            "deleted": 0,
            "is_quote": 0
        })
        self.cachedNewsAPIQueriesSchema = OrderedDict({
            "query": "",
            "from_date": "",
            "to_date": "",
            "payload": ""
        })
        self.tableSchemaMap = {
            "people": self.personSchema,
            "article_person": self.articlePersonSchema,
            "article_topic": self.articleTopicSchema,
            "topics": self.topicSchema,
            "articles": self.articleSchema,
            "rough_snippets": self.roughSnippetSchema,
            "training_snippets": self.trainingSnippetSchema,
            "snippets": self.snippetSchema,
            "cached_newsapi_queries": self.cachedNewsAPIQueriesSchema
        }
        self.uniqueKeyMap = {
            "people": ["first_name", "last_name", "party"],
            "topics": ["topic"],
            "articles": ["source_link", "article_body"],
            "article_topic": ["article_id", "topic_id"],
            "article_person": ["article_id", "person_id"],
            "rough_snippets": ["snippet","person_id","topic_id","source_id"],
            "training_snippets": ["snippet","person_id","topic_id","source_id","generated_by"],
            "snippets": ["snippet","person_id","topic_id","source_id"],
            "cached_newsapi_queries": ["query", "from_date", "to_date"]
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
        if tn == "articles":
            return self._articleExistanceCheck(vals)
        exists = False
        keys = self.uniqueKeyMap[tn]
        matchVals = {}
        for key in keys:
            matchVals[key] = vals[key]
        matchSet = self.find(tn, matchVals)
        if len(matchSet) > 0: exists = True
        return exists, matchSet

    def _articleExistanceCheck(self, vals):
        # special case -- first check source_link, then check article_summary
        # even if we have it from another publication, it might be the same content cause of syndication
        # thus, just return the story we already have rather than write a new one to the db from a different url
        matchSet1 = self.find("articles", {"source_link": vals["source_link"]})
        if len(matchSet1) > 0: return True, matchSet1
        matchSet2 = self.find("articles", {"article_body": vals["article_body"]})
        if len(matchSet2) > 0: return True, matchSet2
        return False, []

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

    def find(self, tn, vals=None, maxResults=None, mostRecent=False):
        if not id: return False
        self._openDatabase()
        if not vals:
            queryStr = "SELECT * FROM "+tn
            loadedCursor = self.c.execute(queryStr)
        else:
            cleanedVals = {}
            for key, val in vals.items():
                if val != None:
                    cleanedVals[key] = val
            queryStr = "SELECT * FROM "+tn+" WHERE "
            counter = 0
            valList = []
            for key, val in cleanedVals.items():
                queryStr += key + "=?"
                valList.append(val)
                if counter < len(cleanedVals)-1: queryStr += " AND "
                counter += 1
            if mostRecent == True: # this should only ever hit for articles, at least for now
                queryStr += " order by published_date desc"
            if maxResults:
                queryStr += " limit "+str(maxResults)
            try:
                loadedCursor = self.c.execute(queryStr, tuple(valList))
            except:
                breakpoint()
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
            articles.append(self.getOne("articles", row["article_id"]))
        return articles

    # and now, a ton of convenience functions:

    def getCountOf(self, tn, vals=None):
        return len(self.find(tn, vals))

    def getCountOfArticles(self):
        return self.getCountOf("articles")

    def getCountOfGoodSnippets(self):
        return self.getCountOf("snippets")

    def getCountOfRoughSnippets(self):
        return self.getCountOf("rough_snippets")

    def getCountOfDiscardedArticles(self):
        return self.getCountOf("articles", {"discarded": 1})

    def getCountOfGrokedArticles(self):
        return self.getCountOf("articles", {"groked": 1})

    def getCountOfShepherdedArticles(self):
        return self.getCountOf("articles", {"shepherded": 1})

    def markArticleShepherded(self, article):
        return self.update("articles", article["id"], {"shepherded": 1})

    def getUnshepherdedArticle(self):
        arts = self.find("articles", {"shepherded": 0}, 1, True)
        if arts:
            return arts[0]
        else:
            return None
