import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("API_KEY")
DATASET_ID = os.environ.get("DATASET_ID")


def scrape_amazon(keywords, max_wait=900):

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



