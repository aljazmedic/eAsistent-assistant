import logging
import os
import threading

import event_handler as eh
from arguments import run_args_init
from eassistant_connection import EAssistantService
from google_calendar_connection import GoogleCalendarService
from misc import clear_dir, assure_dir, datetime

logger = logging.getLogger()

CALENDAR_ID: str = ""
CALENDAR_NAME: str = ""


def main():
	args_parsed = run_args_init()
	uniquestr = datetime.datetime.now().strftime("%d-%b_%H%M%S")
	logFormatter = logging.Formatter(
		fmt='%(asctime)-15s - (%(relativeCreated)-8d ms) |%(levelname)-7s| @ [%(threadName)-12.12s] %(name)15.15s - %(message)s',
		datefmt='%d-%b %H:%M:%S')
	if args_parsed.verbose:
		dbg_lvl = logging.DEBUG
		print("Verbose mode:")
	elif args_parsed.quiet:
		dbg_lvl = logging.WARNING
	else:
		dbg_lvl = logging.INFO
	assure_dir(args_parsed.log_dir)
	fileHandler = logging.FileHandler(os.path.join(args_parsed.log_dir, args_parsed.log_file_name % uniquestr),
									  mode=args_parsed.log_mode)

	consoleHandler = logging.StreamHandler()
	consoleHandler.setLevel(dbg_lvl)
	fileHandler.setLevel(logging.DEBUG)
	consoleHandler.setFormatter(logFormatter)
	fileHandler.setFormatter(logFormatter)

	global logger, CALENDAR_NAME, CALENDAR_ID
	logger.setLevel(dbg_lvl)
	logger.addHandler(consoleHandler)
	logger.addHandler(fileHandler)
	logger.debug(str(args_parsed))
	CALENDAR_NAME = args_parsed.cal_name

	if args_parsed.prune_temp:
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
													   remove_if_exists=args_parsed.rm_cal)

	eas.introduce()

	threads = eh.update_dates(gcs,
							  eas,
							  datetime.date.today() + datetime.timedelta(days=1),
							  datetime.date(2019, 9, 27),
							  threaded=True)

	for t in threads:
		t.start()

	for t in threads:
		t.join(timeout=1)


if __name__ == '__main__':
	main()
