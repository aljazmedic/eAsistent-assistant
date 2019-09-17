import logging

import threading
import event_handler as eh
from arguments import run_args_init
from eassistant_connection import EAssistantService
from google_calendar_connection import GoogleCalendarService
from misc import *
import os

CALENDAR_ID: str = ""
CALENDAR_NAME: str = ""

logger = logging.getLogger()


def main():
	import logging.config
	args_parsed = run_args_init()
	uniquestr = datetime.datetime.now().strftime("%d-%b_%H%M%S")
	logFormatter = logging.Formatter(
		fmt='\r%(asctime)-15s - (%(relativeCreated)-8d ms) |%(levelname)-7s| @ %(name)s [%(threadName)-12.12s] - %(message)s',
		datefmt='%d-%b %H:%M:%S')
	print(args_parsed)
	if args_parsed.verbose:
		dbg_lvl = logging.DEBUG
	elif args_parsed.quiet:
		dbg_lvl = logging.ERROR
	else:
		dbg_lvl = logging.INFO
	if not os.path.exists(args_parsed.log_dir):
		os.makedirs(args_parsed.log_dir)
	fileHandler = logging.FileHandler(os.path.join(args_parsed.log_dir, args_parsed.log_file_name % uniquestr),
									  mode=args_parsed.log_mode)
	consoleHandler = logging.StreamHandler()
	consoleHandler.setLevel(dbg_lvl)
	fileHandler.setLevel(logging.DEBUG)
	consoleHandler.setFormatter(logFormatter)
	fileHandler.setFormatter(logFormatter)
	global logger
	print(logger, fileHandler, consoleHandler)
	logger.addHandler(consoleHandler)
	logger.addHandler(fileHandler)
	print(logger, fileHandler, consoleHandler)
	# logging.basicConfig(level=dbg_lvl, datefmt='%d-%b %H:%M:%S')
	logger.debug(str(args_parsed))


	global CALENDAR_NAME, CALENDAR_ID
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

	eh.update_date(gcs, eas, datetime.date.today() + datetime.timedelta(days=1), datetime.date.today() + datetime.timedelta(days=1),
				   datetime.date(2019, 9, 27))


if __name__ == '__main__':
	main()
