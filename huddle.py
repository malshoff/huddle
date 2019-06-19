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
          'https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/spreadsheets.readonly'
          ]


PRESENTATION_ID = '1iindiC1jQI8J-c0ZoEDGlCefEQXjK19JDs9bjWbVFXY'
SPREADSHEET_ID = '1ViBwy7VG3J63IwSZDyqvlC5uQF3qC6Lyj4p3DUTzbTg'
TODAYS_DATE = datetime.date.today()
EAST_COAST_ENGINEER_IDS = [123, 52, 17, 116, 51, 128, 40, 140, 119, 127, 142, 143, 31, 91, 115, 42, 136, 126, 114, 147, 77, 124, 145, 85, 72, 117, 121, 135, 146, 144, 150, 129, 154, 133, 141, 12, 134, 138, 137, 151, 118, 149, 148, 16]
employeeAvailability = {key:0 for key in EAST_COAST_ENGINEER_IDS}
UNAVAILABLE_CODES = [9,10,12,13,14,15,16]

credentials = None
EAST_COAST_ENGINEERS = None

with open('east-coast-engineers.json', 'r') as engineers:
    EAST_COAST_ENGINEERS = json.loads(engineers.read())

with open('password.json', 'r') as creds:
    credentials = json.loads(creds.read())


def main():
    bodies = []
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
    #calendar_service = build('calendar', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)

    getNextQB(sheets_service,bodies)
    
    createDate(bodies)
    print("Retrieved Date")
    getAvailability(bodies)
    print("Retrieved Out of Office from Roster")
    requeues(bodies)
    print("Retrieved this morning's requeues")
    #getCalendar(calendar_service,bodies)
    #print('Succesfully Updated Heightened Awareness')
    presentation_copy_id = copyPresentation(drive_service)
    mergeText(service, presentation_copy_id, bodies)
    print('Succesfully created slide deck for ' + str(TODAYS_DATE))
    
    
def getAvailability(bodies):
    r = requests.get('https://pivotal-roster-api.cfapps.io/api/schedule/employee_schedule?audit_date='+str(TODAYS_DATE), auth=(credentials['user'], credentials['pass']))
    engs = r.json()
    for eng in engs:
        engID = eng["engineer"]
        if engID in employeeAvailability:
            employeeAvailability[engID] = eng["availability"]   
    outOfOffice = ''
    for employee in EAST_COAST_ENGINEERS:
        if employeeAvailability[employee["id"]] in UNAVAILABLE_CODES:
            outOfOffice = outOfOffice + employee["first_name"] + " " + employee["last_name"] + ", "
    bodies.append(
        {
            'replaceAllText': {
                'containsText': {
                    'text': '{{OOO}}',
                    'matchCase': True
                },
                'replaceText': outOfOffice
            }
        },
    )

def getNextQB(sheets_service,bodies):
    year, weekNum, dayOfWeek = TODAYS_DATE.isocalendar()
    sheet = sheets_service.spreadsheets()
    nextWeek = weekNum + 1
    sheetRange = "Huddle!A"+str(nextWeek)+":C"+str(nextWeek)
    print("Using sheetRange: " + sheetRange)
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=sheetRange).execute()
    values = result.get('values', [])

    if not values:
        qbs = "None Found"
    else:
        qbs = values[0][1] + " and " + values[0][2]

    bodies.append(
        {
            'replaceAllText': {
                'containsText': {
                    'text': '{{ROTATION}}',
                    'matchCase': True
                },
                'replaceText': qbs
            }
        },
    )

def createDate(bodies):

    # Include the date in the text merge (replaceAllText) request
 
    bodies.append(
        {
            'replaceAllText': {
                'containsText': {
                    'text': '{{DATE}}',
                    'matchCase': True
                },
                'replaceText': str(TODAYS_DATE)
            }
        },
    )

def copyPresentation(drive_service):
    copy_title = 'Daily Huddle ' + str(TODAYS_DATE)
    body = {
        'name': copy_title
    }
    drive_response = drive_service.files().copy(
        fileId=PRESENTATION_ID, body=body).execute()

    return drive_response.get('id')
        
    
def mergeText(service, presentation_copy_id ,bodies):
    
    # Execute the requests for this presentation.
    body = {
        'requests': bodies
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

def getCalendar(calendar_service,bodies):
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

    bodies.append(
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

def requeues(bodies):
    endstr = ''
    with open('password.json', 'r') as creds:
        credentials = json.loads(creds.read())
        r = requests.get('https://salesforce-api-emitter.cfapps.io/api/turnover/cases/?completed=false', auth=(credentials['user'], credentials['pass']))
        #print(r.text)
        for requeue in r.json():
            if not requeue['assignee']:
                endstr = endstr + str(requeue['ticket']) + " " + str(requeue['subject']) + ' - ' + str(requeue['product_name']) + '\n'
        #print(endstr)
        if not endstr:
            endstr = "No Requeues"
        bodies.append(
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
