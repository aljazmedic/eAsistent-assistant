#!/usr/bin/python3
import pickle
import pprint
from time import sleep
from typing import Union

import logging
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from util import gstrftime, os, datetime, pytz

logger = logging.getLogger(__name__)

logger.debug("Loaded.")

# ignore majority of logs
g_api_logger = logging.getLogger("googleapiclient")
g_api_logger.setLevel(logging.CRITICAL)

class GoogleCalendarService:
	def __init__(self, calendar_name: str, body: dict = None, remove_if_exists: bool = False, timezone="Europe/Belgrade"):
		self.working_calendar = ""
		self.calendar_id = ""

		self.GMT_OFF = pytz.timezone(timezone)

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

		credentials_ = None
		if os.path.exists(CREDENTIALS_FILE):
			with open(CREDENTIALS_FILE, "rb") as rf:
				credentials_ = pickle.load(rf)

		if not credentials_ or not credentials_.valid:
			if credentials_ and credentials_.expired and credentials_.refresh_token:
				credentials_.refresh(Request())
			else:
				flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
				credentials_ = flow.run_console()
			with open(CREDENTIALS_FILE, "wb") as wf:
				pickle.dump(credentials_, wf)

		self.service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials_)

		if remove_if_exists:
			rem_cal = self.find_calendar_by_name(calendar_name, exactly_one=True)
			if rem_cal:
				self.remove_calendar(rem_cal["id"])

		self.working_calendar = self.hook_calendar(calendar_name, body)
		self.calendar_id = self.working_calendar["id"]
		logger.debug(f"Connected to {self.calendar_id}")

	def find_calendar_by_name(self, name: str, exactly_one=False) -> Union[list, dict]:
		r = []
		results = self.service.calendarList().list().execute()  # Get all the calendars
		for calendar in results.get("items", []):
			if calendar["summary"] == name:
				if exactly_one:
					return calendar
				r.append(calendar)
		return r

	def hook_calendar(self, name: object, body: object) -> dict:
		"""
		:param name: calendars name
		:param body: body structure
		(https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/calendar_v3.calendarList.html#insert)
		:return: created calendars dict
		"""
		if not body:
			body = {
				"description": "",
				"timeZone": "Europe/Belgrade",
				"summary": name
			}
		results = self.service.calendarList().list().execute()  # Get all the calendars
		for calendar in results.get("items", []):  # Find the corresponding calendar
			if calendar["summary"] == name:
				self.service.calendars().patch(calendarId=calendar["id"], body=body).execute()  # Patch it
				return self.service.calendars().get(calendarId=calendar["id"]).execute()  # Return it
		self.working_calendar = self.service.calendars().insert(body=body).execute()  # Create it
		self.calendar_id = self.working_calendar["id"]
		return self.working_calendar

	def remove_calendar(self, calendar_id=None, name=None) -> None:
		"""
		:param calendar_id: identifier string of a calendar
		:param name: name of the calendar
		:return:
		"""
		if name:
			calendar = self.find_calendar_by_name(name, exactly_one=True)
			if not calendar:
				return None
			calendar_id = calendar["id"]
		return self.service.calendars().delete(calendarId=calendar_id).execute()

	def get_events_between(self, time_tuple: tuple, **list_args) -> dict:
		"""
		:param time_tuple: time boundary of min and max time
		:param list_args: q="*", ...
		"""
		time_min, time_max = [gstrftime(x, tz_force=self.GMT_OFF) for x in time_tuple]

		return self.service.events().list(calendarId=self.calendar_id, timeZone=self.GMT_OFF,
		                                  timeMin=time_min, timeMax=time_max, **list_args).execute()

	def add_event(self, event_body: dict) -> dict:
		sleep(1)
		try:
			return self.service.events().insert(calendarId=self.calendar_id, body=event_body).execute()
		except Exception as e:
			logger.debug("Error adding:\n"+str(event_body))
			logger.error(e)

	def update_event(self, event_id: str, event_body: dict, **patch_kwargs) -> dict:
		sleep(1)
		try:
			return self.service.events().update(calendarId=self.calendar_id, eventId=event_id, body=event_body, **patch_kwargs).execute()
		except Exception as e:
			logger.debug("Error updating:\n"+str(event_body))
			logger.error(e)

	def remove_event(self, event_id: str, **remove_kwargs):
		sleep(1)
		try:
			return self.service.events().delete(calendarId=self.calendar_id, eventId=event_id, **remove_kwargs).execute()
		except Exception as e:
			logger.debug("Error removing")
			logger.error(e)


if __name__ == '__main__':
	# When running locally, disable OAuthlib's HTTPs verification. When
	# running in production *do not* leave this option enabled.
	# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

	pp = pprint.PrettyPrinter(indent=2)
	gcs = GoogleCalendarService("School2")

	pp.pprint(gcs.get_events_between((datetime.datetime.now().date() + datetime.timedelta(days=3),
	                                  datetime.datetime.now().date() + datetime.timedelta(days=4)), q="#school")["items"])
