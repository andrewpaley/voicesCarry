import spacy
from spacy.util import minibatch, compounding
from jumbodb import JumboDB
from random import shuffle
import math

# implementation note: this can be called from shepherd if we're trying to ingest new articles
# or worked with directly for testing

# GOALS:
# 1) DONE: recognize individual quotes in text (needs training/testing)
# 2) TODO: collect more snippets
# 3) TODO: try training categorizes to recognize a) subject and b) speaker?
# 4) TODO: freeze that model and then use it to do a pass pulling quotes and leading/trailing sentences from articles (grok v1)
# 5) FUTURE TODO (post project submit): store those in a "context_snippets" table in jumbodb and then do a second pass of training to teach the system to recognize good context

class Teacher(object):
    def __init__(self):
        self.nlp = spacy.blank('en')
        self.jdb = JumboDB()
        self.train()

    def train(self, dataset = None):
        if not dataset:
            dataset = self.jdb.getAll("snippets")
        trainSet, testSet = self.prepData(dataset, True)

        # set apart in case we want to do different types of analysis later...let's prep for spacy for now
        self.trainSet = self.makeSpacyReadySchema(trainSet)
        self.testSet = self.makeSpacyReadySchema(testSet)
        self.trainQuoteClassifier(self.trainSet)

    def test(self):
        self.testQuoteClassifier()
        self.classifySomeSnippets()

    def prepData(self, dataset, testMode=True): # if testMode is false, all data is training data
        cutoff = 0.75 # the line in the full set between train and test sets
        shuffle(dataset)
        # ensure quotes are equally distributed in result set
        quotes = []
        nonquotes = []
        for d in dataset:
            d["snippet"] = self.cleanUpString(d["snippet"])
            if d["is_quote"] == 1:
                quotes.append(d)
            else:
                nonquotes.append(d)
        shuffle(quotes)
        shuffle(nonquotes)
        # create the subsets
        trainQuotes = quotes[:math.floor(len(quotes)*cutoff)]
        testQuotes = quotes[math.floor(len(quotes)*cutoff):]
        trainNonQuotes = nonquotes[:math.floor(len(nonquotes)*cutoff)]
        testNonQuotes = nonquotes[math.floor(len(nonquotes)*cutoff):]
        # and now the final sets!
        trainSet = trainQuotes + trainNonQuotes
        testSet = testQuotes + testNonQuotes
        shuffle(trainSet)
        shuffle(testSet)
        if testMode != True: return trainSet + testSet
        self.trainSet = trainSet
        self.testSet = testSet
        return trainSet, testSet

    def makeSpacyReadySchema(self, dataset):
        # output list of tuples like (u"snippet text", {"cats": {"QUOTE": 0}}) where quote is 0 or 1
        output = []
        for d in dataset:
            output.append((d["snippet"], {"cats": {"QUOTE": d["is_quote"]}}))
        return output

    def cleanUpString(self, snippet):
        # a place to stick any string cleaning stuff
        # called during data prep
        snippet = snippet.replace(u'’', u"'")
        snippet = snippet.replace(u'“', u'\"')
        snippet = snippet.replace(u'”', '"')
        snippet = snippet.replace("\x1b[1;2D", "")
        snippet = snippet.replace("\x1b[1;", "")
        return snippet

    def trainQuoteClassifier(self, trainSet):
        # focus the trainer
        thePipes = [pipe for pipe in self.nlp.pipe_names if pipe != "textcat"]
        self.nlp.disable_pipes(*thePipes)

        # create/get the textcategorizer
        if "textcat" not in self.nlp.pipe_names:
            textCat = self.nlp.create_pipe("textcat")
            self.nlp.add_pipe(textCat, last=True)
        else:
             textCat = self.nlp.get_pipe("textcat")
        # set up for training
        textCat.add_label("QUOTE")
        losses = {}
        batches = minibatch(trainSet, size=compounding(4., 32., 1.001))
        optimizer = self.nlp.begin_training()
        # train!
        for batch in batches:
            snippets, cats = zip(*batch)
            self.nlp.update(snippets, cats, sgd=optimizer, drop=0.3, losses=losses)
        self.losses = losses
        self.textCat = textCat

    def testQuoteClassifier(self, testSet=None):
        # thanks to spacy's on-site tutorial for chunks of this function
        if not testSet: testSet = self.testSet
        snippets, cats = zip(*testSet)
        print('{:^5}\t{:^5}\t{:^5}\t{:^5}'.format("Loss", "Precision", "Recall", 'F SCORE'))
        snippets = (self.nlp.tokenizer(snippet) for snippet in snippets)
        tp = 0.0   # True positives
        fp = 1e-8  # False positives
        fn = 1e-8  # False negatives
        tn = 0.0   # True negatives
        for i, doc in enumerate(self.textCat.pipe(snippets)):
            gold = cats[i]["cats"]
            for label, score in doc.cats.items():
                if label not in gold:
                    continue
                if score >= 0.5 and gold[label] >= 0.5:
                    tp += 1.
                elif score >= 0.5 and gold[label] < 0.5:
                    fp += 1.
                elif score < 0.5 and gold[label] < 0.5:
                    tn += 1
                elif score < 0.5 and gold[label] >= 0.5:
                    fn += 1
        precision = tp / (tp + fp)
        recall = tp / (tp + fn)
        f_score = 2 * (precision * recall) / (precision + recall)
        print('{0:.3f}\t{1:.3f}\t{2:.3f}\t{3:.3f}'.format(self.losses["textcat"], precision, recall, f_score))

    def classifySomeSnippets(self, snippets=None, limit=10):
        # a wrapper to print a bunch of possible classification outcomes for review
        if not snippets: snippets = self.testSet
        snippetsSubset = snippets[:limit]
        for snippet in snippetsSubset:
            cats = self.classifySnippet(snippet[0])
            print(snippet[0], cats)

    def classifySnippet(self, snippet):
        # take a snippet and return the classification of quote or not
        doc = self.nlp(snippet)
        return doc.cats

if __name__ == "__main__":
    t = Teacher()
    t.train()
