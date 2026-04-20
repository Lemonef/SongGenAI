import requests
import json
import time

BASE_URL = "https://api.sunoapi.org/api/v1"
API_KEY = "8670dc7732aa68bdea4e95f07331625a"
callback_url = "https://disliking-algebra-destitute.ngrok-free.dev/generation/suno/callback/"

def _headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

payload = {
    "prompt": "a test song two",
    "style": "Pop Happy",
    "title": "Test Song",
    "model": "V4_5ALL",
    "customMode": True,
    "instrumental": True,
    "callBackUrl": callback_url,
    "negativeTags": "Heavy Metal, Upbeat Drums",
    "vocalGender": "m",
    "styleWeight": 0.65,
    "weirdnessConstraint": 0.65,
    "audioWeight": 0.65,
}

response = requests.post(
    f"{BASE_URL}/generate",
    json=payload,
    headers=_headers(),
    timeout=30,
)
data = response.json()
task_id = data.get("data", {}).get("taskId") or data.get("taskId")

time.sleep(2)

resp2 = requests.get(
    f"{BASE_URL}/generate/record-info",
    params={"taskId": task_id},
    headers=_headers(),
    timeout=30,
)
with open("suno_pending_resp.json", "w", encoding="utf-8") as f:
    json.dump(resp2.json(), f, indent=2)

