import logging
import os
import threading, dotenv

import main_handler
from arguments import run_args_init
from eassistant_connection import EAssistantService
from google_calendar_connection import GoogleCalendarService
from util import clear_dir, assure_dir, datetime
from meal_prediction import MealPredictorFromDB


logger = logging.getLogger()
THREADING_LOCKS = {}


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

	global logger
	logger.setLevel(dbg_lvl)
	logger.addHandler(consoleHandler)
	logger.addHandler(fileHandler)
	logger.debug(str(args_parsed))
	CALENDAR_NAME = args_parsed.cal_name

	if args_parsed.prune_temp:
		clear_dir("./temp")

	eas: EAssistantService = EAssistantService(MealPredictorFromDB, tuple([os.path.join("temp", "db.db")]))
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
	THREADING_LOCKS["google"] = threading.Lock()
	THREADING_LOCKS["logging"] = threading.Lock()
	main_handler.update_dates(	gcs, eas,
							  	datetime.date.today() + datetime.timedelta(days=6))

	eas.meals.update_day(datetime.date.today()+datetime.timedelta(days=7))

	THREADS = {"events": gcs.create_execution_threads(google_lock=THREADING_LOCKS["google"],
													  logging_lock=THREADING_LOCKS["logging"]),
			   "meals": {}}

	for t_name, t in THREADS["events"].items():
		t.start()

	# Do meal inquiry

	while any([t.isAlive() for t_name, t in THREADS["events"].items()]):
		for t_name, t in THREADS["events"].items():
			t.join(1.0)
			if t.isAlive():
				continue
			meal_thread = THREADS["meals"].get(t_name, None)
			if meal_thread:
				meal_thread.start()

	while any([t.isAlive() for t_name, t in THREADS["meals"].items()]):
		for t_name, t in THREADS["meals"].items():
			t.join(1.0)


if __name__ == '__main__':
	main()
