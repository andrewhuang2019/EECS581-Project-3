import datetime
import os
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError


SCOPES = ["https://www.googleapis.com/auth/calendar"]

class GoogleAPI:
    def __init__(self):
        self.creds = None
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except RefreshError:
                    self.creds = None #drop stale creds and fall to browser login
            if not self.creds or not self.creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                self.creds = flow.run_local_server(port=0)   # opens browser to log in
            with open("token.json", "w") as f:
                f.write(self.creds.to_json())
       
        self.service = build("calendar", "v3", credentials=self.creds)

    def create_event(self, summary, start, end, timezone="America/Chicago", description=None):
        body = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start, "timeZone": timezone},
            "end": {"dateTime": end, "timeZone": timezone},
        }
        return self.service.events().insert(calendarId="primary", body=body).execute()

    def get_events(self, max_results=10):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        result = self.service.events().list(
            calendarId="primary", timeMin=now, maxResults=max_results,
            singleEvents=True, orderBy="startTime").execute()
        return result.get("items", [])

    def get_events_for_day(self, day=None, timezone="America/Chicago"):
        tz = ZoneInfo(timezone) #fall on student timezone
        day = day or datetime.datetime.now(tz).date() #window from local midnight to local midnight
        start = datetime.datetime.combine(day, datetime.time.min, tzinfo=tz)
        end = start + datetime.timedelta(days=1)
        result = self.service.events().list(
            calendarId = "primary",
            timeMin = start.isoformat(),
            timeMax = end.isoformat(),
            singleEvents = True, #expand events that reoccur into individual instances
            orderBy = "startTime", #only allowed when singleEvents is true
        ).execute()
        return result.get("items", []) #no event = missing key so default to empty list
    
    @staticmethod
    def print_events(events):
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date"))
            print(start, e.get("summary", "(no title)"))
    
