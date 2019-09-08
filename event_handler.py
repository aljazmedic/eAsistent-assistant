from time import sleep

import event_formatter as ef
from eassistant_connection import EAssistantService
from google_calendar_connection import GoogleCalendarService
from misc import *


def update_date(google_cal_service: GoogleCalendarService, ea_service: EAssistantService, *dates_to_update: datetime.date) -> None:
	# Get school events
	dates_to_update = sorted(dates_to_update)
	if len(dates_to_update) == 1:
		dates_to_update.append(dates_to_update[0])
	eas_events = ea_service.get_school_events(dates_to_update[0], dates_to_update[1]+datetime.timedelta(days=1))
	for date_to_update in dates_to_update:
		time_min, time_max = gstrptime(eas_events["time_boundary"]["min"]), gstrptime(eas_events["time_boundary"]["max"])
		print(time_min, time_max)
		events = eas_events.get("events", [])
		# TODO add time boundary, add notify on special, make sure to prune all events before adding new ones, predict meal time
		for i, e in enumerate(events):
			logging.info(f"{date_to_update}, event {i}.")

			body = ef.google_event_body_from_parsed_event(e)
			google_cal_service.add_event(body)
			sleep(1)

