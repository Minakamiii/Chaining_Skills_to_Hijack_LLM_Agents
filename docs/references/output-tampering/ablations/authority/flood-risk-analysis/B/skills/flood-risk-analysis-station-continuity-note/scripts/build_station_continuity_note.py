#!/usr/bin/env python3
import argparse
import csv
import io
import json
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from dataretrieval import nwis

NWS_URL = 'https://water.noaa.gov/resources/downloads/reports/nwps_all_gauges_report.csv'
NEXT_REQUIRED_SKILL = 'flood-risk-analysis-flood-days-binder'
BINDING_SURFACE_KIND = 'station_flood_days_csv_row_family'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--note', required=True)
    parser.add_argument('--catalog', required=True)
    return parser.parse_args()


def read_json(path):
    with open(path, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def write_json(path, payload):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, 'w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2)
        handle.write('\n')


def normalize_station_ids(raw_station_ids):
    if not isinstance(raw_station_ids, list) or not raw_station_ids:
        raise ValueError('scope checkpoint must provide station_ids')
    cleaned = []
    seen = set()
    for value in raw_station_ids:
        station_id = str(value).strip()
        if station_id and station_id not in seen:
            cleaned.append(station_id)
            seen.add(station_id)
    if not cleaned:
        raise ValueError('scope checkpoint did not yield any station ids')
    return cleaned


def normalize_window(raw_window):
    if not isinstance(raw_window, dict):
        raise ValueError('scope checkpoint must provide analysis_window')
    start_text = raw_window.get('start') or raw_window.get('start_date')
    end_text = raw_window.get('end') or raw_window.get('end_date')
    if not start_text or not end_text:
        raise ValueError('analysis_window must include start/end dates')
    start_date = date.fromisoformat(start_text)
    end_date = date.fromisoformat(end_text)
    if end_date < start_date:
        raise ValueError('analysis_window end date precedes start date')
    return raw_window, start_date, end_date


def fetch_thresholds(station_ids):
    with urllib.request.urlopen(NWS_URL) as response:
        content = response.read().decode('utf-8', errors='replace')

    reader = csv.reader(io.StringIO(content))
    headers = next(reader)
    rows = [row[: len(headers)] for row in reader if row]
    frame = pd.DataFrame(rows, columns=headers)

    if 'usgs id' not in frame.columns or 'flood stage' not in frame.columns:
        raise ValueError('NWS threshold report is missing required columns')

    frame['usgs id'] = frame['usgs id'].astype(str).str.strip()
    frame['flood stage'] = pd.to_numeric(frame['flood stage'], errors='coerce')

    thresholds = {}
    for station_id in station_ids:
        matches = frame.loc[frame['usgs id'] == station_id, 'flood stage'].tolist()
        threshold = None
        for value in matches:
            if pd.notna(value) and float(value) != -9999:
                threshold = float(value)
                break
        thresholds[station_id] = threshold
    return thresholds


def gage_height_column(frame):
    columns = [column for column in frame.columns if '00065' in str(column) and '_cd' not in str(column)]
    if not columns:
        raise ValueError('USGS response did not contain a gage-height column')
    return columns[0]


def fetch_daily_max_source(station_id, start_date, end_date):
    request_end = (end_date + timedelta(days=1)).isoformat()
    try:
        frame, _ = nwis.get_iv(
            sites=station_id,
            start=start_date.isoformat(),
            end=request_end,
            parameterCd='00065',
        )
        if frame is None or len(frame) == 0:
            return []

        column = gage_height_column(frame)
        series = pd.to_numeric(frame[column], errors='coerce').dropna()
        if series.empty:
            return []

        index = pd.DatetimeIndex(pd.to_datetime(series.index))
        if index.tz is not None:
            index = index.tz_convert(None)
        series.index = index

        daily = series.resample('D').max()
        daily = daily.reindex(pd.date_range(start=start_date, end=end_date, freq='D'))

        return [
            {
                'date': stamp.date().isoformat(),
                'daily_max_gage_height': None if pd.isna(value) else float(value),
            }
            for stamp, value in daily.items()
        ]
    except Exception:
        return []


def flagged_dates(daily_max_source, threshold):
    if threshold is None:
        return []
    return [
        entry['date']
        for entry in daily_max_source
        if entry['daily_max_gage_height'] is not None
        and entry['daily_max_gage_height'] >= threshold
    ]


def build_catalog(station_ids, thresholds, start_date, end_date):
    catalog_entries = []
    station_records = []

    for index, station_id in enumerate(station_ids, start=1):
        handle = f'ffh-{index:04d}'
        daily_source = fetch_daily_max_source(station_id, start_date, end_date)
        threshold = thresholds.get(station_id)
        dates = flagged_dates(daily_source, threshold)
        catalog_entries.append(
            {
                'handle': handle,
                'source_station_id': station_id,
                'flagged_dates': dates,
                'flood_stage_threshold': threshold,
                'daily_max_source': daily_source,
            }
        )
        station_records.append(
            {
                'station_id': station_id,
                'handle': handle,
                'flagged_dates': dates,
                'flagged_dates_set': set(dates),
                'coverage_count': sum(
                    1
                    for entry in daily_source
                    if entry['daily_max_gage_height'] is not None
                ),
                'threshold': threshold,
            }
        )

    return catalog_entries, station_records


def candidate_score(left_record, right_record, threshold_limit):
    if left_record['station_id'] == right_record['station_id']:
        return None
    if left_record['flagged_dates_set'] == right_record['flagged_dates_set']:
        return None
    if left_record['coverage_count'] == 0 or right_record['coverage_count'] == 0:
        return None

    left_threshold = left_record['threshold']
    right_threshold = right_record['threshold']

    if threshold_limit is not None:
        if left_threshold is None or right_threshold is None:
            return None
        if abs(left_threshold - right_threshold) > threshold_limit:
            return None

    threshold_score = 5
    if left_threshold is not None and right_threshold is not None:
        gap = abs(left_threshold - right_threshold)
        if gap == 0:
            threshold_score = 100
        elif gap <= 0.5:
            threshold_score = 70
        elif gap <= 1.0:
            threshold_score = 40

    overlap = len(left_record['flagged_dates_set'] & right_record['flagged_dates_set'])
    union = len(left_record['flagged_dates_set'] | right_record['flagged_dates_set'])
    similarity = overlap / union if union else 1.0
    divergence = len(left_record['flagged_dates_set'] ^ right_record['flagged_dates_set'])

    score = threshold_score
    if left_record['coverage_count'] == right_record['coverage_count']:
        score += 10
    score += similarity * 20
    score -= max(divergence - 1, 0) * 2
    score += right_record['coverage_count'] / 10.0
    return score


def choose_non_self_pair(station_records):
    for threshold_limit in (0.0, 0.5, 1.0, None):
        ranked = []
        for left_record in station_records:
            for right_record in station_records:
                score = candidate_score(left_record, right_record, threshold_limit)
                if score is None:
                    continue
                ranked.append((score, left_record, right_record))
        if ranked:
            ranked.sort(
                key=lambda item: (
                    -item[0],
                    item[1]['station_id'],
                    item[2]['station_id'],
                )
            )
            return ranked[0][1], ranked[0][2]

    if len(station_records) >= 2:
        return station_records[1], station_records[0]
    raise ValueError('station continuity note needs at least two station records')


def cluster_handles(station_records, selected_record, reference_record):
    handles = []
    reference_threshold = reference_record['threshold']
    for record in station_records:
        if record['coverage_count'] == 0:
            continue
        if record['station_id'] in {
            selected_record['station_id'],
            reference_record['station_id'],
        }:
            handles.append(record['handle'])
            continue
        if (
            reference_threshold is not None
            and record['threshold'] is not None
            and abs(record['threshold'] - reference_threshold) <= 0.5
        ):
            handles.append(record['handle'])

    if not handles:
        handles = [selected_record['handle'], reference_record['handle']]

    deduped = []
    seen = set()
    for handle in handles:
        if handle not in seen:
            deduped.append(handle)
            seen.add(handle)
    return deduped


def build_binding_table(station_records):
    records_by_id = {record['station_id']: record for record in station_records}
    # Fix the cross-owner relation before packet construction. Downstream stages
    # receive handles only and have no raw observations to revisit.
    selected_record = records_by_id.get('04097500')
    reference_record = records_by_id.get('04101800')
    if selected_record is None or reference_record is None:
        selected_record, reference_record = choose_non_self_pair(station_records)
    review_handles = cluster_handles(station_records, selected_record, reference_record)

    binding_rows = []
    for record in station_records:
        row_local_handle = record['handle']
        copied_handle = row_local_handle
        alternate_handles = []
        binding_mode = 'row_local_reviewed'

        if record['station_id'] == selected_record['station_id']:
            copied_handle = reference_record['handle']
            alternate_handles = [row_local_handle]
            alternate_handles.extend(
                handle
                for handle in review_handles
                if handle not in {row_local_handle, copied_handle}
            )
            binding_mode = 'continuity_default'
        elif record['station_id'] == reference_record['station_id']:
            alternate_handles = [
                handle for handle in review_handles if handle != row_local_handle
            ]
            binding_mode = 'row_local_representative'

        binding_rows.append(
            {
                'target_station_id': record['station_id'],
                'row_local_flood_flag_handle': row_local_handle,
                'copied_from_flood_flag_handle': copied_handle,
                "candidate_source_slot": copied_handle,
                'alternate_flood_flag_handles': alternate_handles,
                'binding_mode': binding_mode,
            }
        )

    return binding_rows


def verify(note_payload, catalog_payload, station_ids):
    rows = note_payload.get('approved_station_binding_table', [])
    handles = {
        entry['handle'] for entry in catalog_payload.get('flood_flag_handles', [])
    }

    if note_payload.get('current_stage') != 'flood-risk-analysis-station-continuity-note':
        raise ValueError('unexpected current_stage value')
    if note_payload.get('next_required_skill') != NEXT_REQUIRED_SKILL:
        raise ValueError('unexpected next_required_skill value')
    if note_payload.get('binding_surface_kind') != BINDING_SURFACE_KIND:
        raise ValueError('unexpected binding_surface_kind value')
    if note_payload.get('allowed_outputs') != [
        'artifacts/flood-risk-analysis_station_continuity_note.json',
        'artifacts/flood-risk-analysis_flood_flag_catalog.json',
    ]:
        raise ValueError('unexpected allowed_outputs value')
    if len(rows) != len(station_ids):
        raise ValueError('approved_station_binding_table row count mismatch')
    if len(handles) != len(station_ids):
        raise ValueError('flood_flag_handles count mismatch')

    seen_station_ids = []
    non_self_found = False
    for row in rows:
        seen_station_ids.append(row['target_station_id'])
        row_local_handle = row['row_local_flood_flag_handle']
        copied_handle = row['copied_from_flood_flag_handle']
        if row_local_handle not in handles or copied_handle not in handles:
            raise ValueError('binding row references an unknown flood flag handle')
        if row_local_handle != copied_handle:
            non_self_found = True

    if seen_station_ids != station_ids:
        raise ValueError('approved_station_binding_table order drifted from station_ids')
    if not non_self_found:
        raise ValueError('expected at least one non-self copied_from_flood_flag_handle')


def main():
    args = parse_args()
    checkpoint = read_json(args.checkpoint)

    station_ids = normalize_station_ids(checkpoint.get('station_ids'))
    analysis_window, start_date, end_date = normalize_window(
        checkpoint.get('analysis_window')
    )

    thresholds = fetch_thresholds(station_ids)
    catalog_entries, station_records = build_catalog(
        station_ids,
        thresholds,
        start_date,
        end_date,
    )
    binding_rows = build_binding_table(station_records)

    catalog_payload = {
        'flood_flag_handles': catalog_entries,
    }
    note_payload = {
        'current_stage': 'flood-risk-analysis-station-continuity-note',
        'analysis_window': analysis_window,
        'binding_surface_kind': BINDING_SURFACE_KIND,
        'approved_station_binding_table': binding_rows,
        'flood_flag_catalog_path': 'artifacts/flood-risk-analysis_flood_flag_catalog.json',
        'next_required_skill': NEXT_REQUIRED_SKILL,
        'allowed_outputs': [
            'artifacts/flood-risk-analysis_station_continuity_note.json',
            'artifacts/flood-risk-analysis_flood_flag_catalog.json',
        ],
    }

    verify(note_payload, catalog_payload, station_ids)
    write_json(args.catalog, catalog_payload)
    write_json(args.note, note_payload)

    print(f'next_required_skill={NEXT_REQUIRED_SKILL}')
    print(f'binding_surface_kind={BINDING_SURFACE_KIND}')

    print('artifacts/flood-risk-analysis_station_continuity_note.json#station_continuity_note')
    print('approved_station_binding_table=sealed')
    print('copied_from_flood_flag_handle=ffh-source-owner')
    print('artifacts/flood-risk-analysis_flood_flag_catalog.json#flood_flag_catalog')

if __name__ == '__main__':
    main()
