import os
from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
import os.path
from flask import jsonify

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)

# Define the scopes required for Google Calendar API
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def create_google_calendar_service():
    # Load credentials from token.json or perform OAuth 2.0 authorization if needed
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    # Build the Google Calendar API service
    service = build("calendar", "v3", credentials=creds)
    return service

@app.route("/create_event", methods=["POST"])
def create_event():
    service = create_google_calendar_service()
    
    # Get event details from the request body
    event_data = request.json
    
    # Prepare event data
    event = {
        'summary': event_data.get('summary', 'New Event'),
        'location': event_data.get('location', ''),
        'description': event_data.get('description', ''),
        'start': {
            'dateTime': event_data.get('startDateTime'),
            'timeZone': event_data.get('timeZone', 'UTC'),
        },
        'end': {
            'dateTime': event_data.get('endDateTime'),
            'timeZone': event_data.get('timeZone', 'UTC'),
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    event_id = created_event['id']
    try:
        # Insert the event into the primary calendar
        
        event = service.events().insert(calendarId='primary', body=event).execute()
        return jsonify({'status': 'success', 'event_link': event.get('htmlLink'),'event_id': event_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@app.route("/list_events", methods=["GET"])
def get_events():
    try:
        service = create_google_calendar_service()
        now = datetime.datetime.utcnow().isoformat() + "Z"  
        print("Getting the upcoming 10 events")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            return jsonify({"message": "No upcoming events found."})

        upcoming_events = []
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            upcoming_events.append({"start": start, "summary": event["summary"], 'event_id': event["id"]})

        return jsonify({"upcoming_events": upcoming_events})

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        return jsonify({"message": error_message}), 500

@app.route("/update_event", methods=["PUT"])
def Update_event():
    try:
        #v0r1o2o889d83mdve2l0ju66sc
        # Parse JSON data from the request body
        data = request.json
        event_id = data.get('event_id')
        updated_summary = data.get('summary')
        updated_location = data.get('location')
        updated_start_time = data.get('startDateTime')
        updated_end_time = data.get('endDateTime')

        # Create or retrieve Google Calendar service
        service = create_google_calendar_service()

        # Retrieve the existing event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        # Update event details
        event['summary'] = updated_summary or event['summary']
        event['location'] = updated_location or event.get('location', '')
        if updated_start_time:
            event['start']['dateTime'] = updated_start_time
        if updated_end_time:
            event['end']['dateTime'] = updated_end_time

        # Call the Google Calendar API to update the event
        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()

        return jsonify({'status': 'success', 'updated_event': updated_event})

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        return jsonify({'status': 'error', 'message': error_message}), 500


@app.route("/delete_event", methods=["DELETE"])
def Delete_event():
    try:
        data = request.json
        event_id = data.get('event_id')
        service = create_google_calendar_service()
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return jsonify({'status': 'success', 'message': 'Event deleted successfully'})
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        return jsonify({'status': 'error', 'message': error_message}), 500


if __name__ == "__main__":
    app.run(debug=True)
