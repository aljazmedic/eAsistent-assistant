import event_handler as eh
from arguments import arg_init
from eassistant_connection import EAssistantService
from google_calendar_connection import GoogleCalendarService
from misc import *

CALENDAR_ID: str = ""
CALENDAR_NAME: str = ""


def main(arg_object):
	global CALENDAR_NAME, CALENDAR_ID
	CALENDAR_NAME = arg_object.cal_name

	if arg_object.prune_temp:
		clear_dir("./temp")

	eas: EAssistantService = EAssistantService()
	gcs: GoogleCalendarService = GoogleCalendarService(CALENDAR_NAME,
	                                {
		                                  "foregroundColor": "#ECD032",
		                                  "description": "School calendar assistant calendar for subjects, exams, meals and more!",
		                                  "backgroundColor": "#ECD032",
		                                  "timeZone": "Europe/Belgrade",
		                                  "summary": CALENDAR_NAME
	                                  },
	                            remove_if_exists=arg_object.rm_cal)

	eas.introduce()
	"""
	listed_events = gcs.get_events_between(CALENDAR_ID, (datetime.date.today()+datetime.timedelta(days=1), datetime.date.today()+datetime.timedelta(days=2)), q="#school")

	for e in listed_events.get("items", []):
		print(e["start"].get("dateTime", e["start"].get("date", "")), e["summary"], e["description"], sep="\n")
	"""

	eh.update_date(gcs, eas, datetime.date.today()+datetime.timedelta(days=1), datetime.date.today()+datetime.timedelta(days=8))


	# sch_events = eas.get_school_events(datetime.datetime.today()+datetime.timedelta(days=1))
	# eh.add_school_events_to_calendar(gcs, sch_events)


if __name__ == '__main__':
	ar = arg_init()
	logger = logging.getLogger(__name__)
	logging.basicConfig(level=logging.INFO, datefmt='%d-%b%H:%M:%S',
							format='\r%(asctime)-15s (%(relativeCreated)-8d ms) - %(message)s')

	main(ar)
