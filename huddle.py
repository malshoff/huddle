from __future__ import print_function
import pickle
import os.path
import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/presentations',
          'https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/calendar'
          ]

# The ID of a sample presentation.
PRESENTATION_ID = '1iindiC1jQI8J-c0ZoEDGlCefEQXjK19JDs9bjWbVFXY'


def main():
    
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('slides', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    calendar_service = build('calendar', 'v3', credentials=creds)

    mergeText(service, drive_service)
    print('Merged text Succesfully')
    getCalendar(calendar_service)
    print('Succesfully Updated Heightened Awareness')
    
def mergeText(service, drive_service):
    todays_date = str(datetime.date.today())
    # Duplicate the template presentation using the Drive API.
    copy_title = 'Daily Huddle ' + todays_date
    body = {
        'name': copy_title
    }
    drive_response = drive_service.files().copy(
        fileId=PRESENTATION_ID, body=body).execute()
    presentation_copy_id = drive_response.get('id')

    # Create the text merge (replaceAllText) requests
    # for this presentation.
    requests = [
        {
            'replaceAllText': {
                'containsText': {
                    'text': '{{DATE}}',
                    'matchCase': True
                },
                'replaceText': todays_date
            }
        },
    ]

    # Execute the requests for this presentation.
    body = {
        'requests': requests
    }
    response = service.presentations().batchUpdate(
        presentationId=presentation_copy_id, body=body).execute()

    # Count the total number of replacements made.
    num_replacements = 0
    for reply in response.get('replies'):
        num_replacements += reply.get('replaceAllText') \
            .get('occurrencesChanged')
        print('Created presentation ID: %s' % presentation_copy_id)
        print('Replaced %d text instances' % num_replacements)

def getCalendar(calendar_service):
    CALENDAR_ID = 'pivotal.io_lq4bhr6dgtnhmlj3fc82g4o3c4@group.calendar.google.com'

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = calendar_service.events().list(calendarId=CALENDAR_ID,timeMin=now,
                                        singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No current HA events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])

if __name__ == '__main__':
    main()
