import tbapy
import discord
from secrets import Secrets
from datetime import datetime
import time

YEAR = 2020
WARNING_MINUTES = 15

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

    # return team updates to send back
    def getTeamUpdates(self, last_update_data = None):
        teams = []
        teams_event_keys = []
        for team in self.teams:
            for match in self.match_results_announced + self.match_results_announced:
                if team in match.red_teams or team in match.blue_teams:
                    teams.append(team)
                    teams_event_keys.append(match.event_key)
                    break
        status = []
        event_names = []
        for team, event_key in zip(teams, teams_event_keys):
            status.append(self.tba.team_status(team, event_key).overall_status_str.replace("<b>", "**").replace("</b>", "**"))
            event_names.append(self.tba.event(event_key, simple=True).name)
        # generate event -> [status] dict
        event_statuses = {}
        for status, event_name in zip(status, event_names):
            if event_name in event_statuses:
                event_statuses[event_name].append(status)
            else:
                event_statuses[event_name] = [status]
        embed=discord.Embed(title="Current Team Status:")
        for event_name in event_statuses:
            embed.add_field(name=event_name, value="\n\n".join(event_statuses[event_name]), inline=False)
        if last_update_data != None:
            cur_update_data = (teams, status, event_names)
            foundAnyDifferent = False
            for i in range(len(cur_update_data)):
                for last_data, cur_data in zip(last_update_data[i], cur_update_data[i]):
                    if last_data != cur_data:
                        foundAnyDifferent = True
                        break
            if not foundAnyDifferent:
                return None, cur_update_data
        return embed, (teams, status, event_names)

    # return list of embeds to send back
    def getUpdates(self):
        resp = []
        if datetime.today().strftime('%Y-%m-%d') != self.last_refreshed:
            self.refreshNewEvents()
        for event, event_key in zip(self.events, self.event_keys):
            for match in [Match(event, match) for match in self.tba.event_matches(event_key)]:
                selected_teams = match.teamsInMatch(self.teams)
                #if len(selected_teams) > 0 and not match.isFinished():
                    #print("Checking:", match.key, match.minutesTillStart(), match.predicted_time)
                if len(selected_teams) > 0 and match.isWithinWarningTime() and match.key not in [match.key for match in self.matches_announced]:
                    self.matches_announced.append(match)
                    print("Upcoming match:", match.key)
                    resp.append(match.generateEmbed(self.teams))
                elif len(selected_teams) > 0 and match.isFinished() and match.key not in [match.key for match in self.match_results_announced]:
                    self.match_results_announced.append(match)
                    print("Finished match:", match.key)
                    resp.append(match.generateEmbed(self.teams))
        return resp


class Match:
    def __init__(self, event_object, match_object):
        self.predicted_time = match_object.predicted_time
        if self.predicted_time == None:
            self.predicted_time = match_object.time if match_object.time != None else int(time.time() + 60 * 30)
        self.match_finished = match_object.actual_time != None
        self.key = match_object.key
        self.event_name = event_object.short_name #also can try .name
        self.event_key = match_object.event_key
        self.match_key = match_object.key
        match_types = {'qm': 'Quals', 'ef': 'Eight-Finals', 'qf': 'Quarterfinals', 'sf': 'Semifinals', 'f': 'Finals'}
        self.match_name = match_types[match_object.comp_level]
        if match_object.comp_level in ['qf', 'sf']:
            self.match_name += " {} Match {}".format(match_object.set_number, match_object.match_number)
        else:
            self.match_name += " Match {}".format(match_object.match_number)
        self.red_teams = [key for key in match_object.alliances['red']['team_keys']]
        self.blue_teams = [key for key in match_object.alliances['blue']['team_keys']]
        self.winner = match_object.winning_alliance if self.isFinished() else None
        if 'score_breakdown' in match_object and match_object.score_breakdown != None and 'red' in match_object.score_breakdown and 'blue' in match_object.score_breakdown and 'totalPoints' in match_object.score_breakdown['red'] and 'totalPoints' in match_object.score_breakdown['blue']:
            self.red_score = match_object.score_breakdown["red"]["totalPoints"] if self.isFinished() else None
            self.blue_score = match_object.score_breakdown["blue"]["totalPoints"] if self.isFinished() else None
        else:
            self.red_score = "Not Found"
            self.blue_score = "Not Found"
        

    def isFinished(self):
        return self.match_finished

    def minutesTillStart(self):
        val = (int(self.predicted_time) - time.time())/60
        #print(self.predicted_time, "-", time.time(), "=", val)
        return val

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
