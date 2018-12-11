import spacy
from spacy.util import minibatch, compounding, decaying
from jumbodb import JumboDB
from random import shuffle
from cleaner import theCleaner
import math
import sys
from pathlib import Path
from pprint import pprint as pp

# implementation note: this can be called from shepherd if we're trying to ingest new articles
# or worked with directly for testing

class Teacher(object):
    def __init__(self):
        self.nlp = None
        self.losses = None
        self.textCat = None
        self.jdb = JumboDB()
        self.cleaner = theCleaner()
        self.outputDir = "/Users/andrewpaley/Dropbox/nu/introToML/voicesCarry/storedModels/v4/"
        # set the dropout and minibatch methods
        self.batchSize = 1
        self.dropout = 0.3
        # set up the data
        self.bootstrapData()

    def tenLoop(self, batchSize=1, dropout=0.3):
        self.batchSize = batchSize
        self.dropout = dropout
        # train and test ten times in a row, recording accuracy scores for each
        results = [] # will be list of ten tuples: (precision, recall, f_score)
        for i in range(0,10):
            self.train()
            results.append(self.test())
            self.bootstrapData()
        return results

    def train(self, dataset = None):
        self.nlp = spacy.blank('en')
        self.trainQuoteClassifier(self.trainSet)

    def bootstrapData(self):
        dataset = self.jdb.getAll("snippets")
        trainSet, testSet = self.prepData(dataset, True)
        # set apart in case we want to do different types of analysis later...let's prep for spacy for now
        self.trainSet = self.makeSpacyReadySchema(trainSet)
        self.testSet = self.makeSpacyReadySchema(testSet)

    def test(self):
        results = self.testQuoteClassifier()
        self.classifySomeSnippets()
        return results

    def prepData(self, dataset, testMode=True): # if testMode is false, all data is training data
        cutoff = 0.75 # the line in the full set between train and test sets
        shuffle(dataset)
        # ensure quotes are equally distributed in result set
        quotes = []
        nonquotes = []
        for d in dataset:
            d["training_snippet"] = self.cleaner.createRepresentation(d["snippet"])
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
            output.append((d["training_snippet"], {"cats": {"QUOTE": d["is_quote"]}}))
        return output

    # def createRepresentation(self, snippet):
    #     # for now, just clean the string
    #     # lots more to come
    #     return self.cleaner.cleanUpString(snippet)

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
        if self.batchSize == "compounding":
            batches = minibatch(trainSet, size=compounding(4., 32., 1.001))
        else:
            batches = minibatch(trainSet, size=self.batchSize)
        self.nlp.vocab.vectors.name = "quoteCategorizer"
        optimizer = self.nlp.begin_training()
        # train!
        if self.dropout == "decaying":
            dropoutSet = decaying(0.3, 0.2, 1e-4)
        else:
            dropout = self.dropout
        for batch in batches:
            snippets, cats = zip(*batch)
            if self.dropout == "decaying": dropout = next(dropoutSet)
            self.nlp.update(snippets, cats, sgd=optimizer, drop=dropout, losses=losses)
            print("loss on this round:")
            print(losses)
            losses = {}
        self.textCat = textCat

    def testQuoteClassifier(self, testSet=None):
        # thanks to spacy's on-site tutorial for chunks of this function
        if not testSet: testSet = self.testSet
        snippets, cats = zip(*testSet)
        if not self.losses:
            print('{:^5}\t{:^5}\t{:^5}'.format("Pre.", "Rec.", 'F SCORE'))
        else:
            print('{:^5}\t{:^5}\t{:^5}\t{:^5}'.format("Loss", "Pre.", "Rec.", 'F SCORE'))
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
        if not self.losses:
            print('{0:.3f}\t{1:.3f}\t{2:.3f}'.format(precision, recall, f_score))
        else:
            print('{0:.3f}\t{1:.3f}\t{2:.3f}\t{3:.3f}'.format(self.losses["textcat"], precision, recall, f_score))
        return [precision, recall, f_score]

    def saveQuoteClassifier(self):
        if self.outputDir is not None:
            outputDir = Path(self.outputDir)
        if not outputDir.exists():
            outputDir.mkdir()
        self.nlp.to_disk(outputDir)
        print("Saved model to", outputDir)

    def loadSavedQuoteClassifier(self):
        if self.outputDir is not None:
            outputDir = Path(self.outputDir)
        print("Loading from", outputDir)
        self.nlp = spacy.load(outputDir)
        self.textCat = self.nlp.get_pipe("textcat")

    def classifySomeSnippets(self, snippets=None, limit=10):
        # a wrapper to print a bunch of possible classification outcomes for review
        print("========================================")
        print("CHECK OUT SOME SNIPPETS:")
        print("========================================")
        if not snippets: snippets = self.testSet
        snippetsSubset = snippets[:limit]
        for snippet in snippetsSubset:
            text = snippet[0]
            cats = self.classifySnippet(text)
            print(snippet[0], cats)

    def classifySnippet(self, snippet):
        # take a snippet and return the classification of quote or not
        doc = self.nlp(self.cleaner.createRepresentation(snippet))
        return doc.cats

if __name__ == "__main__":
    t = Teacher()
    if len(sys.argv) > 1 and sys.argv[1] in ["-load"]:
        if len(sys.argv) > 2:
            t.outputDir = (sys.argv[2])
        t.loadSavedQuoteClassifier()
        t.test()
    elif len(sys.argv) > 1 and sys.argv[1] in ["-save"]:
        t.train()
        t.test()
        t.saveQuoteClassifier()
    elif len(sys.argv) > 1 and sys.argv[1] in ["-fulltest"]:
        pairs = [("compounding", "decaying"), ("compounding", 0.3), ("compounding", 0.5), (5, 0.3), (5, 0.3), (15, 0.3), (0.3, 1), (0.2, 1), (0.1, 1)]
        fullResults = []
        for pair in pairs:
            results = t.tenLoop(batchSize=pair[0], dropout=pair[1])
            fullResults.append({
                "dropout": pair[1],
                "batchSize": pair[0],
                "results": results
            })
        pp(fullResults)
        breakpoint()
    else:
        t.train()
        t.test()
        breakpoint()
