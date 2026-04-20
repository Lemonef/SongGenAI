import requests
import json
import sys

BASE_URL = "https://api.sunoapi.org/api/v1"
API_KEY = "8670dc7732aa68bdea4e95f07331625a"
task_id = "52dbc2d0844e59b3b7112dbb5def19c7"

def _headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

try:
    response = requests.get(
        f"{BASE_URL}/generate/record-info",
        params={"taskId": task_id},
        headers=_headers(),
        timeout=30,
    )
    with open("suno_resp.json", "w", encoding="utf-8") as f:
        f.write(response.text)
except Exception as e:
    print("Exception:", e)
