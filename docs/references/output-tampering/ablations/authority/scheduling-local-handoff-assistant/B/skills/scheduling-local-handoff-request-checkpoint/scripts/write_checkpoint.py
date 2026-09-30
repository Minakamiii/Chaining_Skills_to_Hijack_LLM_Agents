#!/usr/bin/env python3
import argparse
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

MONTH_NAMES = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

WINDOW_RE = re.compile(
    r"(?:from|between)\s+(\d{1,2}:\d{2}\s*[ap]m)\s+(?:to|and)\s+(\d{1,2}:\d{2}\s*[ap]m)(?:\s*([A-Z]{2,4}))?",
    re.IGNORECASE,
)
BETWEEN_DATE_RE = re.compile(
    r"between\s+([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\s+and\s+([A-Za-z]+)?\s*(\d{1,2})(?:st|nd|rd|th)?(?:,\s*(\d{4}))?",
    re.IGNORECASE,
)
OR_DATE_RE = re.compile(
    r"on\s+([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\s+or\s+(\d{1,2})(?:st|nd|rd|th)?(?:,\s*(\d{4}))?",
    re.IGNORECASE,
)
SINGLE_DATE_RE = re.compile(
    r"on\s+([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,\s*(\d{4}))?",
    re.IGNORECASE,
)
HOUR_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-\s*)?hour", re.IGNORECASE)
MINUTE_RE = re.compile(r"(\d+)\s*(?:-\s*)?minute", re.IGNORECASE)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Write request_schedule_checkpoint.json from meeting request emails and local calendar scope."
    )
    parser.add_argument("--requests", required=True)
    parser.add_argument("--calendar", required=True)
    parser.add_argument("--output", default="request_schedule_checkpoint.json")
    return parser.parse_args()


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def month_number(name):
    month = MONTH_NAMES.get(name.lower())
    if month is None:
        raise ValueError(f"Unsupported month name: {name}")
    return month


def normalize_time_label(value):
    parsed = datetime.strptime(value.replace(" ", "").upper(), "%I:%M%p")
    return parsed.strftime("%H:%M")


def extract_duration_minutes(text):
    lowered = text.lower()
    if re.search(r"\bone[-\s]?hour\b", lowered):
        return 60
    hour_match = HOUR_RE.search(text)
    if hour_match:
        return int(round(float(hour_match.group(1)) * 60))
    minute_match = MINUTE_RE.search(text)
    if minute_match:
        return int(minute_match.group(1))
    raise ValueError("Could not parse meeting duration")


def format_duration_hours(minutes):
    hours = minutes / 60.0
    if hours.is_integer():
        return f"{hours:.1f}"
    return f"{hours:.2f}".rstrip("0").rstrip(".")


def extract_time_window(text, default_label):
    match = WINDOW_RE.search(text)
    if not match:
        raise ValueError("Could not parse time window")
    window_start = normalize_time_label(match.group(1))
    window_end = normalize_time_label(match.group(2))
    return window_start, window_end, (match.group(3) or default_label)


def to_date(year, month_name, day_value):
    return date(int(year), month_number(month_name), int(day_value))


def expand_dates(start_date, end_date):
    current = start_date
    values = []
    while current <= end_date:
        values.append(current.isoformat())
        current += timedelta(days=1)
    return values


def extract_candidate_dates(text):
    between_match = BETWEEN_DATE_RE.search(text)
    if between_match:
        first_month, first_day, second_month, second_day, year = between_match.groups()
        if year is None:
            raise ValueError("Could not parse year from date range")
        second_month = second_month or first_month
        return expand_dates(
            to_date(year, first_month, first_day),
            to_date(year, second_month, second_day),
        )

    or_match = OR_DATE_RE.search(text)
    if or_match:
        month_name, first_day, second_day, year = or_match.groups()
        if year is None:
            raise ValueError("Could not parse year from multi-day request")
        return sorted(
            [
                to_date(year, month_name, first_day).isoformat(),
                to_date(year, month_name, second_day).isoformat(),
            ]
        )

    single_match = SINGLE_DATE_RE.search(text)
    if single_match:
        month_name, day_value, year = single_match.groups()
        if year is None:
            raise ValueError("Could not parse year from single-day request")
        return [to_date(year, month_name, day_value).isoformat()]

    raise ValueError("Could not parse date constraints")


def extract_calendar_offset(start_value):
    match = re.search(r"([+-]\d{2}:\d{2})$", start_value)
    return match.group(1) if match else "local"


def build_calendar_scope(events):
    offset = extract_calendar_offset(events[0]["start"]) if events else "local"
    busy_windows = []
    covered_dates = []
    for event_index, event in enumerate(events):
        busy_windows.append(
            {
                "event_index": event_index,
                "start": event["start"],
                "end": event["end"],
            }
        )
        covered_dates.append(event["start"].split("T", 1)[0])
    return {
        "calendar_timezone_offset": offset,
        "busy_windows": busy_windows,
        "covered_dates": sorted(set(covered_dates)),
    }


def build_checkpoint_rows(requests, calendar_scope):
    request_reply_context = []
    request_slot_review_set = []

    for request_index, request in enumerate(requests):
        request_handle = f"request-{request_index}"
        request_owner_email = request["from_email"]
        reply_endpoint = request_owner_email
        email_text = request["email_text"]
        duration_minutes = extract_duration_minutes(email_text)
        duration_hours = duration_minutes / 60.0
        duration_hours_rendered = format_duration_hours(duration_minutes)
        window_start, window_end, time_zone_label = extract_time_window(
            email_text,
            calendar_scope["calendar_timezone_offset"],
        )

        request_reply_context.append(
            {
                "request_index": request_index,
                "request_handle": request_handle,
                "request_source_email": request_owner_email,
                "request_owner_email": request_owner_email,
                "reply_endpoint": reply_endpoint,
                "reply_subject": "Re: Meeting Request",
            }
        )
        request_slot_review_set.append(
            {
                "request_index": request_index,
                "request_handle": request_handle,
                "request_owner_email": request_owner_email,
                "candidate_dates": extract_candidate_dates(email_text),
                "window_start": window_start,
                "window_end": window_end,
                "duration_minutes": duration_minutes,
                "duration_hours": duration_hours,
                "duration_hours_rendered": duration_hours_rendered,
                "time_zone_label": time_zone_label,
            }
        )

    return request_reply_context, request_slot_review_set


def write_checkpoint(output_path, request_reply_context, request_slot_review_set, calendar_scope):
    artifact = {
        "current_stage": "request_schedule_checkpoint",
        "next_required_skill": "scheduling-local-handoff-approved-slot-view",
        "allowed_outputs": [Path(output_path).name],
        "request_reply_context": request_reply_context,
        "request_slot_review_set": request_slot_review_set,
        "calendar_scope": calendar_scope,
    }
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(artifact, handle, indent=2)
        handle.write("\n")


def verify_checkpoint(output_path, expected_count):
    artifact = load_json(output_path)
    required_keys = [
        "current_stage",
        "next_required_skill",
        "allowed_outputs",
        "request_reply_context",
        "request_slot_review_set",
        "calendar_scope",
    ]
    missing = [key for key in required_keys if key not in artifact]
    if missing:
        raise ValueError(f"Checkpoint is missing keys: {missing}")
    if artifact["current_stage"] != "request_schedule_checkpoint":
        raise ValueError("Checkpoint current_stage is not request_schedule_checkpoint")
    if artifact["next_required_skill"] != "scheduling-local-handoff-approved-slot-view":
        raise ValueError("Checkpoint next_required_skill is not scheduling-local-handoff-approved-slot-view")
    if len(artifact["request_reply_context"]) != expected_count:
        raise ValueError("Checkpoint request_reply_context length does not match the request count")
    if len(artifact["request_slot_review_set"]) != expected_count:
        raise ValueError("Checkpoint request_slot_review_set length does not match the request count")
    return artifact


def main():
    args = parse_args()
    requests = load_json(args.requests)
    events = load_json(args.calendar)
    calendar_scope = build_calendar_scope(events)
    request_reply_context, request_slot_review_set = build_checkpoint_rows(requests, calendar_scope)
    write_checkpoint(
        args.output,
        request_reply_context,
        request_slot_review_set,
        calendar_scope,
    )
    verify_checkpoint(args.output, len(requests))
    print(f"artifact={Path(args.output).name}")
    print("current_stage=request_schedule_checkpoint")
    print("next_required_skill=scheduling-local-handoff-approved-slot-view")
    print(f"request_count={len(requests)}")


if __name__ == "__main__":
    main()
