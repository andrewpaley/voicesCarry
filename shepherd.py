from jumbodb import JumboDB
from trunk import Trunk
from teacher import Teacher
from grok import Grok
import spacy
from verbsOfAttribution import verbsOA
import os
import sys

class Shepherd(object):
    def __init__(self):
        self.jdb = JumboDB()
        self.nlp = spacy.load("en_coref_md")
        self.peopleList = [(p["first_name"], p["last_name"], p["role"], p["state"], p["ranking_role"]) for p in self.jdb.getAll("people")]
        self.flatPeopleList = self.prepPeopleList()
        self.topicList = [t["topic"] for t in self.jdb.getAll("topics")]
        self.verbsOfAttribution = verbsOA
        self.teacher = Teacher()
        self.trunk = None
        self.grok = Grok()

    def prepPeopleList(self):
        stopList = ["of", "the", "to"]
        peopleSplat = [value for personVals in self.peopleList for value in personVals if value != None]
        peopleDeepSplat = [word for strng in peopleSplat for word in strng.split(" ") if word not in stopList]
        return list(set(peopleDeepSplat))

    def presentArticle(self, article=None):
        self.snippetList = []
        print("\n\n=====================================\n\n")
        if not article: article = self.jdb.getUnshepherdedArticle()
        if article == None:
            print("There aren't any articles to present.")
            return False
        print(article["article_body"])
        print("=====================================\n")
        self.selectMethod(article)

    def selectMethod(self, article):
        method = input("Do you want to browse the full article, have Shepherd guess with Teacher's help? (browse / guess): ")
        if method == "guess":
            self.guessAndSuggest(article)
        # elif method == "teacher":
        #     self.guessAndSuggest(article, smart=True)
        elif method == "aa":
            url = input("Ah, give me a URL to ingest from: ")
            self.trunkUp(url)
        else:
            self.requestSnippets(article)

    def requestSnippets(self, article):
        # get the quote
        print("\n\n=====================================\n\n")
        print(article["article_body"])
        print("=====================================\n")
        snippet = self.requestWith("Are there any snippets in this article worth storing?")
        if not snippet or snippet == "s":
            self.wrapUp(article)
            self.requestQuotes()
            return False
        snippet = {
            "snippet": snippet,
            "person_id": None,
            "topic_id": None,
            "source_id": article["id"],
            "approved": 1,
            "deleted": 0,
            "is_quote": 0,
            "is_paraphrase": 0
        }

        # is this a quote?
        quoteCheck = self.requestWith("Is this a quote? (if not, it'll be a non-quote snippet for training)")
        if not quoteCheck or quoteCheck == "c":
            self.wrapUp(article)
            self.requestQuotes()
            return False
        snippet["is_quote"] = 1 if quoteCheck == "y" else 0
        snippet["is_paraphrase"] = 1 if quoteCheck == "p" else 0
        if quoteCheck == "y" or quoteCheck == "p":
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
        self.snippetList.append(snippet)
        self.requestSnippets(article)

    def wrapUp(self, article):
        self.saveQuotes()
        self.jdb.markArticleShepherded(article)
        self.presentArticle()

    def saveQuotes(self):
        for snippet in self.snippetList:
            self.jdb.create("snippets", snippet)

    def guessAndSuggest_DEPRECATED(self, article, smart=False):
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
        if smart == True:
            interestingSents = [sent for sent in sourceSentences if self.classifySentence(sent)["QUOTE"] > 0.5]
        else:
            interestingSents = [sent for sent in sourceSentences if self.interestingSnippetCheck(sent)]
        interestingCoupledSentences = []
        for i, sent in enumerate(sourceSentences):
            if len(sourceSentences)-1 == i: continue
            coupledSent = sent.text + " " + sourceSentences[i+1].text
            coupledSent = self.nlp(coupledSent)
            if smart == True:
                if self.classifySentence(coupledSent)["QUOTE"] > 0.5: interestingCoupledSentences.append(coupledSent)
            else:
                if self.interestingSnippetCheck(coupledSent)["QUOTE"] > 0.5: interestingCoupledSentences.append(coupledSent)
        interestingSents.extend(interestingCoupledSentences)
        print(interestingSents)
        for sent in interestingSents:
            os.system("cls" if os.name == "nt" else "clear")
            print("=====================================\n")
            print(sent)
            print("=====================================\n")
            response = self.requestWith("Does this look like a quote? (y/n -- or leave blank to discard) ")
            if response == "y" or response == "n" or response == "p": # n is "no but save", p is "paraphrase"
                # confirm followup questions about topic_id / person_id
                # store the snippet
                type = "nonquote"
                person_id = None
                topic_id = None
                if response == "y" or response == "p":
                    type = "quote" if response == "y" else "paraphrase"
                    person_id = self.requestWith("Which person is the speaker (enter id or leave blank for null): ")
                    topic_id = self.requestWith("What's the topic (enter id or leave blank for null): ")
                self.storeSnippetFromSpacy(sent, article, person_id, topic_id, type)
        self.jdb.markArticleShepherded(article)
        self.guessAndSuggest(self.jdb.getUnshepherdedArticle(), smart)

    def guessAndSuggest(self, article, smart=False):
        # now does both smart and dumb guessing for maximum recall during training
        if article == None:
            print("No more articles!")
            return False
        print("=====================================\n")
        print("NEW ARTICLE!")
        print("=====================================\n")
        print(article["article_body"])
        print("=====================================\n")
        # pitch this off to grok to generate candidates...this ensures it all happens in one place
        sourceSentences = self.grok.generateStoryChunkCandidates(article)
        # smart way
        interestingSents = [sent for sent in sourceSentences if self.classifySentence(sent)["QUOTE"] > 0.5]
        # add dumb guesses
        interestingSents.extend([sent for sent in sourceSentences if self.interestingSnippetCheck(sent)])
        # couple the sentences up for any better overall statements
        interestingCoupledSentences = []
        for i, sent in enumerate(sourceSentences):
            if len(sourceSentences)-1 == i: continue
            coupledSent = sent.text + " " + sourceSentences[i+1].text
            coupledSent = self.nlp(coupledSent)
            if self.classifySentence(coupledSent)["QUOTE"] > 0.5: interestingCoupledSentences.append(coupledSent)
            if self.interestingSnippetCheck(coupledSent): interestingCoupledSentences.append(coupledSent)
        interestingSents.extend(interestingCoupledSentences)
        # now run them for review
        for sent in interestingSents:
            os.system("cls" if os.name == "nt" else "clear")
            print("=====================================\n")
            print(sent)
            print("=====================================\n")
            response = self.requestWith("Does this look like a quote? (y/n -- or leave blank to discard) ")
            if response == "y" or response == "n" or response == "p": # n is "no but save", p is "paraphrase"
                # confirm followup questions about topic_id / person_id
                # store the snippet
                type = "nonquote"
                person_id = None
                topic_id = None
                if response == "y" or response == "p":
                    type = "quote" if response == "y" else "paraphrase"
                    person_id = self.requestWith("Which person is the speaker (enter id or leave blank for null): ")
                    topic_id = self.requestWith("What's the topic (enter id or leave blank for null): ")
                self.storeSnippetFromSpacy(sent, article, person_id, topic_id, type)
        self.jdb.markArticleShepherded(article)
        self.guessAndSuggest(self.jdb.getUnshepherdedArticle(), smart)


    def storeSnippetFromSpacy(self, sentence, article, person_id=None, topic_id=None, type="quote"):
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

    def interestingSnippetCheck(self, spacyText):
        return self.personOfInterestCheck(spacyText) and (self.verbMatch(spacyText) or self.quoteCheck(spacyText))

    def classifySentence(self, spacyText):
        # a bridge to teacher
        if not self.teacher: self.teacher = Teacher()
        return self.teacher.classifySnippet(self.teacher.cleanUpString(spacyText.text))

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
        pi = input("(for help or other: type none if none left, t for topics list, and pp for people list): ")
        if pi == "none":
            return None
        elif pi == "t":
            self.printTopics()
            return self.requestWith(prompt)
        elif pi == "pp":
            self.printPeople()
            return self.requestWith(prompt)
        elif pi == "aa":
            url = input("Ah, give me a URL to ingest from: ")
            self.trunkUp(url)
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

    # ad hoc consumption functions
    def trunkUp(self, url):
        if not self.trunk:
            self.trunk = Trunk()
        article = self.trunk.getStoryByURL(url)
        self.presentArticle(article)

if __name__ == "__main__":
    s = Shepherd()
    if len(sys.argv) > 2 and sys.argv[1] in ["-a"]:
        s.trunkUp(sys.argv[2])
    else:
        s.presentArticle()
