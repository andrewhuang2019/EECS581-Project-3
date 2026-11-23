import datetime
import os

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
                self.creds.refresh(Request())
            else:
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
   
    @staticmethod
    def print_events(events):
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date"))
            print(start, e.get("summary", "(no title)"))
    
