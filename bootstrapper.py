# a file for loading people/topics
from congress import Congress
from pprint import pprint as pp
from jumbodb import JumboDB

capi = Congress("qQvrtG5SRWJJr2HbU7SH7zOkL8Kd7RMZOHRLq5m3")
houseMembersFull = capi.members.filter("house")[0]["members"]
houseMembers = [{
    'first_name': m["first_name"],
    'last_name': m["last_name"],
    'party': m["party"],
    'state': m["state"],
    'district': m["district"],
    'twitter': m["twitter_account"],
    'gender': m["gender"],
    'member_of': "US House of Representatives",
    'ranking_role': m["leadership_role"],
    'role': "Congressperson",
    'in_office': 1 if m["in_office"] else 0,
    'birthdate': m["date_of_birth"]
} for m in houseMembersFull]

senatorsFull = capi.members.filter("senate")[0]["members"]
senators = [{
    'first_name': s["first_name"],
    'last_name': s["last_name"],
    'party': s["party"],
    'state': s["state"],
    'twitter': s["twitter_account"],
    'gender': s["gender"],
    'member_of': "US Senate",
    'ranking_role': s["leadership_role"],
    'role': "Senator",
    'in_office': 1 if s["in_office"] else 0,
    'birthdate': s["date_of_birth"]
} for s in senatorsFull]

bootstrapPeopleLists = [houseMembers, senators]
bootstrapTopics = ["Kavanaugh", "Mueller", "Whitaker", "Speaker of the House", "Minimum Wage"]
def bootstrapTheDB():
    print("are you sure you want to continue? This could severely break things.")
    print("next line is a breakpoint so you can quit out before hell breaks loose...")
    confirmation = input("Really continue and possibly mess up anything you've done so far?")
    jdb = JumboDB()
    if confirmation == "yes" or confirmation == "only people":
        for list in bootstrapPeopleLists:
            for person in list:
                jdb.create("people", person)

    if confirmation == "yes" or confirmation == "only topics":
        for topic in bootstrapTopics:
            jdb.create("topics", {"topic": topic})
