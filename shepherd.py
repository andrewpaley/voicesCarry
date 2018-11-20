from jumbodb import JumboDB
import spacy
from verbsOfAttribution import verbsOA

class Shepherd(object):
    def __init__(self):
        self.jdb = JumboDB()
        self.nlp = spacy.load("en_coref_md")
        self.peopleList = [p["last_name"] for p in self.jdb.getAll("people")]
        self.topicList = [t["topic"] for t in self.jdb.getAll("topics")]
        self.verbsOfAttribution = verbsOA
        self.presentArticle()

    def presentArticle(self):
        self.snippetList = []
        print("\n\n=====================================\n\n")
        article = self.jdb.getUnshepherdedArticle()
        if article == None:
            print("There aren't any articles to present.")
            return False
        print(art["article_body"])
        print("=====================================\n")
        self.selectMethod(article)

    def selectMethod(self, article):
        method = input("Do you want to (b)rowse the full article or let Shepherd (g)uess? (b / g): ")
        if method == "b":
            self.requestSnippets(art)
        else:
            self.smartSuggest(art)

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
        sa = self.nlp(article["article_body"])
        article["corefed_body"] = sa._.coref_resolved
        csa = self.nlp(article["corefed_body"])
        sentences = list(csa.sents)
        interestingSents = [sent for sent in sentences if self.verbOrQuoteCheck(sent)]
        for sent in interestingSents:
            print(sent)
            response = self.requestWith("Does this look like a quote?")
            if response == "y":
                # confirm followup questions about topic_id / person_id
                # store the snippet
                self.createSnippetFromSpacy(sent)

    def createSnippetFromSpacy(sent):
        # TODO: implement storage now that we're guessing reasonably
        return False

    def verbOrQuoteCheck(self, spacyText):
        return (self.verbMatch(spacyText) or self.quoteCheck(spacyText))

    def verbMatch(self, spacyText):
        keyLemmas = [word.lemma_ for word in spacyText if word.pos_ == "VERB"]
        # TODO: mutate all words in the match list to the lemma forms
        matches = [word for word in keyLemmas if word in self.verbsOfAttribution]
        return len(matches) > 0

    def quoteCheck(self, spacyText):
        quoteTokens = [token for token in spacyText if token.is_quote]
        return len(quoteTokens) >0


    def requestWith(self, prompt):
        print(prompt)
        pi = input("(type n if none left, t for topics list, and p for people list): ")
        if pi == "n":
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
            print(person["first_name"] + "" + person["last_name"] + ": " + str(person["id"]))
        print("==============")

if __name__ == "__main__":
    s = Shepherd()
