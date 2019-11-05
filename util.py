#!/usr/bin/python3
import datetime
import json
import os
import shutil

import iso8601
import logging
import pytz
import requests
import tzlocal
import dotenv
import threading
from typing import Union, Optional, Dict, List, Tuple, Any
from deprecated import deprecated

DEFAULT_TIMEZONE = "Europe/Belgrade"

logger = logging.logger = logging.getLogger(__name__)
dotenv.set_key(os.path.join(os.curdir, ".env"), key_to_set="SA_DOTENV_DIR", value_to_set=os.path.join(os.curdir, ".env"))
GETTING_LOCK = threading.Lock()
THREADING_LOCKS = {}


def list_safe_get(l, idx, default=None):
	# type: (List, int, Optional[Any]) -> Any
	try:
		return l[idx]
	except IndexError:
		return default


def events_start_at_same_time(e1: dict, e2: dict, no_timezone: bool = False) -> bool:
	s1 = get_event_start(e1)
	s2 = get_event_start(e2)
	if no_timezone:
		s1, s2 = s1[:19], s2[:19]
	return s1 == s2


def get_create(d, k, v):
	# type: (Dict, str, Any) -> Any
	""" Retrieves key, if there was none it creates it and returns it"""
	if k not in d:
		d[k] = v
	return d[k]


def get_tlock(name):
	# type: (str) -> threading.Lock
	""" Retrieves global threading locks"""
	with GETTING_LOCK:
		if name not in THREADING_LOCKS:
			THREADING_LOCKS[name] = threading.Lock()
		return THREADING_LOCKS[name]


def get_school_week(dt):
	# type:(datetime.date) -> int
	""" Retrieves consecutive number of school week"""
	first_day = datetime.date(dt.year, 9, 1)
	while first_day.weekday() >= 5:
		first_day += datetime.timedelta(days=1)
	return dt.isocalendar()[1] - first_day.isocalendar()[1]


def ask_for(session, method, url, counter=0, **kwargs):
	r = session.send(session.prepare_request(requests.Request(method, url, **kwargs)))
	r.encoding = 'ISO-8859-1'
	if r.status_code // 100 == 4 and counter < 2:
		print("RETRYING...", counter + 1)
		return ask_for(session, method, url, counter + 1, **kwargs)
	elif counter >= 2:
		print("CANNOT GET", url, r, sep="\n")
		raise Exception("Exception at request", r, url)
	return r


def clear_dir(folder):
	for the_file in os.listdir(folder):
		file_path = os.path.join(folder, the_file)
		try:
			if os.path.isfile(file_path):
				os.unlink(file_path)
			elif os.path.isdir(file_path):
				shutil.rmtree(file_path)
		except Exception as e:
			logger.exception(e)


def load_dotenv():
	""" Loads dotenv from project wide .env file"""
	dotenv.load_dotenv(os.getenv("SA_DOTENV_DIR", os.path.join(os.curdir, ".env")))


def write_to_dotenv(key, value):
	# type: (str, Any) -> Any
	""" Saves value to the .env"""
	dotenv.set_key(os.getenv("SA_DOTENV_DIR", os.path.join(os.curdir, ".env")), key, value)
	load_dotenv()
	return value


def get_event_start(e: dict) -> str:
	return e["start"].get("dateTime", e["start"].get("date", ""))


def get_event_end(e: dict) -> str:
	return e["end"].get("dateTime", e["end"].get("date", ""))


def gstrftime(dt, tz_force=None, separated_tz=False):
	# FORMAT: 2002-10-02T15:00:00Z
	if type(dt) == datetime.date:  # Is only a date
		dt = datetime.datetime.combine(dt, datetime.datetime.min.time())

	if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:  # has no timezone awareness
		pytz.timezone(DEFAULT_TIMEZONE).localize(dt.replace(tzinfo=None))
	if tz_force:
		if type(tz_force) == str:
			tz_force = pytz.timezone(tz_force)
		dt = tz_force.localize(dt.replace(tzinfo=None))
	if separated_tz:
		s = dt.strftime("%Y-%m-%dT%H:%M:%S")
	else:
		s = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
	return s


def gstrptime(iso_formatted_string):
	dt = iso8601.parse_date(iso_formatted_string)
	return dt


def tmp_save(txt, name, end="json"):
	unique_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
	with open("temp/" + f"{name}_{unique_date}.{end}", "w") as wf:
		if end == "json":
			json.dump(txt, wf, indent=4)
		else:
			wf.write(txt)
			wf.flush()


def progress_line(i, len_of_array, text, tab=30):
	n = int(((i + 1) / len_of_array) * tab)
	print("\r[", "=" * n, ">", " " * (tab - n - 1), "] ", i, " of ", len_of_array, " %s (%2.1f %%)" % (text, 100.0 * (i / len_of_array)), sep="", end="")


def event_time_difference(list_of_events, cmp_function = min):
	# type: (List[dict], callable) -> Tuple[dict, dict]

	def get_delta(e1_: dict, e2_: dict):
		e1_end = gstrptime(get_event_end(e1_))
		e2_start = gstrptime(get_event_start(e2_))
		return e2_start - e1_end

	r1 = list_of_events[0]
	r2 = list_of_events[1]
	best = get_delta(r1, r2)
	for i, e1 in enumerate(list_of_events[:-1], start=1):
		e2 = list_of_events[i]
		d = get_delta(e1, e2)
		if cmp_function(d, best) == d:
			r1, r2 = e1, e2
			best = d

	return r1, r2


if __name__ == '__main__':
	logger.debug("Misc testing")
	print(gstrftime(datetime.datetime.now(), tz_force=tzlocal.get_localzone()))
	print(gstrftime(datetime.datetime.now().astimezone(tzlocal.get_localzone())))
