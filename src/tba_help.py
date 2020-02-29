import tbapy
import discord
from secrets import Secrets
from datetime import datetime
import time

YEAR = 2020
WARNING_MINUTES = 30

class TBA_Teams_List_Generator:
    def __init__(self, auth_key):
        self.tba = tbapy.TBA(auth_key)
    
    def getTeamsFromState(self, state):
        return [team.key for team in self.tba.teams(year=YEAR) if team.state_prov == state]

class TBA_Watcher:
    def __init__(self, auth_key, teams):
        self.tba = tbapy.TBA(auth_key)
        self.matches_announced = []
        self.match_results_announced = []
        self.refreshNewEvents()
        self.teams = teams

    def refreshNewEvents(self):
        curdate = datetime.today().strftime('%Y-%m-%d')
        self.events = [event for event in self.tba.events(YEAR) if event.start_date <= curdate and event.end_date >= curdate]
        self.event_keys = [event.key for event in self.events]
        self.last_refreshed = curdate
        self.matches_announced = [match for match in self.matches_announced if match.event_key in self.event_keys]
        self.match_results_announced = [match for match in self.match_results_announced if match.event_key in self.event_keys]

    # return list of embeds to send back
    def getUpdates(self, channel):
        resp = []
        if datetime.today().strftime('%Y-%m-%d') != self.last_refreshed:
            self.refreshNewEvents()
        for event, event_key in zip(self.events, self.event_keys):
            for match in [Match(event, match) for match in self.tba.event_matches(event_key)]:
                selected_teams = match.teamsInMatch(self.teams)
                if len(selected_teams) > 0 and match.isWithinWarningTime() and match.key not in self.matches_announced:
                    self.matches_announced.append(match.key)
                    print("Upcoming match:", match.key)
                    resp.append(match.generateEmbed(self.teams))
                elif len(selected_teams) > 0 and match.isFinished() and match.key not in self.match_results_announced:
                    self.match_results_announced.append(match.key)
                    print("Finished match:", match.key)
                    resp.append(match.generateEmbed(self.teams))
        return resp


class Match:
    def __init__(self, event_object, match_object):
        self.predicted_time = match_object.predicted_time
        self.match_finished = match_object.actual_time != None
        self.key = match_object.key
        self.event_name = event_object.short_name #also can try .name
        self.event_key = match_object.event_key
        self.match_key = match_object.key
        match_types = {'qm': 'Quals', 'ef': 'Eight-Finals', 'qf': 'Quarterfinals', 'sf': 'Semifinals', 'f': 'Finals'}
        self.match_name = match_types[match_object.comp_level]
        if match_object.comp_level in ['qf', 'sf', 'f']:
            self.match_name += " {} Match {}".format(match_object.set_number, match_object.match_number)
        else:
            self.match_name += " Match {}".format(match_object.match_number)
        self.red_teams = [key for key in match_object.alliances['red']['team_keys']]
        self.blue_teams = [key for key in match_object.alliances['blue']['team_keys']]
        self.winner = match_object.winning_alliance if self.isFinished() else None
        self.red_score = match_object.score_breakdown["red"]["totalPoints"] if self.isFinished() else None
        self.blue_score = match_object.score_breakdown["blue"]["totalPoints"] if self.isFinished() else None
        

    def isFinished(self):
        return self.match_finished

    def minutesTillStart(self):
        return (int(self.predicted_time) - int(time.time()))/60

    def isWithinWarningTime(self):
        return not self.isFinished() and self.minutesTillStart() <= WARNING_MINUTES

    def teamsInMatch(self, possible_teams):
        teams = []
        for team in possible_teams:
            if team in self.red_teams:
                teams.append(team)
            elif team in self.blue_teams:
                teams.append(team)
        return teams

    def generateEmbed(self, highlight_teams):
        description = ""
        title = self.event_name + " - " + self.match_name
        color = 0xffffff
        if self.winner == None:
            description = "Match starts in {} minutes".format(int(self.minutesTillStart()))
        elif len(self.winner) == 0: # tie
            description = "Tie with a score of {} - {}".format(self.red_score, self.blue_score)
        else:
            if self.winner == "red":
                color = 0xff0000
                description = "**Red** wins {} - {}".format(self.red_score, self.blue_score)
            else:
                color = 0x0000ff
                description = "**Blue** wins {} - {}".format(self.blue_score, self.red_score)
        embed=discord.Embed(title=title, url="https://www.thebluealliance.com/match/" + self.match_key, description=description, color=color)
        embed.set_thumbnail(url="https://www.thebluealliance.com/images/tba_lamp.svg")
        red_teams = ", ".join([team[3:] if team not in highlight_teams else '***' + team[3:] + '***'  for team in self.red_teams])
        blue_teams = ", ".join([team[3:] if team not in highlight_teams else '***' + team[3:] + '***'  for team in self.blue_teams])
        embed.add_field(name="**Red Teams**" if self.winner == 'red' else "Red Teams", value=red_teams, inline=True)
        embed.add_field(name="**Blue Teams**" if self.winner == 'blue' else "Blue Teams", value=blue_teams, inline=True)
        return embed
