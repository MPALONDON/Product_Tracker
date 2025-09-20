import os
import requests
import pandas as pd
from dotenv import load_dotenv
from io import StringIO

load_dotenv()

API_KEY = os.environ.get("API_KEY")
DATASET_ID = os.environ.get("DATASET_ID")


def scrape_amazon(keywords):

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
    params = {
        "dataset_id": DATASET_ID,
        "include_errors": "true",
        "type": "discover_new",
        "discover_by": "keyword",
    }
    data = [{"keyword": kw} for kw in keywords]

    trigger_response = requests.post(trigger_url, headers=headers, params=params, json=data)

    if trigger_response.status_code != 200:
        raise Exception(f"Trigger failed: {trigger_response.text}")

    trigger_res = trigger_response.json()
    snapshot_id = trigger_res.get("snapshot_id")
    print("Snapshot ID:", snapshot_id)
    return snapshot_id


def fetch_snapshot(snapshot_id):

    headers = {"Authorization": f"Bearer {API_KEY}"}

    data_url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}"
    data_resp = requests.get(data_url, headers=headers)
    data_resp.raise_for_status()

    data = pd.read_json(StringIO(data_resp.text),lines=True)
    filtered_data = data.dropna(subset=['initial_price'])
    return filtered_data