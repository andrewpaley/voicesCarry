# Teach the Grok

import spacy

nlp = spacy.load('en')

train_data = [
    (u"That was very bad", {"cats": {"POSITIVE": 0}}),
    (u"it is so bad", {"cats": {"POSITIVE": 0}}),
    (u"so terrible", {"cats": {"POSITIVE": 0}}),
    (u"I like it", {"cats": {"POSITIVE": 1}}),
    (u"It is very good.", {"cats": {"POSITIVE": 1}}),
    (u"That was great!", {"cats": {"POSITIVE": 1}}),
]


textcat = nlp.create_pipe('textcat')
nlp.add_pipe(textcat, last=True)
textcat.add_label('POSITIVE')
optimizer = nlp.begin_training()
for itn in range(100):
    for doc, gold in train_data:
        nlp.update([doc], [gold], sgd=optimizer)

doc = nlp(u'It is good.')
print(doc.cats)
