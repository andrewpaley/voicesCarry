import spacy
from jumbodb import JumboDB
from random import shuffle
import math

train_data = [
    (u"That was very bad", {"cats": {"POSITIVE": 0}}),
    (u"it is so bad", {"cats": {"POSITIVE": 0}}),
    (u"so terrible", {"cats": {"POSITIVE": 0}}),
    (u"I like it", {"cats": {"POSITIVE": 1}}),
    (u"It is very good.", {"cats": {"POSITIVE": 1}}),
    (u"That was great!", {"cats": {"POSITIVE": 1}}),
]

# implementation note: in fullness of time, this can be called from grok if we're trying to ingest new articles or worked with directly for testing

class Teacher(object):
    def __init__(self):
        self.nlp = spacy.load('en')
        self.jdb = JumboDB()

    def train(self, dataset = None):
        if not dataset:
            dataset = self.jdb.getAll("snippets")
        trainSet, testSet = self.prepData(dataset, True)

        # set apart in case we want to do different types of analysis later...let's prep for spacy for now
        trainSet = self.makeSpacyReadySchema(trainSet)
        testSet = self.makeSpacyReadySchema(testSet)

        breakpoint()



        # THIS IS WHERE YOU STOPPED...NEXT UP: IMPLEMENT THE ACTUAL TEXT CLASSIFIER CODE COMMENTED OUT AT FILE BOTTOM
        # AND THEN JUST KEEP GETTING TRAINING SAMPLES
        # NOTE: Might have to deal with weird/different types of quotation characters in a data prep pass




    def test(self):
        pass

    def prepData(self, dataset, testMode=True): # if testMode is false, all data is training data
        cutoff = 0.75
        shuffle(dataset)
        # ensure quotes are equally distributed in result set
        quotes = []
        nonquotes = []
        for d in dataset:
            if d["is_quote"] == 1:
                quotes.append(d)
            else:
                nonquotes.append(d)
        shuffle(quotes)
        shuffle(nonquotes)
        trainQuotes = quotes[:math.floor(len(quotes)*cutoff)]
        testQuotes = quotes[math.floor(len(quotes)*cutoff):]
        trainNonQuotes = nonquotes[:math.floor(len(nonquotes)*cutoff)]
        testNonQuotes = nonquotes[math.floor(len(nonquotes)*cutoff):]
        # the final sets!
        trainSet = trainQuotes + trainNonQuotes
        testSet = testQuotes + testNonQuotes
        shuffle(trainSet)
        shuffle(testSet)
        if testMode != True: return trainSet + testSet
        return trainSet, testSet

    def makeSpacyReadySchema(self, dataset):
        # output list of tuples like (u"snippet text", {"cats": {"QUOTE": 0}}) where quote is 0 or 1
        output = []
        for d in dataset:
            output.append((d["snippet"], {"cats": {"QUOTE": d["is_quote"]}}))
        return output

# textcat = nlp.create_pipe('textcat')
# nlp.add_pipe(textcat, last=True)
# textcat.add_label('POSITIVE')
# optimizer = nlp.begin_training()
# for itn in range(100):
#     for doc, gold in train_data:
#         nlp.update([doc], [gold], sgd=optimizer)
#
# doc = nlp(u'It is good.')
# print(doc.cats)

if __name__ == "__main__":
    t = Teacher()
    t.train()
