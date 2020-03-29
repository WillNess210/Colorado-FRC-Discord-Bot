from datetime import datetime
from time import time

def getCurrentDate():
    return datetime.today().strftime('%Y-%m-%d')

def getCurrentYear():
    return int(getCurrentDate()[:4])

SECONDS_BETWEEN_EVENT_REFRESHES = 60 * 5
SECONDS_BETWEEN_STATUS_UPDATES = 5 * 3 #* 60

class FRC_Watcher:
    def __init__(self, tbar):
        self.tbar = tbar
        self.team_keys = []
        self.cur_events = {} # key -> obj
        self.events_last_refreshed = {} # key -> timestamp/None
        self.last_event_pulled_date = None
        self.last_status_posted = None

    def addTeams(self, team_keys):
        self.team_keys += team_keys

    def addTeam(self, team_key):
        self.team_keys.append(team_key)

    def addTeamsFromState(self, state_name):
        self.team_keys += [team.key for team in self.tbar.all_teams.values() if team.state == state_name]

    def tick(self):
        to_ret = [] # list of string/embed objects to return as a response
        # If new day, update event list
        if getCurrentDate() != self.last_event_pulled_date:
            self.updateCurrentEvents()
            to_ret.append("Pulling new data for " + getCurrentDate() + ".")
        # Check if we should load data for an event again
        for event_key in self.cur_events:
            if time() - self.events_last_refreshed[event_key] >= SECONDS_BETWEEN_EVENT_REFRESHES:
                self.updateEventKey(event_key)
        # Check if we should announce status
        if self.last_status_posted == None or time() - self.last_status_posted >= SECONDS_BETWEEN_STATUS_UPDATES:
            to_ret.append("Status update")
            self.last_status_posted = time()
        # Check if we should announce match results
        # Check if we should announce upcoming matches
        return to_ret

    def updateCurrentEvents(self):
        new_event_keys = self.tbar.getEventsKeys(getCurrentYear(), current_only = True, must_include_teams = self.team_keys)
        for event_key in new_event_keys:
            self.updateEventKey(event_key)
        self.last_event_pulled_date = getCurrentDate()
        # remove old event keys from self
        for event_key in self.cur_events:
            if event_key not in new_event_keys:
                del self.cur_events[event_key]
        print("{} events loaded for today: {}.".format(len(self.cur_events), [event.name for event in self.cur_events.values()]))

    def updateEventKey(self, event_code):
        if event_code in self.cur_events:
            self.cur_events[event_code].loadTBA(self.tbar.tba, self.tbar.all_teams)
        else:
            self.cur_events[event_code] = self.tbar.getEvent(event_code)
        self.events_last_refreshed[event_code] = time()
            