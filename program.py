import requests, json, time
from random import random
from bs4 import BeautifulSoup
import datetime
import google_calendar_connection as gc
from time import sleep
import logging
from pprint import PrettyPrinter
from misc import *
from notifier import send_notification
from arguments import arg_init
from eassistant_connection import init_session

def ask_for(session, method, url, counter = 0, **kwargs):
	r = session.send(session.prepare_request(requests.Request(method, url, **kwargs)))
	r.encoding = 'ISO-8859-1'
	if r.status_code//100 == 4 and counter < 2:
		print("RETRYING...", counter+1)
		init_session(session)
		return ask_for(session, method, url, counter+1, **kwargs)
	elif counter >= 2:
		print("CANNOT GET", url, r, sep="\n")
		raise Exception("Exception at request", r, url)
	return r

def get_school_week(start_date=datetime.datetime.now()):
	start_date += datetime.timedelta(days=1)

	#Assure we don't parse for saturday or sunday
	while(start_date.weekday() >= 5):
		start_date += datetime.timedelta(days=1)

	return {"from":	 start_date									.strftime("%Y-%m-%d"),
			"to":	(start_date+datetime.timedelta(days=4))		.strftime("%Y-%m-%d")}

def introduce(sess):
	table = ask_for(sess, "GET", "https://www.easistent.com/m/me/child").json()
	logging.info(f"Logged in as {table['display_name']} (ID:{table['id']}), age level: {table['age_level']}")

def get_school_events(sess, **delta_time):
	timetable_payload = get_school_week(datetime.datetime.now() + datetime.timedelta(**delta_time))
	parsed_table = ask_for(sess, "GET", "https://www.easistent.com/m/timetable/weekly", params=timetable_payload).json()
	tmp_save(parsed_table, "timetable_parsed","json")
	#print(parsed_table)	
	time_table_object = to_timetable(parsed_table)
	tmp_save(time_table_object, "timetable_formatted", "json")
	return time_table_object

def add_school_events_to_calendar(google_cal_service, session, calendarId, *args, **kwargs):
	#TODO add time boundary, add notify on special, make sure to prune all events before adding new ones
	sch_events = get_school_events(session, *args, **kwargs)

	local_tz = pytz.timezone(sch_events["time_boundary"]["timeZone"])
	local_tz

	def fm(*args, zone=None):
		if len(args) > 1:
			return [fm(x, zone=zone) for x in args]
		dt = gstrptime(args[0])
		print(dt)
		return gstrftime(zone.localize(dt.replace(tzinfo=None)))

	time_min, time_max = fm(sch_events["time_boundary"]["min"], sch_events["time_boundary"]["max"], zone=local_tz)
	print(time_min, time_max)
	listed_events = google_cal_service.events().list(calendarId=calendarId, timeZone=local_tz.zone, q="#school").execute()
	for e in listed_events.get("items", []):
		print(e["start"].get("dateTime", e["start"].get("date", "")), e["summary"], e["description"], "\n", sep="\n")
	
	L = len(sch_events["events"])
	for i, e in enumerate(sch_events["events"]):
		BODY = google_event_body_from_parsed_event(e)
		google_cal_service.events().insert(calendarId=calendarId, body=BODY).execute()
		progress_line(i+1, L, "events processed!")
		sleep(1)

def main(arg_object):
	with requests.Session() as s:
		if arg_object.prune_temp:
			clear_dir("./temp")

		WORKING_CAL_NAME = arg_object.cal_name

		init_session(s)
		introduce(s)
		CAL = gc.get_authenticated_service()
		if arg_object.rm_cal:
			gc.remove_calendar(CAL, name=WORKING_CAL_NAME)

		calendar_id = gc.assure_calendar(CAL, WORKING_CAL_NAME)["id"]
		add_school_events_to_calendar(CAL, s, calendar_id)


if __name__ == '__main__':
	ar = arg_init()
	logger = logging.getLogger(__name__)
	logging.basicConfig(level=logging.INFO, datefmt='%d-%b-%y %H:%M:%S',
			format='\r%(asctime)-15s (%(relativeCreated)-8d ms) - %(message)s')
	main(ar)