import os
import pprint

import google.oauth2.credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

import datetime
import pytz, datetime



pp = pprint.PrettyPrinter(indent=2)
GMT_OFF = pytz.utc

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = "private/client_secret.json"
CREDENTIALS_FILE = "private/google_oauth2client_credentials.pickle"

# This access scope grants read-only access to the authenticated user's Drive
# account.
SCOPES = 'https://www.googleapis.com/auth/calendar'
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

def get_authenticated_service():
	creds = None
	if os.path.exists(CREDENTIALS_FILE):
		with open(CREDENTIALS_FILE, "rb") as rf:
			creds = pickle.load(rf)

	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
			creds = flow.run_console()
		with open(CREDENTIALS_FILE, "wb") as wf:
			pickle.dump(creds, wf)

	return build(API_SERVICE_NAME, API_VERSION, credentials = creds)

def find_calendar_by_name(name: str, exactly_one=False) -> list:
	r=[]
	for calendar in results["items"]:
		if calendar["summary"] == name:
			if exactly_one:
				return calendar
			return r.append(calendar)
	return r

def assure_calendar(service, name: str, body = {}):
	if not body:
		body  = {
			"foregroundColor": "#ECD032", # The foreground color of the calendar in the hexadecimal format "#ffffff". This property supersedes the index-based colorId property. To set or change this property, you need to specify colorRgbFormat=true in the parameters of the insert, update and patch methods. Optional.
			"description": "School calendar assistant calendar for subjects, exams, meals and more!", # Description of the calendar. Optional. Read-only.
			"backgroundColor": "#ECD032", # The main color of the calendar in the hexadecimal format "#0088aa". This property supersedes the index-based colorId property. To set or change this property, you need to specify colorRgbFormat=true in the parameters of the insert, update and patch methods. Optional.
			"timeZone": "Europe/Belgrade", # The time zone of the calendar. Optional. Read-only.
			"summary":name
		}

	results = service.calendarList().list().execute() #Get all the calendars
	for calendar in results["items"]: #Find the corresponding calendar
		if calendar["summary"] == name:
			service.calendars().patch(calendarId=calendar["id"], body=body).execute() #Patch it
			return service.calendars().get(calendarId=calendar["id"]).execute() #Return it
	return service.calendars().insert(body=body).execute() #Create it

def remove_calendar(service, calendarId=None, name=None):
	if name:
		calendarId = assure_calendar(service, name)["id"]
	return service.calendars().delete(calendarId=calendarId).execute()

if __name__ == '__main__':
	# When running locally, disable OAuthlib's HTTPs verification. When
	# running in production *do not* leave this option enabled.
	#os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
	CAL = get_authenticated_service()

	pp.pprint(assure_calendar(CAL, "School2"))
	