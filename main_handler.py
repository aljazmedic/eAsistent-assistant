#!/usr/bin/python3

import logging

from eassistant_connection import EAssistantService
from google_calendar_connection import GoogleCalendarService
from util import gstrptime, datetime, get_event_start

logger = logging.getLogger(__name__)


def _update_single_date(google_cal_service: GoogleCalendarService, date_construct: dict, date: str) -> None:
	"""
	:param google_cal_service:
	:param date_construct: dictionary with entries for time
	:param date:
	:return:
	"""
	"""
	"08:15:00":{
		"easistent":[events],
		"google":[events]
	},
	...
	"""

	def list_safe_get(l: list, idx: int, default=None):
		try:
			return l[idx]
		except IndexError:
			return default

	for e_time, all_events in date_construct.items():
		google_events = all_events.get("google", [])
		easistent_events = all_events.get("easistent", [])

		for i in range(max(len(google_events), len(easistent_events))):
			g_ev, ea_ev = list_safe_get(google_events, i), list_safe_get(easistent_events, i)

			if ea_ev and g_ev:
				# patch google event
				google_cal_service.update_event(event_id=g_ev["id"], event_body=ea_ev, execution_thread=date)
				logger.debug(get_event_start(ea_ev) + " Patch queued.")
			elif ea_ev and not g_ev:
				# create google event from ea_ev
				google_cal_service.add_event(ea_ev, execution_thread=date)
				logger.debug(get_event_start(ea_ev) + " Add queued.")
			elif not ea_ev and g_ev:
				# remove google event
				google_cal_service.remove_event(event_id=g_ev["id"], execution_thread=date)
				logger.debug(get_event_start(g_ev) + " Remove queued.")


def update_dates(google_cal_service: GoogleCalendarService, ea_service: EAssistantService, *dates_to_update: datetime.date):
	# Get school events
	dates_to_update = sorted(dates_to_update)
	if len(dates_to_update) == 1:
		dates_to_update.append(dates_to_update[0])
	eas_events = ea_service.get_school_events(dates_to_update[0], dates_to_update[1]+datetime.timedelta(days=1))
	logger.info("Events time boundary: " + str(eas_events["time_boundary"]))
	time_min, time_max = gstrptime(eas_events["time_boundary"]["min"]), gstrptime(eas_events["time_boundary"]["max"])

	events_from_cal = google_cal_service.get_events_between((time_min, time_max), q="#school", orderBy="startTime", singleEvents=True)

	events_to_enter = eas_events.get("events", [])
	events_google = events_from_cal.get("items", [])

	logger.debug("Retrieved google events: " + str(len(events_google)))
	logger.debug("Easistent events:        " + str(len(events_to_enter)))

	# Create event list sorted by day
	EVENTS_BY_DAY = {}

	for event in events_to_enter:
		etime = get_event_start(event)
		etime, date = etime[11:19], etime[:10]  # only the date part
		if date not in EVENTS_BY_DAY:
			EVENTS_BY_DAY[date] = {}
		if etime not in EVENTS_BY_DAY[date]:
			EVENTS_BY_DAY[date][etime] = {}
		_, f_event = ea_service.ef.google_event_body_from_parsed_event(event)
		if "easistent" not in EVENTS_BY_DAY[date][etime]:
			EVENTS_BY_DAY[date][etime]["easistent"] = [f_event]
		else:
			EVENTS_BY_DAY[date][etime]["easistent"].append(f_event)

	for g_event in events_google:
		etime = get_event_start(g_event)
		etime, date = etime[11:19], etime[:10]  # only the date part
		if date not in EVENTS_BY_DAY:
			EVENTS_BY_DAY[date] = {}
		if etime not in EVENTS_BY_DAY[date]:
			EVENTS_BY_DAY[date][etime] = {}
		if "google" not in EVENTS_BY_DAY[date][etime]:
			EVENTS_BY_DAY[date][etime]["google"] = [g_event]
		else:
			EVENTS_BY_DAY[date][etime]["google"].append(g_event)

	for date, construct in EVENTS_BY_DAY.items():
		_update_single_date(google_cal_service, construct, date)
