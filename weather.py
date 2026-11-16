"""Retrieve today's forecast from Open-Meteo (no API key required)."""

import argparse
import json

import requests


API_URL = "https://api.open-meteo.com/v1/forecast"


def get_today_forecast(latitude=38.9717, longitude=-95.2353):
    """Return today's forecast for a location, defaulting to Lawrence, KS.

    'Today' uses the location's time zone, not the computer's time zone.
    Temperatures are Fahrenheit; precipitation probability is a percentage.
    weather_code is Open-Meteo's WMO condition code (see README).
    Raises ValueError for invalid coordinates and RuntimeError if the request
    fails or the API returns incomplete data. No request occurs on import.
    """
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Latitude must be -90 to 90; longitude must be -180 to 180.")

    try:
        response = requests.get(
            API_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": (
                    "weather_code,temperature_2m_max,temperature_2m_min,"
                    "precipitation_probability_max"
                ),
                "temperature_unit": "fahrenheit",
                "timezone": "auto",
                "forecast_days": 1,
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError("Could not connect to the weather API: " + str(exc)) from exc

    try:
        data = response.json()
        daily = data["daily"]
        forecast = {
            "date": daily["time"][0],
            "timezone": data["timezone"],
            "high_f": daily["temperature_2m_max"][0],
            "low_f": daily["temperature_2m_min"][0],
            "rain_chance_percent": daily["precipitation_probability_max"][0],
            "weather_code": daily["weather_code"][0],
        }
        if any(value is None for value in forecast.values()):
            raise ValueError("Missing forecast value")
        return forecast
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("The weather API returned an invalid or incomplete forecast.") from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latitude", type=float, default=38.9717)
    parser.add_argument("--longitude", type=float, default=-95.2353)
    args = parser.parse_args()
    try:
        forecast = get_today_forecast(args.latitude, args.longitude)
    except (ValueError, RuntimeError) as exc:
        parser.exit(1, f"Weather error: {exc}\n")
    print(json.dumps(forecast, indent=2))


if __name__ == "__main__":
    main()
