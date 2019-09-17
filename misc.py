import datetime
import json
import os
import shutil

import iso8601
import logging
import pytz
import requests
import tzlocal
from typing import Union
DEFAULT_TIMEZONE = "Europe/Belgrade"


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
			print(e)


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
	logging.debug("gstrftime:" + str(dt) + "->" + s)
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


if __name__ == '__main__':
	logging.debug("Misc testing")
	print(gstrftime(datetime.datetime.now(), tz_force=tzlocal.get_localzone()))
	print(gstrftime(datetime.datetime.now().astimezone(tzlocal.get_localzone())))

