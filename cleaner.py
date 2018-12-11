import spacy

class theCleaner(object):
    def __init__(self):
        # an object of helper functions for cleaning and conversion to representation for a) training and b) classifying
        self.nlp = spacy.load("en_coref_md")
        pass

    def createRepresentation(self, snippet):
        snippet = self.cleanUpString(snippet)

        # none of the following seemed to help substantially with accuracy or recall
        # I'm surprised that replacing entities didn't help somewhat, but so it goes
        snippet = self.replaceEntities(snippet)
        # snippet = self.lemmatizeWords(snippet)
        # snippet = self.parseTreeRepresentation(snippet)
        return snippet

    def cleanUpString(self, snippet):
        # a place to stick any string cleaning stuff
        # called during data prep
        snippet = snippet.replace('’', "'")
        snippet = snippet.replace('“', '"')
        snippet = snippet.replace('”', '"')
        snippet = snippet.replace('“', '"')
        snippet = snippet.replace('”', '"')
        snippet = snippet.replace("\x1b[1;2D", "")
        snippet = snippet.replace("\x1b[1;", "")
        snippet = snippet.replace("\n", "")
        snippet = snippet.replace("\'", "'")
        return snippet

    def replaceEntities(self, snippet):
        spacySnippet = self.nlp(snippet)
        entCounter = 0
        for ent in spacySnippet.ents:
            snippet = snippet.replace(ent.text, "ENTITY"+str(entCounter))
            entCounter += 1
        return snippet

    def lemmatizeWords(self, snippet):
        spacySnippet = self.nlp(snippet)
        output = ""
        for token in spacySnippet:
            output += token.lemma_ + " "
        return output

    def parseTreeRepresentation(self, snippet):
        spacySnippet = self.nlp(snippet)
        parseTree = spacySnippet.print_tree()
        # brb, learning about Recursive Neural Networks, ala the back half of these slides:
        # http://cs224d.stanford.edu/lectures/CS224d-Lecture10.pdf
        return parseTree
