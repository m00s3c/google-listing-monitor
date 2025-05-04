import json
import requests
import os
import sys
from datetime import datetime

CONFIG_FILE = 'config.json'
BASELINE_FILE = 'baseline.json'
LAST_SEEN_FILE = 'last_seen.json'

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def get_place_details(api_key, place_id, fields):
    endpoint = 'https://maps.googleapis.com/maps/api/place/details/json'
    params = {
        'place_id': place_id,
        'fields': ','.join(fields),
        'key': api_key
    }
    res = requests.get(endpoint, params=params)
    data = res.json()
    if data.get('status') != 'OK':
        print(f"[{datetime.now()}] ERROR fetching {place_id}: {data.get('status')}")
        return None
    return data['result']

def compare_data(label, place_id, baseline, current):
    changes = {}
    for k in baseline:
        if baseline.get(k) != current.get(k):
            changes[k] = {
                "expected": baseline.get(k),
                "actual": current.get(k)
            }
    return changes

def main():
    config = load_json(CONFIG_FILE)
    baseline = load_json(BASELINE_FILE)
    last_seen = {}
    
    api_key = config.get("api_key")
    listings = config.get("listings", [])
    fields = config.get("fields_to_monitor", [])

    if not api_key or not listings:
        print("Missing API key or listings.")
        sys.exit(1)

    for listing in listings:
        place_id = listing.get("place_id")
        label = listing.get("label", place_id)
        current_data = get_place_details(api_key, place_id, fields)
        if not current_data:
            continue

        last_seen[place_id] = current_data

        baseline_data = baseline.get(place_id, {})
        if not baseline_data:
            print(f"[{datetime.now()}] WARNING: No baseline for {label} ({place_id}). Add it to baseline.json.")
            continue

        changes = compare_data(label, place_id, baseline_data, current_data)
        if changes:
            print(f"[{datetime.now()}] ⚠️  Changes detected for {label} ({place_id}):")
            for field, val in changes.items():
                print(f"  - {field}: expected '{val['expected']}', got '{val['actual']}'")
        else:
            print(f"[{datetime.now()}] ✅ No changes for {label} ({place_id})")

    save_json(LAST_SEEN_FILE, last_seen)

if __name__ == '__main__':
    main()
