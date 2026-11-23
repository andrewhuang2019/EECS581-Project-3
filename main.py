from weather import get_today_forecast
from google_api import GoogleAPI

def main():
    try:
        forecast = get_today_forecast()
        print(forecast)  # replace with LCD output later
    except RuntimeError as error:
        print(f"Weather unavailable: {error}")

    try:
        api = GoogleAPI()
        event = api.create_event(
            "Test event from Python",
            "2026-11-24T10:00:00",
            "2026-11-24T11:00:00",
            timezone="America/Chicago",
        )
        print("Created:", event.get("htmlLink"))
        api.print_events(api.get_events())
    except Exception as e: 
        print(f"A generic error occurred: {e}")

if __name__ == "__main__":
    main()

