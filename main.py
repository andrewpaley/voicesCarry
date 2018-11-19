from jumbodb import JumboDB
from trunk import Trunk
from grok import Grok

# make a data-getter and kick it off to update from the last couple of days
# promptInput = input("Update the stories database? (y/n): ")
# if promptInput == "y":
#     t = Trunk()
#     t.suckUp()
#
# # new up a grokker
# g = Grok()
# g.getUngroked()



import corenlp
cnlpAnnotators = "tokenize ssplit pos lemma ner depparse coref quote"
cnlp = corenlp.CoreNLPClient(annotators=cnlpAnnotators.split())

test = """The spin game is now in full swing. At first, it seemed the Blue Wave wasn’t quite what was predicted. But with each passing day came more and more good news for Democrats and progressives. The Washington Post quoted a terrific quip making the rounds in the House Democratic Caucus ― that this year’s midterms were more like Hanukkah than Christmas ― several days of gifts.\n\nStill, to hear conservatives and corporate Democrats tell it, Election Day was not a good day for progressives. Every day, The Wall Street Journal publishes another opinion piece contending that the Democratic victory was less than it seemed. Kimberley Strassel, cherry-picking a few high-profile losses in Friday’s WSJ, declared: “Biggest Loser: Elizabeth Warren.”\n\nOn Saturday, in the same space, political scientist Allen Guelzo invidiously compared Tuesday’s Democratic House pickup of “only” between 35 and 40 House seats to the election of 1932, when the Democrats did a bit better and flipped 46. FDR in 1932! I’d say that’s pretty good company. In fact, this year saw the biggest Democratic midterm gains since the post-Watergate blowout of 1974, when Dems took 49 Republican seats.\n\nYou kind of expect this lame spinning from the Journal. Far more insidious is the corporate Democrat spin machine called Third Way.\n\nTo hear this band of Wall Street Democrats tell it, centrist Democrats had a great night, while progressives were losers. This selective use of statistics has all the intellectual honesty of an offering prospectus for subprime derivatives. Third Way bragged that 23 of its endorsed candidates were among those who flipped Republican seats. Yes, but in fact many of those were substantive progressives, including Sharice Davids (Kansas), Jason Crow (Colorado), Anne Kirkpatrick (Arizona) and Abigail Spanberger (Virginia). As a House member, even Beto O’Rourke (!) was part of the supposedly centrist New Democrat Coalition.\n\nTo believe that “moderates” were Tuesday’s big winners, you’d have to redefine what it means to be a moderate. Most Democratic winners, even those backed by Third Way, were advocates of expanded Medicare and Social Security, better minimum wage protection and more control of prescription drug pricing.\n\nThird Way is quick to point out that if you look at standard polls, you find that more Americans characterize themselves as moderates or conservatives than as liberals. But if you dig deeper, you find that the majority of voters are substantive progressives. In fact, the percentage of Democrats who identify as liberal rather than moderate has risen steadily in the past decade. By 2018, more than half of all Democrats considered themselves liberal.\n\nMore to the point, a large majority of Americans are substantively progressive once we go beyond superficial labels. Fully 70 percent support Medicare for All, a figure that includes 82 percent of self-identified Democrats and even 52 percent of Republicans as well as a majority of independents. Large majorities also support making higher education debt-free. Pew found that 58 percent of Americans support a $15 minimum wage. According to Gallup, 62 percent of Americans approve of unions, a 15-year high. Gallup also found broad majority support for a large infrastructure program.\n\nProgressive is the new moderate. And by clearly addressing pocketbook frustrations, progressive Democrats show the power of that message to bridge over race.\n\nSupporters of Sharice Davids celebrate her victory over the Republican incumbent, Kevin Yoder, in their Kansas House race. (ASSOCIATED PRESS) More"""

oo = cnlp.annotate(test)

breakpoint()
