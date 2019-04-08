from __future__ import print_function

import datetime
import os.path
import pickle
import json
import requests
from requests.auth import HTTPBasicAuth

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/presentations',
          'https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/calendar'
          ]

# The ID of a sample presentation.
PRESENTATION_ID = '1iindiC1jQI8J-c0ZoEDGlCefEQXjK19JDs9bjWbVFXY'
TODAYS_DATE = str(datetime.date.today())



def main():
    requests = []
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

    presentation_copy_id = copyPresentation(drive_service)
    createDate(requests)
    getCalendar(calendar_service,requests)
    mergeText(service, presentation_copy_id, requests)
    print('Merged text Succesfully')
    getCalendar(calendar_service)
    print('Succesfully Updated Heightened Awareness')

def createDate(requests):

    # Include the date in the text merge (replaceAllText) request
 
    requests.append(
        {
            'replaceAllText': {
                'containsText': {
                    'text': '{{DATE}}',
                    'matchCase': True
                },
                'replaceText': TODAYS_DATE
            }
        },
    )

def copyPresentation(drive_service):
    copy_title = 'Daily Huddle ' + TODAYS_DATE
    body = {
        'name': copy_title
    }
    drive_response = drive_service.files().copy(
        fileId=PRESENTATION_ID, body=body).execute()

    return drive_response.get('id')
        
    
def mergeText(service, presentation_copy_id ,requests):
    
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

def getCalendar(calendar_service,requests):
    CALENDAR_ID = 'pivotal.io_lq4bhr6dgtnhmlj3fc82g4o3c4@group.calendar.google.com'

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the current HA events')
    events_result = calendar_service.events().list(calendarId=CALENDAR_ID,timeMin=now,
                                        singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])
    allEvents = ''

    if not events:
        print('No current HA events found.')
    for event in events:
        allEvents = allEvents + event['summary'] + ', '
        print(event['summary'])

    requests.append(
        {
            'replaceAllText': {
                'containsText': {
                    'text': '{{HA}}',
                    'matchCase': True
                },
                'replaceText': allEvents
            }
        },
    )

def requeues(requests):
    endstr = ''
    with open('password.json', 'r') as creds:
        credentials = json.loads(creds.read())
        r = requests.get('https://salesforce-api-emitter.cfapps.io/api/turnover/cases/?completed=false', auth=(credentials['user'], credentials['pass']))
        #print(r.text)
        for requeue in r.json():
            endstr = endstr + requeue['ticket'] + " " + requeue['subject'] + ' ' + requeue['product_name'] + '\n'

        requests.append(
        {
            'replaceAllText': {
                'containsText': {
                    'text': '{{RQ}}',
                    'matchCase': True
                },
                'replaceText': endstr
            }
        },
        )
if __name__ == '__main__':
    main()
