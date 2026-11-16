"""
schedule_input.py

Collects a user's class schedule and saves it to schedule.json so another
Python program can read it.

Accepted input formats (name is asked separately):
    MonWedFri 10:00-10:50
    TueThu 2:00-3:30
    TueThu 9:30am-10:45am      (optional am/pm)

Times without am/pm are assumed to be typical class hours:
    7:00-11:59 -> AM, 12:00-6:59 -> PM

Reading the file from another program:
    from schedule_input import load_schedule
    classes = load_schedule()           # list of dicts
    or just:  json.load(open("schedule.json"))
"""

import json
import re

SCHEDULE_FILE = "schedule.json"
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_PATTERN = re.compile(r"mon|tues?|wed|thurs?|thu|fri|sat|sun", re.IGNORECASE)
TIME_PATTERN = re.compile(r"^(\d{1,2}):(\d{2})\s*(am|pm)?$", re.IGNORECASE)


def parse_days(text):
    """'MonWedFri' -> ['Mon', 'Wed', 'Fri']. Raises ValueError if invalid."""
    days, pos = [], 0
    while pos < len(text):
        m = DAY_PATTERN.match(text, pos)
        if not m:
            raise ValueError(f"Can't understand days starting at '{text[pos:]}'")
        day = m.group(0)[:3].capitalize()
        if day in days:
            raise ValueError(f"Day '{day}' listed twice")
        days.append(day)
        pos = m.end()
    if not days:
        raise ValueError("No days given")
    return sorted(days, key=DAY_NAMES.index)


def parse_time(text, default_period=None):
    """Return (minutes_since_midnight, period_was_explicit)."""
    m = TIME_PATTERN.match(text.strip())
    if not m:
        raise ValueError(f"Bad time '{text}' (use H:MM or HH:MM)")
    hour, minute, period = int(m.group(1)), int(m.group(2)), m.group(3)
    if minute > 59:
        raise ValueError(f"Bad minutes in '{text}'")
    if period:
        if not 1 <= hour <= 12:
            raise ValueError(f"Bad hour in '{text}'")
        hour = hour % 12 + (12 if period.lower() == "pm" else 0)
        return hour * 60 + minute, True
    if hour > 23:
        raise ValueError(f"Bad hour in '{text}'")
    if hour < 7:  # 1:00-6:59 -> afternoon/evening
        hour += 12
    return hour * 60 + minute, False


def fmt(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_entry(line):
    """'TueThu 2:00-3:30' -> {'days': [...], 'start': '14:00', 'end': '15:30'}"""
    parts = line.strip().split(None, 1)
    if len(parts) != 2 or "-" not in parts[1]:
        raise ValueError("Use the format: DAYS START-END, e.g. MonWedFri 10:00-10:50")
    days = parse_days(parts[0])
    start_txt, end_txt = parts[1].split("-", 1)
    start, _ = parse_time(start_txt)
    end, end_explicit = parse_time(end_txt)
    # e.g. "11:00-1:00" -> end parsed as 13:00 already; if still not after start, bump to PM
    if end <= start and not end_explicit and end + 12 * 60 < 24 * 60:
        end += 12 * 60
    if end <= start:
        raise ValueError("End time must be after start time")
    return {"days": days, "start": fmt(start), "end": fmt(end)}


def load_schedule(path=SCHEDULE_FILE):
    """Load the saved schedule (use this from your other program)."""
    with open(path) as f:
        return json.load(f)


def save_schedule(classes, path=SCHEDULE_FILE):
    with open(path, "w") as f:
        json.dump(classes, f, indent=2)


def is_exit(text):
    return text.strip().lower() in ("exit", "quit")


def main():
    print("=== Class Schedule Entry ===")
    print("Type 'exit' at any prompt to finish and save what you've entered.\n")
    classes = []
    while True:
        name = input("Class name (e.g. Calculus 101, or 'exit' to quit): ").strip()
        if not name or is_exit(name):
            break
        while True:
            line = input(
                "  Meeting time (e.g. MonWedFri 10:00-10:50 or TueThu 2:00-3:30): "
            )
            if is_exit(line):
                name = None
                break
            try:
                entry = parse_entry(line)
                break
            except ValueError as e:
                print(f"  ! {e}")
        if name is None:  # user exited mid-class; that class is not saved
            break
        entry["name"] = name
        classes.append(entry)
        print(f"  Added: {name} {','.join(entry['days'])} {entry['start']}-{entry['end']}\n")

    if classes:
        save_schedule(classes)
        print(f"Saved {len(classes)} class(es) to {SCHEDULE_FILE}")
    else:
        print("No classes entered; nothing saved.")


if __name__ == "__main__":
    main()