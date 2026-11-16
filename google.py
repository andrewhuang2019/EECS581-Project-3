import datetime
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

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

    def get_events(self):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.events = self.service.events().list(
            calendarId="primary", timeMin=now, maxResults=10,
            singleEvents=True, orderBy="startTime").execute()
        return self.events

    def print_events(self):
        for e in self.events.get("items", []):
            start = e["start"].get("dateTime", e["start"].get("date"))
            print(start, e.get("summary"))

