from eassistant_connection import EAssistantService
from google_calendar_connection import GoogleCalendarService
from misc import *


def events_start_at_same_time(e1: dict, e2: dict, no_timezone: bool = False) -> bool:
	s1 = e1["start"].get("dateTime", e1.get("date", ""))
	s2 = e2["start"].get("dateTime", e1.get("date", ""))
	if no_timezone:
		s1, s2 = s1[:19], s2[:19]
	logging.debug("Comparing " + s1 + " & " + s2)
	return s1 == s2


def update_date(google_cal_service: GoogleCalendarService, ea_service: EAssistantService, *dates_to_update: datetime.date) -> None:
	# Get school events
	dates_to_update = sorted(dates_to_update)
	if len(dates_to_update) == 1:
		dates_to_update.append(dates_to_update[0])
	eas_events = ea_service.get_school_events(dates_to_update[0], dates_to_update[1]+datetime.timedelta(days=1))
	print(eas_events["time_boundary"]["min"], eas_events["time_boundary"]["max"])
	time_min, time_max = gstrptime(eas_events["time_boundary"]["min"]), gstrptime(eas_events["time_boundary"]["max"])
	print(time_min, time_max)

	events_from_cal = google_cal_service.get_events_between((time_min, time_max), q="#school", orderBy="startTime", singleEvents=True)

	events_to_enter = eas_events.get("events", [])
	events_google = events_from_cal.get("items", [])
	logging.debug("Retrieved events: " + str(events_google))
	# TODO add time boundary, add notify on special, make sure to prune all events before adding new ones, predict meal time
	for i, e in enumerate(events_to_enter):
		body = ea_service.ef.google_event_body_from_parsed_event(e)
		event_updated = False
		i_event = 0
		# check common starting events
		for e_google in events_google:
			if events_start_at_same_time(e, e_google, no_timezone=True):
				logging.debug("Events start at same time")
				if not event_updated:
					logging.info("Patching:")
					google_cal_service.update_event(event_id=e_google["id"], event_body=body)
					event_updated = True
				else:
					# duplicate event
					logging.info("Removing:")
					google_cal_service.remove_event(event_id=e_google["id"])
				events_google.pop(i_event)

		# there were no common events
		if not event_updated:
			# no common events
			logging.info("Adding:")
			google_cal_service.add_event(body)

