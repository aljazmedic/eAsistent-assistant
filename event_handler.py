#!/usr/bin/python3

import json
import logging
import threading

from eassistant_connection import EAssistantService
from google_calendar_connection import GoogleCalendarService
from misc import gstrptime, datetime

logger = logging.getLogger(__name__)


def get_event_start(e: dict) -> str:
	return e["start"].get("dateTime", e["start"].get("date", ""))


def events_start_at_same_time(e1: dict, e2: dict, no_timezone: bool = False) -> bool:
	s1 = get_event_start(e1)
	s2 = get_event_start(e2)
	if no_timezone:
		s1, s2 = s1[:19], s2[:19]
	return s1 == s2


def _update_single_date(google_cal_service: GoogleCalendarService, date_construct: dict, date: str, threading_lock: threading.Lock, google_lock: threading.Lock) -> None:
	"""
	:param google_cal_service:
	:param ea_service:
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
	with threading_lock:
		logger.debug(f"Updating {date}")
	for e_time, all_events in date_construct.items():
		google_events = all_events.get("google", [])
		easistent_events = all_events.get("easistent", [])

		for g_ev, ea_ev in zip(google_events, easistent_events):
			if ea_ev and g_ev:
				# patch google event
				with google_lock:
					google_cal_service.update_event(event_id=g_ev["id"], event_body=ea_ev)
				with threading_lock:
					logger.debug(get_event_start(ea_ev) + " Patched.")
			elif ea_ev and not g_ev:
				# create google event from ea_ev
				with google_lock:
					google_cal_service.add_event(ea_ev)
				with threading_lock:
					logger.debug(get_event_start(ea_ev) + " Added.")
			elif not ea_ev and g_ev:
				# remove google event
				with google_lock:
					google_cal_service.remove_event(event_id=g_ev["id"])
				with threading_lock:
					logger.debug(get_event_start(g_ev) + " Removed.")
	with threading_lock:
		logger.debug(f"Finished {date}")


def update_dates(google_cal_service: GoogleCalendarService, ea_service: EAssistantService, *dates_to_update: datetime.date, google_lock: threading.Lock, logging_lock: threading.Lock) -> list:
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
	logger.debug("Easistent events: " + str(len(events_to_enter)))

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

	threads = []
	for date, construct in EVENTS_BY_DAY.items():
		threads.append(threading.Thread(target=_update_single_date, daemon=True, args=(google_cal_service, construct, date, logging_lock, google_lock), name=f'thread_{date[5:]}'))
	return threads
