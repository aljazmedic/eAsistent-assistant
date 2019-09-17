from bs4 import BeautifulSoup
from requests import Session

from account_manager import AccountManager
from event_formatter import EventFormatter
from misc import *
logger = logging.getLogger(__name__)

def get_request_date_boundary(start_date: datetime.date = datetime.date.today(), end_date: datetime.date = None):
	# start_date += datetime.timedelta(days=1)

	# Assure we don't parse for saturday or sunday
	start_date += datetime.timedelta(days=7-start_date.weekday())

	if not end_date:
		end_date = start_date + datetime.timedelta(days=1)
	end_date += datetime.timedelta(days=7-end_date.weekday())

	return {"from": start_date.strftime("%Y-%m-%d"),
	        "to":   end_date.  strftime("%Y-%m-%d")}


class EAssistantService:
	def __init__(self):
		self.ef = EventFormatter()

		self.requests_session = None
		self.account_manager = AccountManager()
		data = self._parse_user_data()
		self.init_session(data)
		self.introduce()

	def _parse_user_data(self):
		r = {
			"pin": "",
			"captcha": "",
			"koda": ""
		}

		for field in ["uporabnik", "geslo"]:
			r[field] = self.account_manager.retrieve(field, request_if_none=True)

		return r

	def init_session(self, user_data):
		self.requests_session = Session()
		logger.info("Initialization of session for eassistant.")
		# Initial get
		login_url = "https://www.easistent.com/p/ajax_prijava"

		post_request = self.requests_session.post(login_url, data=user_data, allow_redirects=True)
		post_json = post_request.json()
		if post_request.status_code != 200 or len(post_json["errfields"]) != 0:
			raise Exception(post_request, post_request.text)
		for err in post_json.get('errfields', []):
			logger.error(err)
		redirect = post_json["data"]["prijava_redirect"]

		get_request = self.requests_session.get(redirect)
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
		logger.info("Session authenticated!")
		return self

	def introduce(self):
		table = ask_for(self.requests_session, "GET", "https://www.easistent.com/m/me/child").json()
		logger.info(f"Logged in as {table['display_name']} (ID:{table['id']}), age level: {table['age_level']}")

	def get_school_events(self, dt_begin: datetime.date = datetime.date.today(), dt_end: datetime.date = None):
		timetable_payload = get_request_date_boundary(dt_begin, dt_end)
		logger.debug("Easistent timetable payload: " + str(timetable_payload))
		parsed_table = ask_for(self.requests_session, "GET", "https://www.easistent.com/m/timetable/weekly",
		                       params=timetable_payload).json()
		tmp_save(parsed_table, "timetable_parsed", "json")
		# print(parsed_table)
		time_table_object = self.ef.format_timetable_for_entry(parsed_table)
		tmp_save(time_table_object, "timetable_formatted", "json")
		return time_table_object
