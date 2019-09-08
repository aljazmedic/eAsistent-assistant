import base64

from bs4 import BeautifulSoup
from requests import Session

import event_formatter as ef
from misc import *


def get_request_date_boundary(start_date: datetime.date = datetime.date.today(), end_date: datetime.date = None):
	# start_date += datetime.timedelta(days=1)

	# Assure we don't parse for saturday or sunday
	while start_date.weekday() >= 5:
		start_date += datetime.timedelta(days=1)

	if not end_date:
		end_date = start_date + datetime.timedelta(days=1)
		while end_date.weekday() >= 5:
			end_date += datetime.timedelta(days=1)

	return {"from": start_date.strftime("%Y-%m-%d"),
	        "to":   end_date.  strftime("%Y-%m-%d")}


def _parse_user_data(path: str):
	with open(path) as rf:
		data = json.load(rf)

	data["geslo"] = str(base64.b64decode(data["geslo"].encode("utf-8")), "utf-8")
	return data


class EAssistantService:
	def __init__(self):
		self.requests_session = None
		data = _parse_user_data("private/creds.json")
		self.init_session(data)

	def init_session(self, user_data):
		self.requests_session = Session()
		logging.info("Initialization of session for eassistant.")
		# Initial get
		login_url = "https://www.easistent.com/p/ajax_prijava"

		post_request = self.requests_session.post(login_url, data=user_data, allow_redirects=True)
		post_json = post_request.json()
		if post_request.status_code != 200 or len(post_json["errfields"]) != 0:
			raise Exception(post_request, post_request.text)
		print(post_json)
		rdrect = post_json["data"]["prijava_redirect"]

		get_request = self.requests_session.get(rdrect)
		# get_request.encoding = 'ISO-8859-1'

		# Extract auth metas from html
		soup = BeautifulSoup(get_request.text, 'html.parser')
		metas = {}
		soup = soup.find("head").find_all("meta")

		for nm in soup:
			if nm.get("name", None) in ("x-child-id", "access-token", "refresh-token"):
				metas[nm.get("name", None)] = nm.get("content", "").strip()

		# update headers to achieve authorization level :OK  :)
		self.requests_session.headers.update({
			"Authorization": metas["access-token"],
			"X-Child-Id": metas["x-child-id"],
			"X-Client-Version": "13",
			"X-Client-Platform": "web",
			"X-Requested-With": "XMLHttpRequest"
		})
		logging.info("Session authenticated!")
		return self

	def introduce(self):
		table = ask_for(self.requests_session, "GET", "https://www.easistent.com/m/me/child").json()
		logging.info(f"Logged in as {table['display_name']} (ID:{table['id']}), age level: {table['age_level']}")

	def get_school_events(self, dt_begin: datetime.date = datetime.date.today(), dt_end: datetime.date = None):
		timetable_payload = get_request_date_boundary(dt_begin, dt_end)
		parsed_table = ask_for(self.requests_session, "GET", "https://www.easistent.com/m/timetable/weekly",
		                       params=timetable_payload).json()
		tmp_save(parsed_table, "timetable_parsed", "json")
		# print(parsed_table)
		time_table_object = ef.to_timetable(parsed_table)
		tmp_save(time_table_object, "timetable_formatted", "json")
		return time_table_object
