import logging
import os
from threading import Thread

import main_handler
from arguments import run_args_init
from eassistant_connection import EAssistantService
from google_calendar_connection import GoogleCalendarService
from util import clear_dir, datetime
from meal_prediction import MealPredictorFromDB
import assure_packages

logger = logging.getLogger()


def setup_loggers(args_parsed):
	uniquestr = datetime.datetime.now().strftime("%d-%b_%H%M%S")
	logFormatter = logging.Formatter(
		fmt='%(asctime)-15s - (%(relativeCreated)-8d ms) |%(levelname)-7s| @ [%(threadName)-12.12s] %(name)15.15s - %(message)s',
		datefmt='%d-%b %H:%M:%S')
	dbg_lvl = args_parsed.log_level
	os.makedirs(args_parsed.log_dir, exist_ok=True)

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


def main():
	args_parsed = run_args_init()
	assure_packages.install_pip("19.3.1", args_parsed.log_level)
	assure_packages.install_requirements(args_parsed.log_level)
	setup_loggers(args_parsed)
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

	if args_parsed.days:
		days = set()
		for delta_days in args_parsed.days:
			rel_days = {
				"today": 0,
				"yesterday": -1,
				"tomorrow": 1,
				"next_week": 7
			}
			try:
				delta_days = rel_days.get(delta_days, int(delta_days))
			except ValueError:
				logging.warning(f"Unknown day value: {delta_days}!")
			days.add(datetime.date.today() + datetime.timedelta(days=delta_days))
	else:
		days = [datetime.date.today() + datetime.timedelta(days=1*7),
				datetime.date.today() + datetime.timedelta(days=2*7)]

	main_handler.update_dates(	gcs, eas, *days)
	if args_parsed.meals:
		eas.meals.update_meals(gcs, *days)
	THREADS = {
		"events": {},
		"meals": {}
	}
	gcs.create_execution_threads(
						save_to=THREADS["events"]
						)
	eas.meals.create_execution_threads(
						save_to=THREADS["meals"])

	for t_name, t in THREADS["events"].items():
		t.start()

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
