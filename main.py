import datetime
import json
import os
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIGURATION ---
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary' # This refers to the robot's primary calendar OR the one you shared
# If 'primary' doesn't work, use your actual gmail address as the ID (e.g., 'yourname@gmail.com')
TARGET_CALENDAR_ID = 'devanshgarg024@gmail.com' 

def get_codeforces_contests():
    # ... (Same as your previous code) ...
    try:
        url = "https://codeforces.com/api/contest.list"
        resp = requests.get(url, params={"gym": "false"}).json()
        if resp["status"] != "OK": return []
        upcoming = [c for c in resp["result"] if c["phase"] == "BEFORE"]
        return upcoming
    except Exception as e:
        print(f"Error fetching Codeforces: {e}")
        return []

def auth_service_account():
    # Load the secret from the environment variable
    service_account_info = json.loads(os.environ['GCP_SA_KEY'])
    creds = service_account.Credentials.from_service_account_info(
        service_account_info, scopes=SCOPES
    )
    return creds

def add_to_calendar(service, contest):
    unique_id = f"cf{contest['id']}"
    # ... (Same logic as before) ...
    
    start_dt = datetime.datetime.fromtimestamp(contest['startTimeSeconds'])
    end_dt = start_dt + datetime.timedelta(seconds=contest['durationSeconds'])
    
    event_body = {
        'id': unique_id, 
        'summary': f"CF: {contest['name']}",
        'description': f"Link: https://codeforces.com/contest/{contest['id']}",
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Asia/Kolkata'},
    }

    try:
        # NOTICE: We use TARGET_CALENDAR_ID here
        service.events().insert(calendarId=TARGET_CALENDAR_ID, body=event_body).execute()
        print(f"ADDED: {contest['name']}")
    except HttpError as error:
        if error.resp.status == 409:
            print(f"EXISTS: {contest['name']}")
        else:
            print(f"Error: {error}")

def main():
    creds = auth_service_account()
    service = build('calendar', 'v3', credentials=creds)
    contests = get_codeforces_contests()
    for c in contests:
        add_to_calendar(service, c)

if __name__ == '__main__':
    main()