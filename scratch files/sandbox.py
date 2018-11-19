from newsapi import NewsApiClient
from congress import Congress
import spacy

# Set up connections
newsapi = NewsApiClient(api_key='b9faafb8977145a8a9a32d797792dc65')

# Issues
topics = ["Kavanaugh", "Tax Returns", "Mueller", "Whitaker", "Speaker of the House", "Minimum Wage"]
capi = Congress("qQvrtG5SRWJJr2HbU7SH7zOkL8Kd7RMZOHRLq5m3")
houseMembersFull = capi.members.filter("house")[0]["members"]
houseMembers = [{
    'fname': m["first_name"],
    'lname': m["last_name"],
    'party': m["party"],
    'state': m["state"],
    'district': m["district"],
    'twitter': m["twitter_account"]
} for m in houseMembersFull]

senatorsFull = capi.members.filter("senate")[0]["members"]
senators = [{
    'fname': s["first_name"],
    'lname': s["last_name"],
    'party': s["party"],
    'state': s["state"],
    'twitter': s["twitter_account"]
} for s in senatorsFull]

# kavanaugh
kavanaugh = newsapi.get_everything(q='Kavanaugh',
                                      from_param='2018-10-12',
                                      to='2018-10-24',
                                      language='en',
                                      sort_by='relevancy')

# pelosi
pelosi = newsapi.get_everything(q='Nancy Pelosi',
                                      from_param='2018-11-11',
                                      to='2018-11-11',
                                      language='en',
                                      sort_by='relevancy')
