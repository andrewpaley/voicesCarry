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
        # set the dropout and minibatch
        self.batchSize = 1
        self.dropout = 0.3
        # set up the data
        self.bootstrapData()

    def train(self, dataset = None):
        if not dataset: dataset = self.trainSet
        self.nlp = spacy.blank('en')
        self.trainQuoteClassifier(dataset)

    def test(self, dataset = None):
        if not dataset: dataset = self.testSet
        results = self.testQuoteClassifier(dataset)
        self.classifySomeSnippets()
        return results

    def tenFoldCV(self, batchSize=1, dropout=0.3):
        if not isinstance(batchSize, int) and len(batchSize.split(" ")) > 1:
            bs = batchSize.split(" ")
            self.batchStart = bs[1]
            self.batchEnd = bs[2]
            self.batchSize = bs[0]
        else:
            self.batchSize = batchSize
        if not isinstance(dropout, float) and len(dropout.split(" ")) > 1:
            do = dropout.split(" ")
            self.dropStart = do[1]
            self.dropEnd = do[2]
            self.dropout = do[0]
        else:
            self.dropout = dropout
        # train and test ten times in a row, recording accuracy scores for each
        results = [] # will be list of ten lists: [precision, recall, f_score]
        dataset = self.jdb.getAll("snippets")
        datasets = self.prepData10CV(dataset)
        for ds in datasets:
            self.train(ds[0])
            results.append(self.test(ds[1]))
        return results

    def bootstrapData(self):
        dataset = self.jdb.getAll("snippets")
        trainSet, testSet = self.prepData(dataset, True)
        self.trainSet = self.makeSpacyReadySchema(trainSet)
        self.testSet = self.makeSpacyReadySchema(testSet)

    def prepData(self, dataset, testMode=True): # if testMode is false, all data is training data
        cutoff = 0.8 # the line in the full set between train and test sets
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

    def prepData10CV(self, dataset):
        shuffle(dataset)
        # ensure quotes are equally distributed in result set
        tenSets = [] # ultimately a list of lists of each of ten chunks
        preppedData = [] # a list of ten tuples of train data and test data made from tenSets
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
        # swizzle the schema
        quotes = self.makeSpacyReadySchema(quotes)
        nonquotes = self.makeSpacyReadySchema(nonquotes)
        # create the subsets
        tenSetsQuotes = self.chunkList(quotes)
        tenSetsNonQuotes = self.chunkList(nonquotes)
        for i, payload in enumerate(tenSetsQuotes):
            fullSet = payload + tenSetsNonQuotes[i]
            shuffle(fullSet)
            tenSets.append(fullSet)
        for i, testSet in enumerate(tenSets):
            trainSet = [snippet for chunk in tenSets if chunk!=tenSets[i] for snippet in chunk]
            preppedData.append((trainSet, testSet))
        self.cvSets = preppedData
        return self.cvSets

    def chunkList(self, payload):
        n = math.floor(len(payload)/10.0)
        output = []
        for x in range(0, len(payload), n):
            output.append(payload[x:x+n])
        if len(output) > 10:
            output = output[:-1]
        return output

    def makeSpacyReadySchema(self, dataset):
        # output list of tuples like (u"snippet text", {"cats": {"QUOTE": 0}}) where quote is 0 or 1
        output = []
        for d in dataset:
            output.append((d["training_snippet"], {"cats": {"QUOTE": d["is_quote"]}}))
        return output

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
            start = float(self.batchStart)
            end = float(self.batchEnd)
            batches = minibatch(trainSet, size=compounding(start, end, 1.001))
        else:
            batches = minibatch(trainSet, size=self.batchSize)
        self.nlp.vocab.vectors.name = "quoteCategorizer"
        optimizer = self.nlp.begin_training()
        # train!
        if self.dropout == "decaying":
            start = float(self.dropStart)
            end = float(self.dropEnd)
            dropoutSet = decaying(start, end, 1e-4)
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
        # thanks to spacy's on-site tutorial for a chunk of this function
        if not testSet: testSet = self.testSet
        snippets, cats = zip(*testSet)
        if not self.losses:
            print('{:^5}\t{:^5}\t{:^5}'.format("Pre.", "Rec.", 'F SCORE'))
        else:
            print('{:^5}\t{:^5}\t{:^5}\t{:^5}'.format("Loss", "Pre.", "Rec.", 'F SCORE'))
        snippets = (self.nlp.tokenizer(snippet) for snippet in snippets)
        truePos = 0.0
        falsePos = 1e-8
        falseNeg = 1e-8
        trueNeg = 0.0
        for i, doc in enumerate(self.textCat.pipe(snippets)):
            truth = cats[i]["cats"]
            for label, score in doc.cats.items():
                if label not in truth:
                    continue
                if score >= 0.5 and truth[label] >= 0.5:
                    truePos += 1.
                elif score >= 0.5 and truth[label] < 0.5:
                    falsePos += 1.
                elif score < 0.5 and truth[label] < 0.5:
                    trueNeg += 1
                elif score < 0.5 and truth[label] >= 0.5:
                    falseNeg += 1
        precision = truePos / (truePos + falsePos)
        recall = truePos / (truePos + falseNeg)
        if precision == 0 and recall == 0:
            f_score = 0
        else:
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
        pairs = [("compounding 4. 32.", "decaying 0.3 0.2"), ("compounding 4. 32.", 0.3), ("compounding 4. 32.", 0.5), (5, 0.3), (15, 0.3), (1, 0.5), (1, 0.3), (1, 0.1), (1, "decaying 0.3 0.1"), ("compounding 1. 4.", 0.2)]
        fullResults = []
        for pair in pairs:
            results = t.tenFoldCV(batchSize=pair[0], dropout=pair[1])
            fullResults.append({
                "dropout": pair[1],
                "batchSize": pair[0],
                "results": results
            })
        pp(fullResults)
        breakpoint()
    elif "-nonstart" in sys.argv:
        breakpoint()
    else:
        t.train()
        t.test()
        breakpoint()
