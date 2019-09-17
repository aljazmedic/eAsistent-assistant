import threading
import event_handler as eh
from arguments import run_args_init
from eassistant_connection import EAssistantService
from google_calendar_connection import GoogleCalendarService
from misc import *

CALENDAR_ID: str = ""
CALENDAR_NAME: str = ""


def main(args):
	global CALENDAR_NAME, CALENDAR_ID
	CALENDAR_NAME = args.cal_name

	if args.prune_temp:
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
													   remove_if_exists=args.rm_cal)

	eas.introduce()
	"""
	listed_events = gcs.get_events_between(CALENDAR_ID, (datetime.date.today()+datetime.timedelta(days=1), datetime.date.today()+datetime.timedelta(days=2)), q="#school")

	for e in listed_events.get("items", []):
		print(e["start"].get("dateTime", e["start"].get("date", "")), e["summary"], e["description"], sep="\n")
	"""

	eh.update_date()


if __name__ == '__main__':
	ar = run_args_init()
	print(ar)
	logger = logging.getLogger(__name__)
	logging.basicConfig(level=logging.DEBUG, datefmt='%d-%b %H:%M:%S', filename=ar.log_file_name, filemode=ar.log_mode,
						format='\r%(asctime)-15s|%(relativeCreated)-8d ms|%(levelname)-7s| - %(message)s')

	main(ar)
