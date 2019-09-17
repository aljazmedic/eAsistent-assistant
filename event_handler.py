from eassistant_connection import EAssistantService
from google_calendar_connection import GoogleCalendarService
from misc import *


def get_event_start(e: dict) -> str:
	return e["start"].get("dateTime", e["start"].get("date", ""))


def events_start_at_same_time(e1: dict, e2: dict, no_timezone: bool = False) -> bool:
	s1 = get_event_start(e1)
	s2 = get_event_start(e2)
	if no_timezone:
		s1, s2 = s1[:19], s2[:19]
	return s1 == s2


def update_date(google_cal_service: GoogleCalendarService, ea_service: EAssistantService, *dates_to_update: datetime.date) -> None:
	# Get school events
	dates_to_update = sorted(dates_to_update)
	if len(dates_to_update) == 1:
		dates_to_update.append(dates_to_update[0])
	eas_events = ea_service.get_school_events(dates_to_update[0], dates_to_update[1]+datetime.timedelta(days=1))
	logging.info("Events time boundary: " + str(eas_events["time_boundary"]))
	time_min, time_max = gstrptime(eas_events["time_boundary"]["min"]), gstrptime(eas_events["time_boundary"]["max"])

	events_from_cal = google_cal_service.get_events_between((time_min, time_max), q="#school", orderBy="startTime", singleEvents=True)

	events_to_enter = eas_events.get("events", [])
	events_google = events_from_cal.get("items", [])
	logging.debug("Retrieved google events: " + str(len(events_google)))
	logging.debug("Easistent events: " + str(len(events_to_enter)))
	# TODO add notify on special, predict meal time
	for i, e in enumerate(events_to_enter):
		special, body = ea_service.ef.google_event_body_from_parsed_event(e)
		if special:
			logging.info("Special: " + special)
		event_updated = False
		i_event = 0
		# check common starting events
		for e_google in events_google:
			if events_start_at_same_time(e, e_google, no_timezone=True):
				# logging.debug("Events starting at same time")
				if not event_updated:
					google_cal_service.update_event(event_id=e_google["id"], event_body=body)
					logging.info(get_event_start(body) + " Patched.")
					event_updated = True
				else:
					# duplicate event
					google_cal_service.remove_event(event_id=e_google["id"])
					logging.info(get_event_start(e_google) + " Removed.")
				events_google.pop(i_event)

		# there were no common events
		if not event_updated:
			# no common events
			google_cal_service.add_event(body)
			logging.info(get_event_start(body) + " Added.")
