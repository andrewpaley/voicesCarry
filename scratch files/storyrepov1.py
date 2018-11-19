import spacy
nlp = spacy.load('en')

story1 = """A federal judge in Georgia on Friday ordered state Secretary of State Brian Kemp to establish additional procedures to guarantee that voters flagged by the state as potential noncitizens can vote in the 2018 election if they can prove their citizenship.

The decision from U.S. District Judge Eleanor Ross is a win for voting rights groups who are suing the state over its so-called “exact match” system for registering new voters. The ruling is expected to affect 3,141 people who registered but whose registrations were considered pending because the state couldn’t verify their citizenship. Overall, there are about 53,000 people whose voter registrations are pending because of a system that critics say is inaccurate and discriminatory.

“From the perspective of these voters, every one of these 3,000 individual voters has an individual and constitutional right to vote,” said Danielle Lang, an attorney at the Campaign Legal Center representing the plaintiffs in the suit. “Elections in the United States are regularly decided by smaller margins than that and every vote counts.”

The ruling orders Kemp to allow people to vote if they present proof of citizenship to the county registrar before voting, or to a poll manager or deputy registrar at the polls. If someone shows up at the polls without proof of citizenship, election officials have to either let them return with proof or let them cast a provisional ballot. If someone casts a provisional ballot, they have until Friday after the election to verify their citizenship.

Voting rights have emerged as a major flashpoint in Georgia’s close gubernatorial race between Kemp and Democrat Stacey Abrams. An Associated Press analysis found that of the 53,000 people with pending voter registrations, nearly 70 percent are black, and Abrams has accused Kemp of trying to suppress votes. He has strongly denied the accusation.

In Georgia, legal permanent residents can get a driver’s license. If a legal permanent resident then became a citizen and registered to vote, however, the state’s driver’s license database was still flagging them as a noncitizen.

When someone registers to vote in Georgia, the state takes their information and matches it against either the state driver’s license database or a federal Social Security database to verify citizenship and identity. If the information isn’t an exact match, or if someone is flagged as a potential noncitizen, the person is sent a notice informing them that their registration is incomplete and they need to provide additional documentation to vote.

Most of the people on the list could vote if they showed up at the polls with ID. But those whose citizenship status was in question had to show proof of citizenship to a deputy registrar to cast a ballot. Those deputy registrars aren’t always available at the polls, Lang said. Georgia officials maintained in the suit that there were other ways for people whose citizenship was under question to vote, but Ross expressed skepticism that those alternatives were being executed.

The citizenship verification process also disproportionately affected people of color. Michael McDonald, a political science professor at the University of Florida, analyzed the voters and found Asian applicants made up 27 percent of those flagged for citizenship, even though they make up just 2.1 percent of Georgia’s voter pool. Latino applicants made up 17 percent of those flagged, even though they account for 2.8 percent of registered voters in Georgia. Whites, who are 54 percent of Georgia’s registered voters, only accounted for 13.7 percent of the list.

Ross ordered Kemp to take additional steps to educate voters about what to do if they are eligible and have been flagged as a noncitizen. She said he had to issue a press release and update his website to show how people who have been flagged can verify their citizenship status and vote. She also said he had to direct local election officials on how they can verify citizenship, and require county election boards to post a list of acceptable forms of proof of citizenship.

“Judge Ross acknowledged that Georgia already has a process in place to check citizenship at the polls,” Kemp spokeswoman Candice Broce said in a statement Friday. “She decided to also allow poll managers to participate in the verification process. It is a minor change to the current system.”
"""
