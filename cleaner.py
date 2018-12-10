import spacy

class theCleaner(object):
    def __init__(self):
        # an object of helper functions for cleaning and conversion to representation for a) training and b) classifying
        self.nlp = spacy.load("en_coref_md")
        pass

    def createRepresentation(self, snippet):
        snippet = self.cleanUpString(snippet)
        # print(snippet)
        snippet = self.replaceEntities(snippet)
        return snippet

    def cleanUpString(self, snippet):
        # a place to stick any string cleaning stuff
        # called during data prep
        snippet = snippet.replace(u'’', u"'")
        snippet = snippet.replace(u'“', u'"')
        snippet = snippet.replace(u'”', '"')
        snippet = snippet.replace(u'“', u'"')
        snippet = snippet.replace(u'”', u'"')
        snippet = snippet.replace("\x1b[1;2D", "")
        snippet = snippet.replace("\x1b[1;", "")
        snippet = snippet.replace("\n", "")
        snippet = snippet.replace("\'", "'")
        return snippet

    def replaceEntities(self, snippet):
        spacySnippet = self.nlp(snippet)
        for ent in spacySnippet.ents:
            snippet = snippet.replace(ent.text, "ENTITY")
        return snippet
