from jumbodb import JumboDB
import spacy
from verbsOfAttribution import verbsOA
import os

# TODOS:
# Expand list of people (Deval Patrick, Beto O'Rourke, ...)
# Expand list of topics (election 2018, ...)


class Shepherd(object):
    def __init__(self):
        self.jdb = JumboDB()
        self.nlp = spacy.load("en_coref_md")
        self.peopleList = [(p["first_name"], p["last_name"], p["role"], p["state"], p["ranking_role"]) for p in self.jdb.getAll("people")]
        self.flatPeopleList = self.prepPeopleList()
        self.topicList = [t["topic"] for t in self.jdb.getAll("topics")]
        self.verbsOfAttribution = verbsOA
        self.presentArticle()

    def prepPeopleList(self):
        stopList = ["of", "the", "to"]
        peopleSplat = [value for personVals in self.peopleList for value in personVals if value != None]
        peopleDeepSplat = [word for strng in peopleSplat for word in strng.split(" ") if word not in stopList]
        return list(set(peopleDeepSplat))

    def presentArticle(self):
        self.snippetList = []
        print("\n\n=====================================\n\n")
        article = self.jdb.getUnshepherdedArticle()
        if article == None:
            print("There aren't any articles to present.")
            return False
        print(article["article_body"])
        print("=====================================\n")
        self.selectMethod(article)

    def selectMethod(self, article):
        method = input("Do you want to (b)rowse the full article or let Shepherd (g)uess? (b / g): ")
        if method == "b":
            self.requestSnippets(article)
        else:
            self.smartSuggest(article)

    def requestSnippets(self, article):
        # get the quote
        snippet = self.requestWith("Are there any snippets in this article worth storing?")
        if not snippet or snippet == "s":
            self.wrapUp(article)
            self.requestQuotes()
            return False
        snippet = {
            "snippet": snippet,
            "person_id": 0,
            "topic_id": 0,
            "source_id": article[id],
            "approved": 1,
            "deleted": 0,
            "is_quote": 0
        }

        # is this a quote?
        quoteCheck = self.requestWith("Is this a quote or a non-quote snippet for training?")
        if not quoteCheck or quoteCheck == "c":
            self.wrapUp(article)
            self.requestQuotes()
            return False
        snippet["is_quote"] = 1 if quoteCheck == "y" else 0

        # get the speaker
        speaker_id = self.requestWith("Who is the speaker of the quote (give the id)?")
        if speaker_id == "c" or (speaker_id and self.jdb.getOne("people", speaker_id) == None):
            self.wrapUp(article)
            self.requestQuotes()
            return False
        snippet["person_id"] = speaker_id

        # get the topic
        topic_id = self.requestWith("What's the topic (give the id)?")
        if topic_id == "c" or (topic_id and self.jdb.getOne("topics", topic_id) == None):
            self.wrapUp(article)
            self.requestQuotes()
            return False
        snippet["topic_id"] = topic_id
        self.snippetList.append(quote)
        self.requestSnippets()

    def wrapUp(self, article):
        self.saveQuotes()
        self.jdb.markArticleShepherded(article)
        self.presentArticle()

    def saveQuotes(self):
        for snippet in self.snippetList:
            self.jdb.create("snippets", snippet)

    def smartSuggest(self, article):
        if article == None:
            print("No more articles!")
            return False
        print("=====================================\n")
        print("NEW ARTICLE!")
        print("=====================================\n")
        print(article["article_body"])
        print("=====================================\n")
        sa = self.nlp(article["article_body"])
        sourceSentences = list(sa.sents)
        article["corefed_body"] = sa._.coref_resolved
        corefSA = self.nlp(article["corefed_body"])
        corefSentences = list(corefSA.sents)
        # interestingSents = [sent for sent in corefSentences if self.interestingSnippetCheck(sent)]
        interestingSents = [sent for sent in sourceSentences if self.interestingSnippetCheck(sent)]
        for sent in interestingSents:
            os.system("cls" if os.name == "nt" else "clear")
            print("=====================================\n")
            print(sent)
            print("=====================================\n")
            response = self.requestWith("Does this look like a quote? (y/n -- or leave blank to discard) ")
            if response == "y" or response == "n": # second one is "no but save"
                # confirm followup questions about topic_id / person_id
                # store the snippet
                type = "quote" if response == "y" else "non_quote"
                person_id = self.requestWith("Which person is the speaker (enter id or leave blank for null): ")
                topic_id = self.requestWith("What's the topic (enter id or leave blank for null): ")
                # self.storeSnippetFromSpacy(sourceSentences[corefSentences.index(sent)], article, person_id, topic_id, type)
                self.storeSnippetFromSpacy(sent, article, person_id, topic_id, type)
        self.jdb.markArticleShepherded(article)
        self.smartSuggest(self.jdb.getUnshepherdedArticle())

    def storeSnippetFromSpacy(self, sentence, article, person_id=None, topic_id=None, type="quote"):
        snippet = {
            "snippet": sentence.text,
            "person_id": person_id,
            "topic_id": topic_id,
            "source_id": article["id"],
            "approved": 1,
            "deleted": 0,
            "is_quote": 1 if type == "quote" else 0
        }
        return self.jdb.create("snippets", snippet)

    def interestingSnippetCheck(self, spacyText):
        return self.personOfInterestCheck(spacyText) and (self.verbMatch(spacyText) or self.quoteCheck(spacyText))

    def verbMatch(self, spacyText):
        keyLemmas = [word.lemma_ for word in spacyText if word.pos_ == "VERB"]
        # TODO: mutate all words in the match list to the lemma forms
        matches = [word for word in keyLemmas if word in self.verbsOfAttribution]
        return len(matches) > 0

    def quoteCheck(self, spacyText):
        quoteTokens = [token for token in spacyText if token.is_quote]
        return len(quoteTokens) > 0

    def personOfInterestCheck(self, spacyText):
        matches = [word.text for word in spacyText if word.text in self.flatPeopleList]
        return len(matches) > 0

    def requestWith(self, prompt):
        print(prompt)
        pi = input("(for help or other: type none if none left, t for topics list, and p for people list): ")
        if pi == "none":
            return None
        elif pi == "t":
            self.printTopics()
            return self.requestWith(prompt)
        elif pi == "p":
            self.printPeople()
            return self.requestWith(prompt)
        return pi

    def printTopics(self):
        topics = self.jdb.getAll("topics")
        print("Topic list:")
        for topic in topics:
            print(topic["topic"] + ": " + str(topic["id"]))
        print("==============")

    def printPeople(self):
        people = self.jdb.getAll("people")
        print("People list:")
        for person in people:
            print(person["first_name"] + " " + person["last_name"] + ": " + str(person["id"]))
        print("==============")

if __name__ == "__main__":
    s = Shepherd()
