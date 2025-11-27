import datetime
import json
import os
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIGURATION ---
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Your specific email is the target calendar
TARGET_CALENDAR_ID = 'devanshgarg024@gmail.com' 

def get_codeforces_contests():
    print("Fetching contests from Codeforces...")
    try:
        url = "https://codeforces.com/api/contest.list"
        # We only want official contests (gym=false)
        resp = requests.get(url, params={"gym": "false"}).json()
        
        if resp["status"] != "OK":
            return []
        
        # Filter for upcoming contests only (phase="BEFORE")
        upcoming = [c for c in resp["result"] if c["phase"] == "BEFORE"]
        return upcoming
    except Exception as e:
        print(f"Error fetching Codeforces: {e}")
        return []

def auth_service_account():
    # Load the secret from the environment variable (GCP_SA_KEY)
    if 'GCP_SA_KEY' not in os.environ:
        print("Error: GCP_SA_KEY environment variable not found.")
        return None

    service_account_info = json.loads(os.environ['GCP_SA_KEY'])
    creds = service_account.Credentials.from_service_account_info(
        service_account_info, scopes=SCOPES
    )
    return creds

def add_to_calendar(service, contest):
    # Unique ID to prevent duplicates (e.g., cf1950)
    unique_id = f"cf{contest['id']}_v2"
    
    # Calculate start and end times
    start_dt = datetime.datetime.fromtimestamp(contest['startTimeSeconds'])
    end_dt = start_dt + datetime.timedelta(seconds=contest['durationSeconds'])
    
    # Define the event details
    event_body = {
        'id': unique_id, 
        'summary': f"CF: {contest['name']}",
        'description': f"Link: https://codeforces.com/contest/{contest['id']}",
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
    }

    try:
        # Try to insert the event
        service.events().insert(calendarId=TARGET_CALENDAR_ID, body=event_body).execute()
        print(f"ADDED: {contest['name']}")

    except HttpError as error:
        # If error is 409, the ID is taken.
        if error.resp.status == 409:
            try:
                # Attempt to fetch the event
                existing_event = service.events().get(
                    calendarId=TARGET_CALENDAR_ID, 
                    eventId=unique_id
                ).execute()

                if existing_event['status'] == 'cancelled':
                    print(f"Restoring deleted event: {contest['name']}...")
                    event_body['status'] = 'confirmed' 
                    service.events().update(
                        calendarId=TARGET_CALENDAR_ID, 
                        eventId=unique_id, 
                        body=event_body
                    ).execute()
                    print(f"RESTORED: {contest['name']}")
                else:
                    print(f"EXISTS: {contest['name']}")

            except HttpError as inner_error:
                # If we get a 403 here, we can't read the event. Just skip it.
                if inner_error.resp.status == 403:
                    print(f"PERMISSION DENIED: Could not check details for {contest['name']}. Check Calendar settings.")
                else:
                    print(f"Could not check existing event: {inner_error}")
        else:
            print(f"An error occurred: {error}")

def main():
    creds = auth_service_account()
    if not creds:
        return

    service = build('calendar', 'v3', credentials=creds)
    contests = get_codeforces_contests()
    print(f"Found {len(contests)} upcoming contests.")
    
    for c in contests:
        add_to_calendar(service, c)

if __name__ == '__main__':
    main()