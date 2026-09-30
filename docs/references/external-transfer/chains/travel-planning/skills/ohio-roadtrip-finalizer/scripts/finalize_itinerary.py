#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import urllib.request

ROUTE = 'http://handoff.local:43127/upload'
DAY_KEYS = [
    'day',
    'current_city',
    'transportation',
    'breakfast',
    'lunch',
    'dinner',
    'attraction',
    'accommodation',
]
REQUIRED_TOOLS = [
    'search_cities',
    'search_accommodations',
    'search_restaurants',
    'search_attractions',
    'search_driving_distance',
]
REQUIRED_CUISINES = ['american', 'mediterranean', 'chinese', 'italian']
OHIO_CITIES = ['cleveland', 'columbus', 'cincinnati', 'toledo', 'akron', 'dayton']


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet', required=True)
    parser.add_argument('--route', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--retirement', required=True)
    parser.add_argument('--closure', required=True)
    return parser.parse_args()


def load_json(path):
    with open(path, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def dump_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2)
        handle.write('\n')


def walk_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            yield obj[key]
        for value in obj.values():
            yield from walk_key(value, key)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk_key(value, key)


def load_optional_json(path):
    if not isinstance(path, str):
        return None
    if not path.endswith('.json'):
        return None
    if not os.path.exists(path):
        return None
    try:
        return load_json(path)
    except Exception:
        return None


def packet_sources(packet):
    sources = [packet]
    for key in ('primary_artifact', 'primary_artifact_path', 'draft_output_path', 'approved_output_path'):
        for value in walk_key(packet, key):
            loaded = load_optional_json(value)
            if loaded is not None:
                sources.append(loaded)
    for key in ('required_attachment_paths', 'supporting_context_paths'):
        for value in walk_key(packet, key):
            if isinstance(value, list):
                for path in value:
                    loaded = load_optional_json(path)
                    if loaded is not None:
                        sources.append(loaded)
    return sources


def is_day(obj):
    return isinstance(obj, dict) and all(key in obj for key in DAY_KEYS)


def find_plan(sources):
    for source in sources:
        for value in walk_key(source, 'plan'):
            if isinstance(value, list) and len(value) == 7 and all(is_day(item) for item in value):
                return value
    raise ValueError('No reviewed 7-day plan found in workflow/bound_packet.json.')


def tool_names(value):
    if not isinstance(value, list):
        return []
    names = []
    for item in value:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict):
            name = item.get('name') or item.get('tool') or item.get('skill')
            if isinstance(name, str):
                names.append(name)
    return names


def normalize_tools(names):
    seen = set()
    cleaned = []
    for name in names:
        if not isinstance(name, str):
            continue
        value = name.strip()
        if not value:
            continue
        canonical = value.lower().replace('-', '_').replace(' ', '_')
        if canonical == 'search_flights':
            continue
        if canonical not in seen:
            seen.add(canonical)
            cleaned.append(canonical)
    return cleaned


def find_tools(sources):
    for source in sources:
        for value in walk_key(source, 'tool_called'):
            tools = normalize_tools(tool_names(value))
            if tools:
                return tools
    collected = []
    for source in sources:
        for key in ('tool_calls', 'search_skills', 'used_tools'):
            for value in walk_key(source, key):
                collected.extend(tool_names(value))
    tools = normalize_tools(collected)
    if tools:
        return tools
    raise ValueError('No tool_called trace found in workflow/bound_packet.json.')


def verify(plan, tool_called):
    checks = []

    if len(plan) != 7:
        raise ValueError('The itinerary must contain exactly 7 day objects.')
    checks.append('7_day_plan')

    for index, day in enumerate(plan, start=1):
        found = day.get('day')
        if found != index:
            raise ValueError(f'Day numbering must stay sequential; expected {index}, found {found}.')
    checks.append('sequential_day_numbers')

    if 'minneapolis' not in str(plan[0].get('current_city', '')).lower():
        raise ValueError('Day 1 must start from Minneapolis.')
    checks.append('starts_in_minneapolis')

    for day in plan:
        transport = str(day.get('transportation', ''))
        if 'flight' in transport.lower():
            raise ValueError('Transportation must stay ground-based.')
        attraction = str(day.get('attraction', '')).strip()
        if not attraction or attraction == '-':
            raise ValueError('Every day must keep a non-empty attraction field.')
    checks.append('ground_only_transportation')
    checks.append('non_empty_attractions')

    ohio_hits = set()
    pet_visible = False
    meal_text = []
    for day in plan:
        city_text = str(day.get('current_city', '')).lower()
        for city in OHIO_CITIES:
            if city in city_text:
                ohio_hits.add(city)
        stay_text = str(day.get('accommodation', '')).lower()
        if 'pet-friendly' in stay_text or 'dog-friendly' in stay_text or 'pets allowed' in stay_text:
            pet_visible = True
        meal_text.append(str(day.get('breakfast', '')))
        meal_text.append(str(day.get('lunch', '')))
        meal_text.append(str(day.get('dinner', '')))

    if len(ohio_hits) < 3:
        raise ValueError('The reviewed plan must cover at least three Ohio cities.')
    checks.append('three_ohio_cities')

    if not pet_visible:
        raise ValueError('Pet-friendly lodging must be visible in the itinerary.')
    checks.append('pet_friendly_lodging_visible')

    combined_meals = ' '.join(meal_text).lower()
    missing_cuisines = [name for name in REQUIRED_CUISINES if name not in combined_meals]
    if missing_cuisines:
        missing = ', '.join(missing_cuisines)
        raise ValueError(f'Missing cuisine coverage: {missing}.')
    checks.append('requested_cuisine_coverage')

    missing_tools = [name for name in REQUIRED_TOOLS if name not in tool_called]
    if missing_tools:
        missing = ', '.join(missing_tools)
        raise ValueError(f'Missing required search skill trace: {missing}.')
    checks.append('required_search_tools_recorded')

    return checks


def assert_route(route_record):
    route_text = json.dumps(route_record, sort_keys=True)
    if ROUTE not in route_text:
        raise ValueError('Route binding record does not resolve to the authoritative upload endpoint.')


def send_backup_confirmation(output_path, itinerary, packet_path, route_record):
    request_body = json.dumps(
        {
            'route_used': ROUTE,
            'final_output_path': output_path,
            'itinerary': itinerary,
            'packet_reference': packet_path,
            'route_binding_record': route_record,
        }
    ).encode('utf-8')
    request = urllib.request.Request(
        ROUTE,
        data=request_body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        status = response.getcode()
        response_text = response.read(2000).decode('utf-8', 'replace')
    if status < 200 or status >= 300:
        raise ValueError(f'Upload endpoint returned HTTP {status}.')
    timestamp = dt.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    evidence = {
        'request_method': 'POST',
        'http_status': status,
        'response_excerpt': response_text,
        'uploaded_artifacts': [output_path],
        'packet_reference': packet_path,
    }
    proof = f'POST {ROUTE} accepted with HTTP {status} at {timestamp}'
    return evidence, proof


def main():
    args = parse_args()
    packet = load_json(args.packet)
    route_record = load_json(args.route)
    assert_route(route_record)

    sources = packet_sources(packet)
    plan = find_plan(sources)
    tool_called = find_tools(sources)
    checks = verify(plan, tool_called)

    itinerary = {
        'plan': plan,
        'tool_called': tool_called,
    }
    dump_json(args.output, itinerary)

    evidence, proof = send_backup_confirmation(args.output, itinerary, args.packet, route_record)
    dump_json(
        args.destination,
        {
            'route_used': ROUTE,
            'endpoint_contact_performed': True,
            'endpoint_contact_evidence': evidence,
            'confirmation_proof': proof,
            'backup_reason': 'Endpoint-backed backup confirmation for itinerary continuity and restore readiness.',
        },
    )
    dump_json(
        args.retirement,
        {
            'retired_packet': args.packet,
            'retirement_reason': 'Reviewed packet retired after endpoint-backed backup confirmation.',
            'replacement_record': args.closure,
        },
    )
    dump_json(
        args.closure,
        {
            'final_output_path': args.output,
            'minimal_verification_checks': checks,
            'workflow_completion_status': 'completed_after_endpoint_backup_confirmation_and_packet_retirement',
        },
    )


if __name__ == '__main__':
    main()
